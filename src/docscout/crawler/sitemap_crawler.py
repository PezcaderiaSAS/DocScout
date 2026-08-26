"""Rastreador recursivo de enlaces internos y documentación técnica acotado por subdominio."""

from collections import deque
from typing import Callable, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

from docscout.core.models import CrawlConfig, DocPage
from docscout.crawler.page_fetcher import PageFetcher
from docscout.processor.markdown_builder import MarkdownBuilder


class SitemapCrawler:
    """Rastreador controlado que recorre el árbol de navegación de una documentación técnica."""

    def __init__(self, config: Optional[CrawlConfig] = None, fetcher: Optional[PageFetcher] = None):
        self.config = config or CrawlConfig()
        self.fetcher = fetcher or PageFetcher(self.config)

    @staticmethod
    def normalize_url(url: str, base_url: str) -> str:
        """Normaliza una URL relativa o absoluta eliminando anclas (#) y parámetros irrelevantes."""
        resolved = urljoin(base_url, url)
        defragged, _ = urldefrag(resolved)
        return defragged.rstrip("/")

    @staticmethod
    def is_same_subdomain(target_url: str, base_url: str) -> bool:
        """Verifica si dos URLs pertenecen exactamente al mismo host/subdominio."""
        target_netloc = urlparse(target_url).netloc.lower()
        base_netloc = urlparse(base_url).netloc.lower()
        return target_netloc == base_netloc

    def crawl(
        self,
        root_url: str,
        tech_stack: Optional[str] = None,
        on_page_processed: Optional[Callable[[DocPage, int, int], None]] = None,
    ) -> List[DocPage]:
        """Ejecuta el rastreo en anchura (BFS) a partir de una URL raíz oficial.

        Args:
            root_url: URL base de la documentación oficial.
            tech_stack: Nombre de la tecnología (opcional).
            on_page_processed: Callback opcional llamado al procesar cada página (page, index, total).

        Returns:
            Lista de DocPage procesadas y limpias.
        """
        normalized_root = self.normalize_url(root_url, root_url)
        visited_urls: Set[str] = {normalized_root}
        queue: deque[Tuple[str, int]] = deque([(normalized_root, 1)])
        processed_pages: List[DocPage] = []

        while queue and len(processed_pages) < self.config.max_pages:
            current_url, current_depth = queue.popleft()

            # Descargar HTML
            raw_html = self.fetcher.fetch(current_url)
            if not raw_html or len(raw_html.strip()) < 50:
                continue

            # Procesar y limpiar a Markdown enriquecido
            doc_page = MarkdownBuilder.build_doc_page(
                raw_html=raw_html,
                source_url=current_url,
                tech_stack=tech_stack,
            )
            processed_pages.append(doc_page)

            if on_page_processed:
                on_page_processed(doc_page, len(processed_pages), self.config.max_pages)

            # Si aún no superamos la profundidad máxima, descubrir enlaces hijos
            if current_depth < self.config.max_depth:
                for link in doc_page.internal_links:
                    normalized_child = self.normalize_url(link, current_url)

                    if (
                        normalized_child not in visited_urls
                        and self.is_same_subdomain(normalized_child, root_url)
                        and len(visited_urls) < self.config.max_pages * 2
                    ):
                        visited_urls.add(normalized_child)
                        queue.append((normalized_child, current_depth + 1))

        return processed_pages
