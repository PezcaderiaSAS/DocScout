"""Modelos de datos Pydantic v2 para DocScout y Google NotebookLM / Gemini."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class OfficialSourceMetadata(BaseModel):
    """Metadatos canónicos de una fuente oficial extraída."""
    title: str = Field(..., description="Título canónico del documento o sección")
    source_url: str = Field(..., description="URL oficial de donde se extrajo el contenido")
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha y hora UTC de la extracción"
    )
    domain: str = Field(..., description="Nombre de dominio oficial verificado")
    tech_stack: Optional[str] = Field(None, description="Tecnología o framework detectado")
    tags: List[str] = Field(default_factory=list, description="Etiquetas temáticas")
    word_count: int = Field(default=0, ge=0, description="Cantidad estimada de palabras")


class DocPage(BaseModel):
    """Representa una página de documentación procesada y convertida a Markdown limpio."""
    metadata: OfficialSourceMetadata
    raw_html: Optional[str] = Field(None, exclude=True, description="HTML crudo original (excluido de serialización)")
    clean_markdown: str = Field(..., description="Contenido limpio en Markdown sin scripts, cookies ni menús")
    internal_links: List[str] = Field(default_factory=list, description="Enlaces a otras subpáginas de documentación")


class SearchResultItem(BaseModel):
    """Resultado individual retornado por el motor de búsqueda y clasificado."""
    title: str = Field(..., description="Título del resultado")
    url: str = Field(..., description="URL destino")
    snippet: str = Field(default="", description="Fragmento descriptivo o resumen")
    is_official_domain: bool = Field(default=False, description="Indica si pertenece a una lista de dominios oficiales")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Puntuación de confianza de oficialidad (0.0 - 1.0)")


class CrawlConfig(BaseModel):
    """Configuración de límites y comportamiento seguro del rastreador."""
    max_pages: int = Field(default=15, ge=1, le=100, description="Número máximo de páginas a descargar")
    max_depth: int = Field(default=2, ge=1, le=5, description="Profundidad máxima de rastreo de subpáginas")
    request_delay_seconds: float = Field(default=0.5, ge=0.1, le=5.0, description="Pausa ética entre peticiones HTTP")
    timeout_seconds: int = Field(default=15, ge=3, le=60, description="Tiempo de espera máximo por petición")
    user_agent: str = Field(
        default="DocScout/1.0 (Official Documentation Extractor for NotebookLM)",
        description="Encabezado User-Agent para peticiones HTTP"
    )


class DossierManifest(BaseModel):
    """Manifiesto de salida para el lote de documentación generado para Google NotebookLM."""
    topic: str = Field(..., description="Tema o tecnología del dossier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Fecha y hora UTC de generación del dossier"
    )
    total_sources: int = Field(..., ge=0, description="Total de fuentes oficiales procesadas")
    total_words: int = Field(..., ge=0, description="Total de palabras del contenido acumulado")
    entry_point_file: str = Field(default="dossier_consolidado.md", description="Archivo Markdown principal")
    sources_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de fuentes con metadatos")


class SearchDocsInput(BaseModel):
    """Esquema de entrada para la herramienta MCP search_official_docs."""
    query: str = Field(..., description="Término técnico o concepto a buscar en fuentes oficiales")
    max_results: int = Field(default=5, ge=1, le=15, description="Número máximo de fuentes oficiales a compilar")
