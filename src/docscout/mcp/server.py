"""Servidor Model Context Protocol (MCP) para Google Gemini y Antigravity."""

from typing import Optional
from fastmcp import FastMCP

from docscout.core.models import CrawlConfig
from docscout.crawler.page_fetcher import PageFetcher
from docscout.crawler.sitemap_crawler import SitemapCrawler
from docscout.discovery.search_engine import SearchEngine
from docscout.exporter.exporter_service import ExporterService
from docscout.processor.markdown_builder import MarkdownBuilder

# Instanciar el servidor FastMCP oficial para DocScout
mcp = FastMCP("DocScout")


@mcp.tool()
def search_official_docs(query: str, max_results: int = 5) -> str:
    """Busca en la web y extrae documentación oficial depurada sin ruido (sin scripts ni cookies) en formato Markdown.

    Args:
        query: Concepto técnico, tecnología o problema a buscar (ej. 'FastAPI background tasks', 'Docker multi-stage').
        max_results: Número máximo de fuentes oficiales a compilar (defecto 5).

    Returns:
        Documento Markdown enriquecido con código técnico intacto y metadatos YAML frontmatter.
    """
    results = SearchEngine.search(query=query, max_results=max_results)
    if not results:
        return f"# ⚠️ Sin resultados oficiales para: '{query}'\n\nNo se encontraron páginas de documentación oficial que coincidan con la búsqueda."

    fetcher = PageFetcher(CrawlConfig(request_delay_seconds=0.3))
    compiled_sections = []

    for idx, item in enumerate(results, 1):
        raw_html = fetcher.fetch(item.url)
        if not raw_html:
            continue

        doc_page = MarkdownBuilder.build_doc_page(
            raw_html=raw_html,
            source_url=item.url,
            custom_tags=["mcp-search", "gemini-source"],
        )

        compiled_sections.append(doc_page.clean_markdown)

    if not compiled_sections:
        return f"# ⚠️ Error de descarga\n\nNo se pudo recuperar el contenido de las fuentes encontradas para '{query}'."

    return "\n\n---\n\n".join(compiled_sections)


@mcp.tool()
def crawl_and_export_docs(url: str, topic: str, max_pages: int = 10) -> str:
    """Rastrea recursivamente una URL raíz de documentación oficial y genera un dossier listo para Google NotebookLM.

    Args:
        url: URL base de la documentación oficial (ej. 'https://docs.pydantic.dev/latest/').
        topic: Nombre o tema del cuaderno (ej. 'Pydantic V2').
        max_pages: Cantidad máxima de páginas a rastrear (defecto 10).

    Returns:
        Resumen de la exportación con la ruta del dossier consolidado en disco.
    """
    config = CrawlConfig(max_pages=max_pages, max_depth=2, request_delay_seconds=0.4)
    crawler = SitemapCrawler(config=config)

    pages = crawler.crawl(root_url=url, tech_stack=topic)
    if not pages:
        return f"No se pudieron descargar páginas desde la URL: {url}"

    export_summary = ExporterService.export_dossier(topic=topic, pages=pages)

    return (
        f"✅ Dossier generado exitosamente para **{topic}**\n\n"
        f"- **Páginas procesadas:** {export_summary['sources_count']}\n"
        f"- **Palabras acumuladas:** {export_summary['total_words']}\n"
        f"- **Archivo consolidado para NotebookLM:** `{export_summary['consolidated_file']}`\n"
        f"- **Manifiesto:** `{export_summary['manifest_file']}`"
    )


def run_mcp_server() -> None:
    """Punto de entrada para ejecutar el servidor MCP sobre STDIO."""
    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
