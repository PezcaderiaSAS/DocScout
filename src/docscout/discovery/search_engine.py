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

        # Si el usuario no especificó la palabra 'docs' ni 'documentation', la agregamos
        if not re.search(r"\b(doc|docs|documentation|guide|manual|api|tutorial|reference)\b", clean_query, re.IGNORECASE):
            additions.append("official documentation")

        if additions:
            return f"{clean_query} {' '.join(additions)}".strip()
        return clean_query

    @classmethod
    def search(
        cls,
        query: str,
        max_results: int = 10,
        tech_filter: Optional[str] = None,
        min_confidence: float = 0.40,
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

        try:
            # Consultar DuckDuckGo usando la API libre DDGS
            with DDGS() as ddgs:
                # Solicitamos el doble para tener suficiente margen tras el filtrado
                results_generator = ddgs.text(
                    optimized_query,
                    max_results=max(max_results * 2, 10),
                )
                
                for item in results_generator:
                    url = item.get("href") or item.get("url") or ""
                    title = item.get("title") or "Sin título"
                    snippet = item.get("body") or item.get("snippet") or ""

                    if not url or not url.startswith("http"):
                        continue

                    raw_items.append(
                        SearchResultItem(
                            title=title,
                            url=url,
                            snippet=snippet,
                        )
                    )
        except Exception as e:
            # Manejo de error de red o timeout
            print(f"[Aviso SearchEngine] Fallo temporal en búsqueda remota: {e}")
            return []

        # Filtrar y ordenar por puntuación de confianza oficial
        ranked_results = DomainFilter.filter_and_rank(
            raw_items,
            min_confidence=min_confidence,
            prioritize_official=True,
        )

        return ranked_results[:max_results]
