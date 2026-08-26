"""Filtro heurístico y clasificador de dominios oficiales para DocScout."""

from typing import List, Set
from urllib.parse import urlparse

from docscout.core.config import (
    is_known_official_domain,
    matches_official_pattern,
)
from docscout.core.models import SearchResultItem

# Lista de dominios que NO son documentación oficial (sitios de blogs, agregadores o tutoriales genéricos)
UNOFFICIAL_OR_AGGREGATOR_DOMAINS: Set[str] = {
    "medium.com",
    "dev.to",
    "geeksforgeeks.org",
    "w3schools.com",
    "tutorialspoint.com",
    "javatpoint.com",
    "freecodecamp.org",
    "stackoverflow.com",
    "stackexchange.com",
    "quora.com",
    "reddit.com",
    "pinterest.com",
    "copyprogramming.com",
    "codeproject.com",
}


class DomainFilter:
    """Clasificador y filtro de confianza para fuentes oficiales de software."""

    @classmethod
    def extract_domain(cls, url: str) -> str:
        """Extrae el nombre de dominio normalizado de una URL."""
        try:
            netloc = urlparse(url).netloc.lower().strip()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""

    @classmethod
    def is_spam_or_aggregator(cls, url: str) -> bool:
        """Determina si la URL pertenece a un agregador o sitio no oficial."""
        domain = cls.extract_domain(url)
        for unofficial in UNOFFICIAL_OR_AGGREGATOR_DOMAINS:
            if domain == unofficial or domain.endswith("." + unofficial):
                return True
        return False

    @classmethod
    def calculate_confidence_score(cls, url: str) -> float:
        """Calcula una puntuación de oficialidad entre 0.0 y 1.0.

        Criterios:
        - 1.00: Dominio oficial verificado en catálogo (FastAPI, Python, Docker, etc.).
        - 0.85: Coincide con patrones heurísticos oficiales (docs.*, readthedocs, github docs).
        - 0.50: Dominio genérico con /docs o /documentation en su ruta.
        - 0.10: Sitios de blogs o agregadores no oficiales.
        """
        if cls.is_spam_or_aggregator(url):
            return 0.10

        domain = cls.extract_domain(url)

        # 1. Catálogo conocido de fuentes oficiales
        if is_known_official_domain(domain):
            return 1.00

        # 2. Patrones de URLs de documentación
        if matches_official_pattern(url):
            return 0.85

        # 3. Indicadores en la ruta URL
        path = urlparse(url).path.lower()
        if any(seg in path for seg in ["/docs", "/documentation", "/guide", "/api-reference", "/manual"]):
            return 0.65

        return 0.30

    @classmethod
    def is_official(cls, url: str) -> bool:
        """Determina si una fuente califica como oficial (confianza >= 0.65)."""
        return cls.calculate_confidence_score(url) >= 0.65

    @classmethod
    def filter_and_rank(
        cls,
        results: List[SearchResultItem],
        min_confidence: float = 0.50,
        prioritize_official: bool = True,
    ) -> List[SearchResultItem]:
        """Filtra y reordena los resultados priorizando las fuentes oficiales con mayor puntuación.

        Args:
            results: Lista de SearchResultItem crudos.
            min_confidence: Umbral mínimo de confianza para aceptar el resultado.
            prioritize_official: Si es True, ubica las fuentes oficiales al inicio.

        Returns:
            Lista ordenada y filtrada de fuentes recomendadas.
        """
        ranked: List[SearchResultItem] = []

        for item in results:
            score = cls.calculate_confidence_score(item.url)
            is_off = score >= 0.65

            updated_item = item.model_copy(
                update={
                    "confidence_score": score,
                    "is_official_domain": is_off,
                }
            )

            if score >= min_confidence:
                ranked.append(updated_item)

        if prioritize_official:
            ranked.sort(key=lambda x: x.confidence_score, reverse=True)

        return ranked
