import sys
from typing import Optional
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt

from docscout import __version__
from docscout.core.models import CrawlConfig
from docscout.crawler.page_fetcher import PageFetcher
from docscout.crawler.sitemap_crawler import SitemapCrawler
from docscout.discovery.search_engine import SearchEngine
from docscout.exporter.exporter_service import ExporterService
from docscout.mcp.config_generator import MCPConfigGenerator
from docscout.mcp.server import run_mcp_server
from docscout.processor.markdown_builder import MarkdownBuilder

# Reconfigurar codificación para compatibilidad total con Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

app = typer.Typer(
    name="docscout",
    help="DocScout: Automatizador de Documentacion Oficial para Google NotebookLM y Servidor MCP para Gemini.",
    add_completion=False,
)
console = Console(force_terminal=True, legacy_windows=False)


def print_banner() -> None:
    """Muestra el banner de bienvenida de DocScout."""
    banner_text = (
        f"[bold cyan]DocScout[/bold cyan] [bold green]v{__version__}[/bold green]\n"
        "[dim]Extractor de Documentación Técnica Oficial para Google NotebookLM y Gemini[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


@app.command(name="search")
def search_command(
    query: str = typer.Argument(..., help="Término técnico o concepto a buscar (ej. 'FastAPI background tasks')"),
    max_results: int = typer.Option(5, "--max-results", "-n", help="Número máximo de fuentes oficiales"),
    tech: Optional[str] = typer.Option(None, "--tech", "-t", help="Filtro de tecnología o framework"),
    output_dir: str = typer.Option("output", "--out", "-o", help="Directorio destino"),
) -> None:
    """Busca en fuentes oficiales, limpia el contenido y empaqueta el dossier para NotebookLM."""
    print_banner()
    console.print(f"\n🔍 [bold]Buscando fuentes oficiales para:[/bold] [yellow]{query}[/yellow]...\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task_search = progress.add_task("Consultando DuckDuckGo y aplicando filtro oficial...", total=None)
        results = SearchEngine.search(query=query, max_results=max_results, tech_filter=tech)
        progress.remove_task(task_search)

    if not results:
        console.print("[bold red]❌ No se encontraron fuentes oficiales que coincidan con la búsqueda.[/bold red]")
        raise typer.Exit(1)

    table = Table(title="Fuentes Oficiales Seleccionadas", border_style="green", header_style="bold green")
    table.add_column("#", justify="center", style="cyan")
    table.add_column("Título", style="white")
    table.add_column("Dominio Oficial", style="magenta")
    table.add_column("Confianza", justify="center", style="yellow")
    table.add_column("URL", style="dim")

    for idx, r in enumerate(results, 1):
        domain = r.url.split("/")[2] if len(r.url.split("/")) > 2 else r.url
        confidence_str = f"{int(r.confidence_score * 100)}%"
        table.add_row(str(idx), r.title[:50], domain, confidence_str, r.url[:60] + "...")

    console.print(table)
    console.print("")

    # Descargar y procesar
    fetcher = PageFetcher(CrawlConfig(request_delay_seconds=0.4))
    processed_pages = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task_download = progress.add_task("Descargando y sanitizando páginas...", total=len(results))

        for item in results:
            raw_html = fetcher.fetch(item.url)
            if raw_html:
                page = MarkdownBuilder.build_doc_page(
                    raw_html=raw_html,
                    source_url=item.url,
                    tech_stack=tech or query.split()[0],
                    custom_tags=[query.lower().replace(" ", "-")],
                )
                processed_pages.append(page)
            progress.advance(task_download)

    if not processed_pages:
        console.print("[bold red]❌ Error: No se pudo descargar el contenido de las fuentes.[/bold red]")
        raise typer.Exit(1)

    # Exportar
    summary = ExporterService.export_dossier(
        topic=query,
        pages=processed_pages,
        output_root=output_dir,
    )

    console.print(
        Panel(
            f"✅ [bold green]Dossier compilado con éxito para Google NotebookLM[/bold green]\n\n"
            f"📁 [bold]Carpeta:[/bold] [cyan]{summary['directory']}[/cyan]\n"
            f"📄 [bold]Dossier Unificado:[/bold] [yellow]{summary['consolidated_file']}[/yellow]\n"
            f"📑 [bold]Fuentes Individuales:[/bold] [white]{summary['sources_count']} archivos en sources/[/white]\n"
            f"📊 [bold]Total Palabras:[/bold] [magenta]{summary['total_words']:,}[/magenta]\n"
            f"📋 [bold]Manifiesto:[/bold] [dim]{summary['manifest_file']}[/dim]",
            title="Exportación Completada",
            border_style="green",
        )
    )


@app.command(name="crawl")
def crawl_command(
    url: str = typer.Argument(..., help="URL raíz de la documentación oficial (ej. 'https://docs.pydantic.dev/latest/')"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Tema o nombre del cuaderno"),
    max_pages: int = typer.Option(10, "--max-pages", "-n", help="Límite máximo de páginas"),
    depth: int = typer.Option(2, "--depth", "-d", help="Profundidad máxima del rastreo"),
    output_dir: str = typer.Option("output", "--out", "-o", help="Directorio destino"),
) -> None:
    """Rastrea recursivamente subpáginas de una URL oficial y genera el paquete para NotebookLM."""
    print_banner()
    topic_name = topic or url.split("/")[2]
    console.print(f"\n🕷️  [bold]Iniciando rastreo recursivo en:[/bold] [cyan]{url}[/cyan]")
    console.print(f"⚙️  [dim]Límites: max_pages={max_pages}, max_depth={depth}[/dim]\n")

    config = CrawlConfig(max_pages=max_pages, max_depth=depth, request_delay_seconds=0.4)
    crawler = SitemapCrawler(config=config)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task_crawl = progress.add_task(f"Rastreando páginas internas de {topic_name}...", total=None)
        pages = crawler.crawl(root_url=url, tech_stack=topic_name)
        progress.remove_task(task_crawl)

    if not pages:
        console.print("[bold red]❌ No se pudieron extraer páginas de la URL proporcionada.[/bold red]")
        raise typer.Exit(1)

    summary = ExporterService.export_dossier(
        topic=topic_name,
        pages=pages,
        output_root=output_dir,
    )

    console.print(
        Panel(
            f"✅ [bold green]Rastreo y exportación completados[/bold green]\n\n"
            f"📁 [bold]Carpeta:[/bold] [cyan]{summary['directory']}[/cyan]\n"
            f"📄 [bold]Dossier Unificado:[/bold] [yellow]{summary['consolidated_file']}[/yellow]\n"
            f"📑 [bold]Páginas Descargadas:[/bold] [white]{summary['sources_count']} secciones[/white]\n"
            f"📊 [bold]Total Palabras:[/bold] [magenta]{summary['total_words']:,}[/magenta]",
            title="Rastreo Finalizado",
            border_style="green",
        )
    )


@app.command(name="mcp")
def mcp_command() -> None:
    """Inicia el Servidor Model Context Protocol (FastMCP) sobre STDIO para Gemini y Antigravity."""
    run_mcp_server()


@app.command(name="config-mcp")
def config_mcp_command(
    output_file: str = typer.Option("mcp_config.json", "--out", "-o", help="Nombre del archivo de configuración"),
) -> None:
    """Genera el snippet mcp_config.json para conectar DocScout a Gemini Desktop / Antigravity / Claude."""
    print_banner()
    path = MCPConfigGenerator.export_config_file(output_file=output_file)
    console.print(f"✅ [bold green]Configuración MCP guardada en:[/bold green] [cyan]{path}[/cyan]\n")
    console.print("[dim]Contenido del archivo generado:[/dim]")
    console.print(Panel(Path(path).read_text(encoding="utf-8"), title="mcp_config.json", border_style="cyan"))


@app.command(name="interactive")
def interactive_command() -> None:
    """Asistente guiado interactivo por terminal paso a paso."""
    print_banner()
    console.print("[bold]Bienvenido al Asistente Interactivo de DocScout[/bold]\n")

    mode = Prompt.ask(
        "¿Qué deseas realizar?",
        choices=["buscar", "rastrear", "servidor-mcp", "configurar-mcp"],
        default="buscar",
    )

    if mode == "buscar":
        q = Prompt.ask("Ingresa el término o concepto técnico (ej. 'Docker multi-stage builds')")
        max_res = IntPrompt.ask("Cantidad de fuentes oficiales a compilar", default=5)
        search_command(query=q, max_results=max_res, tech=None, output_dir="output")

    elif mode == "rastrear":
        url = Prompt.ask("Ingresa la URL raíz de la documentación oficial (ej. 'https://docs.pydantic.dev/latest/')")
        topic = Prompt.ask("Nombre de la tecnología", default="Pydantic")
        max_p = IntPrompt.ask("Límite de páginas a rastrear", default=10)
        crawl_command(url=url, topic=topic, max_pages=max_p, depth=2, output_dir="output")

    elif mode == "servidor-mcp":
        console.print("[yellow]Iniciando Servidor MCP sobre STDIO... Presiona Ctrl+C para salir.[/yellow]")
        mcp_command()

    elif mode == "configurar-mcp":
        config_mcp_command(output_file="mcp_config.json")


if __name__ == "__main__":
    app()
