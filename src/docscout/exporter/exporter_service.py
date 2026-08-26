"""Servicio de persistencia y exportación estructurada para Google NotebookLM."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from docscout.core.models import DocPage, DossierManifest
from docscout.exporter.dossier_bundler import DossierBundler


class ExporterService:
    """Gestiona la persistencia física de dossiers y fuentes modulares en el sistema de archivos."""

    @classmethod
    def export_dossier(
        cls,
        topic: str,
        pages: List[DocPage],
        output_root: str = "output",
    ) -> Dict[str, Any]:
        """Exporta el lote completo de documentación en formato estructurado para Google NotebookLM.

        Estructura generada:
        output/<topic_slug>/
        ├── dossier_consolidado.md
        ├── manifest.json
        └── sources/
            ├── 01_titulo_seccion.md
            └── 02_otro_tema.md

        Args:
            topic: Tema o nombre del paquete de documentación.
            pages: Lista de DocPage procesadas.
            output_root: Directorio raíz de salida (por defecto 'output').

        Returns:
            Diccionario resumen con las rutas de los archivos creados y estadísticas.
        """
        topic_slug = DossierBundler.slugify(topic) or "documentacion"
        target_dir = Path(output_root) / topic_slug
        sources_dir = target_dir / "sources"

        # Crear carpetas si no existen
        sources_dir.mkdir(parents=True, exist_ok=True)

        # 1. Guardar dossier consolidado
        consolidated_md = DossierBundler.build_consolidated_dossier(topic=topic, pages=pages)
        consolidated_path = target_dir / "dossier_consolidado.md"
        consolidated_path.write_text(consolidated_md, encoding="utf-8")

        # 2. Guardar fuentes modulares individuales
        saved_sources: List[Dict[str, Any]] = []
        for idx, page in enumerate(pages, 1):
            page_slug = DossierBundler.slugify(page.metadata.title) or f"seccion_{idx}"
            filename = f"{idx:02d}_{page_slug}.md"
            source_file_path = sources_dir / filename

            source_file_path.write_text(page.clean_markdown, encoding="utf-8")

            saved_sources.append({
                "index": idx,
                "filename": filename,
                "relative_path": str(source_file_path.relative_to(target_dir)),
                "title": page.metadata.title,
                "url": page.metadata.source_url,
                "domain": page.metadata.domain,
                "word_count": page.metadata.word_count,
            })

        # 3. Guardar manifest.json
        total_words = sum(p.metadata.word_count for p in pages)
        manifest = DossierManifest(
            topic=topic,
            total_sources=len(pages),
            total_words=total_words,
            entry_point_file="dossier_consolidado.md",
            sources_summary=saved_sources,
        )

        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(
            manifest.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return {
            "topic": topic,
            "directory": str(target_dir.resolve()),
            "consolidated_file": str(consolidated_path.resolve()),
            "manifest_file": str(manifest_path.resolve()),
            "sources_count": len(pages),
            "total_words": total_words,
        }
