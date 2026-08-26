"""Cliente de descarga HTTP resiliente con rate limiting ético y reintentos exponenciales."""

import asyncio
import time
from typing import Dict, List, Optional
import httpx

from docscout.core.models import CrawlConfig


class PageFetcher:
    """Descargador de páginas web optimizado para sitios de documentación técnica."""

    def __init__(self, config: Optional[CrawlConfig] = None):
        self.config = config or CrawlConfig()
        self._last_request_time: float = 0.0

    def _get_headers(self) -> Dict[str, str]:
        """Genera cabeceras HTTP estándar emulando un cliente legítimo con User-Agent de DocScout."""
        return {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

    def _enforce_rate_limit(self) -> None:
        """Pausa síncrona obligatoria para respetar los límites del servidor remoto."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.config.request_delay_seconds:
            time.sleep(self.config.request_delay_seconds - elapsed)
        self._last_request_time = time.time()

    async def _enforce_rate_limit_async(self) -> None:
        """Pausa asíncrona obligatoria para respetar los límites del servidor remoto."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.config.request_delay_seconds:
            await asyncio.sleep(self.config.request_delay_seconds - elapsed)
        self._last_request_time = time.time()

    def fetch(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Descarga el contenido HTML de una URL de forma síncrona con reintentos.

        Args:
            url: Dirección web a consultar.
            max_retries: Número de reintentos ante errores transitorios.

        Returns:
            Contenido HTML como string, o None si no pudo ser recuperado.
        """
        self._enforce_rate_limit()

        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(
                    headers=self._get_headers(),
                    timeout=self.config.timeout_seconds,
                    follow_redirects=True,
                ) as client:
                    response = client.get(url)

                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in {429, 500, 502, 503, 504}:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        # Error 404, 403 u otro permanente
                        return None
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError):
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2
                else:
                    return None
        return None

    async def fetch_async(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Descarga asíncrona de HTML con reintentos y retroceso exponencial."""
        await self._enforce_rate_limit_async()

        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    headers=self._get_headers(),
                    timeout=self.config.timeout_seconds,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url)

                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in {429, 500, 502, 503, 504}:
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    else:
                        return None
            except (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError):
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    return None
        return None

    def fetch_multiple(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """Descarga en lote una lista de URLs secuencialmente respetando rate limits."""
        results: Dict[str, Optional[str]] = {}
        for url in urls:
            results[url] = self.fetch(url)
        return results
