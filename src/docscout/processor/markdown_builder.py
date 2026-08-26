"""Constructor de Markdown enriquecido y metadatos YAML frontmatter para Google NotebookLM."""

import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import trafilatura

from docscout.core.models import DocPage, OfficialSourceMetadata
from docscout.processor.html_cleaner import HTMLCleaner


class MarkdownBuilder:
    """Transforma HTML limpio en documentos Markdown estructurados con metadatos canónicos."""

    @staticmethod
    def extract_title(html: str, fallback_url: str = "") -> str:
        """Extrae el título canónico de la página HTML."""
        soup = BeautifulSoup(html, "html.parser")
        # 1. Intentar h1
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        # 2. Intentar og:title o twitter:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # 3. Intentar title de cabecera
        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            # Limpiar sufijos comunes como " - FastAPI", " | Docker Docs"
            title_text = re.sub(r"\s*[-|–—]\s*.*$", "", title_text)
            if title_text:
                return title_text

        # 4. Fallback a partir de la URL
        if fallback_url:
            path_segments = [s for s in urlparse(fallback_url).path.split("/") if s]
            if path_segments:
                return path_segments[-1].replace("-", " ").replace("_", " ").title()

        return "Official Documentation"

    @staticmethod
    def extract_internal_links(html: str, base_url: str) -> List[str]:
        """Extrae enlaces internos relativos o absolutos hacia el mismo dominio."""
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc
        links: List[str] = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                continue

            parsed = urlparse(href)
            if not parsed.netloc or parsed.netloc == base_domain:
                links.append(href)

        return list(dict.fromkeys(links))  # Deduplicar manteniendo orden

    @classmethod
    def html_to_markdown_fallback(cls, soup: BeautifulSoup) -> str:
        """Conversor simple de contingencia HTML a Markdown si trafilatura no devuelve contenido."""
        lines: List[str] = []
        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "pre", "ul", "ol", "table"]):
            if element.name in ["h1", "h2", "h3", "h4"]:
                level = int(element.name[1])
                lines.append(f"\n{'#' * level} {element.get_text(strip=True)}\n")
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{text}\n")
            elif element.name == "pre":
                code_tag = element.find("code")
                lang = ""
                if code_tag and code_tag.has_attr("class"):
                    classes = code_tag["class"] if isinstance(code_tag["class"], list) else [code_tag["class"]]
                    for c in classes:
                        if c.startswith("language-") or c.startswith("lang-"):
                            lang = c.replace("language-", "").replace("lang-", "")
                            break
                code_text = element.get_text()
                lines.append(f"\n```{lang}\n{code_text.strip()}\n```\n")
            elif element.name in ["ul", "ol"]:
                for li in element.find_all("li", recursive=False):
                    lines.append(f"- {li.get_text(strip=True)}")
                lines.append("")
        return "\n".join(lines).strip()

    @classmethod
    def build_doc_page(
        cls,
        raw_html: str,
        source_url: str,
        tech_stack: Optional[str] = None,
        custom_tags: Optional[List[str]] = None,
    ) -> DocPage:
        """Procesa el HTML y genera una instancia completa de DocPage con Markdown enriquecido.

        Args:
            raw_html: Contenido HTML crudo.
            source_url: URL de origen del contenido oficial.
            tech_stack: Nombre de la tecnología (opcional).
            custom_tags: Lista de etiquetas temáticas (opcional).

        Returns:
            DocPage lista para empaquetar o consumir por NotebookLM / Gemini.
        """
        # 1. Extraer título canónico y enlaces antes de la limpieza destructiva
        title = cls.extract_title(raw_html, fallback_url=source_url)
        internal_links = cls.extract_internal_links(raw_html, base_url=source_url)
        domain = urlparse(source_url).netloc

        # 2. Limpieza profunda con HTMLCleaner
        cleaned_html = HTMLCleaner.clean_html(raw_html)

        # 3. Extracción de Markdown con Trafilatura
        extracted_md = trafilatura.extract(
            cleaned_html,
            output_format="markdown",
            include_formatting=True,
            include_links=True,
            include_tables=True,
            include_images=False,
            favor_precision=True,
        )

        if not extracted_md or len(extracted_md.strip()) < 50:
            # Fallback manual en caso de que Trafilatura filtre demasiado
            soup_clean = BeautifulSoup(cleaned_html, "html.parser")
            extracted_md = cls.html_to_markdown_fallback(soup_clean)

        # 4. Cálculo de métricas
        words = len(extracted_md.split())
        tags = list(custom_tags or [])
        if tech_stack and tech_stack.lower() not in [t.lower() for t in tags]:
            tags.append(tech_stack.lower())
        tags.append("official-docs")

        metadata = OfficialSourceMetadata(
            title=title,
            source_url=source_url,
            extracted_at=datetime.now(timezone.utc),
            domain=domain,
            tech_stack=tech_stack,
            tags=tags,
            word_count=words,
        )

        # 5. Ensamblar YAML Frontmatter
        frontmatter = cls.generate_frontmatter(metadata)
        full_markdown = f"{frontmatter}\n\n# {title}\n\n{extracted_md}"

        return DocPage(
            metadata=metadata,
            raw_html=raw_html,
            clean_markdown=full_markdown,
            internal_links=internal_links,
        )

    @staticmethod
    def generate_frontmatter(meta: OfficialSourceMetadata) -> str:
        """Construye el encabezado YAML frontmatter canónico para NotebookLM."""
        tags_str = ", ".join(f'"{t}"' for t in meta.tags)
        return (
            "---\n"
            f'title: "{meta.title}"\n'
            f'source_url: "{meta.source_url}"\n'
            f'extracted_at: "{meta.extracted_at.isoformat()}"\n'
            f'domain: "{meta.domain}"\n'
            f'tech_stack: "{meta.tech_stack or "generic"}"\n'
            f"tags: [{tags_str}]\n"
            f"word_count: {meta.word_count}\n"
            "---"
        )
