"""Motor de búsqueda y descubrimiento de documentación técnica con DuckDuckGo (Sin API Keys)."""

from typing import List, Optional

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

from docscout.core.models import SearchResultItem
from docscout.discovery.domain_filter import DomainFilter


class SearchEngine:
    """Motor de búsqueda agnóstico que descubre fuentes oficiales de software."""

    @staticmethod
    def build_search_query(user_query: str, tech_filter: Optional[str] = None) -> str:
        """Construye una consulta optimizada para encontrar documentación oficial."""
        import re

        clean_query = user_query.strip()
        additions = []

        if tech_filter and tech_filter.lower() not in clean_query.lower():
            additions.append(tech_filter)

        # Si el usuario no especificó la palabra 'docs' ni 'documentation' ni 'guia' ni 'manual'
        if not re.search(r"\b(doc|docs|documentation|guide|guia|manual|api|tutorial|reference|arquitectura|architecture)\b", clean_query, re.IGNORECASE):
            additions.append("docs")

        if additions:
            return f"{clean_query} {' '.join(additions)}".strip()
        return clean_query

    @classmethod
    def search(
        cls,
        query: str,
        max_results: int = 10,
        tech_filter: Optional[str] = None,
        min_confidence: float = 0.35,
    ) -> List[SearchResultItem]:
        """Ejecuta una búsqueda en DuckDuckGo y filtra los resultados priorizando fuentes oficiales.

        Args:
            query: Término de búsqueda o concepto técnico.
            max_results: Cantidad máxima de resultados a retornar.
            tech_filter: Filtro de tecnología opcional (ej. "fastapi", "docker").
            min_confidence: Puntuación mínima de oficialidad requerida.

        Returns:
            Lista de SearchResultItem ordenados por relevancia y oficialidad.
        """
        optimized_query = cls.build_search_query(query, tech_filter=tech_filter)
        raw_items: List[SearchResultItem] = []
        seen_urls = set()

        def _fetch_from_ddg(search_term: str, target_count: int) -> None:
            try:
                with DDGS() as ddgs:
                    results_gen = ddgs.text(
                        search_term,
                        max_results=target_count,
                    )
                    for item in results_gen:
                        url = item.get("href") or item.get("url") or ""
                        title = item.get("title") or "Sin título"
                        snippet = item.get("body") or item.get("snippet") or ""

                        if not url or not url.startswith("http") or url in seen_urls:
                            continue

                        seen_urls.add(url)
                        raw_items.append(
                            SearchResultItem(
                                title=title,
                                url=url,
                                snippet=snippet,
                            )
                        )
            except Exception as e:
                pass

        # 1. Búsqueda principal
        _fetch_from_ddg(optimized_query, max(max_results * 5, 25))

        # 2. Si no hay suficientes, búsqueda complementaria directa
        if len(raw_items) < max_results * 2:
            _fetch_from_ddg(f"{query} UI design system", max(max_results * 4, 20))

        # Filtrar y ordenar por puntuación de confianza oficial
        ranked_results = DomainFilter.filter_and_rank(
            raw_items,
            min_confidence=min_confidence,
            prioritize_official=True,
        )

        # Si el filtro estricto no arrojó resultados, relajar levemente el umbral
        if not ranked_results and raw_items:
            ranked_results = DomainFilter.filter_and_rank(
                raw_items,
                min_confidence=0.15,
                prioritize_official=True,
            )

        return ranked_results[:max_results]
