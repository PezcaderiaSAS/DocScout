"""Empaquetador de dossiers consolidados de documentación técnica para Google NotebookLM."""

import re
from datetime import datetime, timezone
from typing import List

from docscout.core.models import DocPage


class DossierBundler:
    """Compilador que unifica múltiples páginas de documentación en un solo dossier estructurado."""

    @staticmethod
    def slugify(text: str) -> str:
        """Convierte una cadena de texto en un slug URL/Anchor seguro."""
        clean = re.sub(r"[^\w\s-]", "", text.lower().strip())
        return re.sub(r"[-\s]+", "-", clean)

    @classmethod
    def build_consolidated_dossier(cls, topic: str, pages: List[DocPage]) -> str:
        """Genera el contenido Markdown unificado con portada, TOC y capítulos ordenados.

        Args:
            topic: Tema o tecnología general del dossier.
            pages: Lista de DocPage procesadas.

        Returns:
            Contenido Markdown consolidado listo para ser cargado en NotebookLM.
        """
        if not pages:
            return f"# 📚 Dossier Oficial: {topic}\n\n*No se recopilaron páginas para este tema.*"

        total_words = sum(p.metadata.word_count for p in pages)
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Frontmatter Global del Dossier
        frontmatter = (
            "---\n"
            f'dossier_topic: "{topic}"\n'
            f"total_sources: {len(pages)}\n"
            f"total_words: {total_words}\n"
            f'generated_at: "{now_iso}"\n'
            f'target_platform: "Google NotebookLM / Gemini"\n'
            f'dossier_version: "1.0.0"\n'
            "---\n\n"
        )

        # 2. Portada y Resumen Ejecutivo
        header = (
            f"# 📚 Dossier Técnico Oficial: {topic.title()}\n\n"
            "> **Fuente de Conocimiento Verificada para Google NotebookLM y Asistentes Gemini.**\n"
            f"> *Generado automáticamente el {now_iso} por DocScout.*\n\n"
            "## 📊 Resumen Ejecutivo del Lote\n\n"
            "| # | Título de la Sección | Dominio Oficial | Palabras | Enlace Canónico |\n"
            "| :-: | :--- | :--- | :-: | :--- |\n"
        )

        table_rows: List[str] = []
        toc_items: List[str] = []

        for idx, page in enumerate(pages, 1):
            anchor = f"capitulo-{idx}-{cls.slugify(page.metadata.title)}"
            title_escaped = page.metadata.title.replace("|", "-")
            url = page.metadata.source_url
            domain = page.metadata.domain
            words = page.metadata.word_count

            table_rows.append(f"| {idx} | [{title_escaped}](#{anchor}) | `{domain}` | {words} | [Ver Oficial]({url}) |")
            toc_items.append(f"{idx}. [{title_escaped}](#{anchor}) - *({domain})*")

        toc_section = (
            "\n## 📑 Índice General de Contenidos\n\n"
            + "\n".join(toc_items)
            + "\n\n---\n\n"
        )

        # 3. Ensamblado de Capítulos
        chapters: List[str] = []
        for idx, page in enumerate(pages, 1):
            anchor = f"capitulo-{idx}-{cls.slugify(page.metadata.title)}"
            
            # Limpiar frontmatter individual si ya venía en clean_markdown para no duplicar en el medio
            body_md = page.clean_markdown
            if body_md.startswith("---"):
                parts = body_md.split("---", 2)
                if len(parts) >= 3:
                    body_md = parts[2].strip()

            chapter_header = (
                f'<a id="{anchor}"></a>\n\n'
                f"## Capítulo {idx}: {page.metadata.title}\n\n"
                f"- **Fuente Oficial:** [{page.metadata.source_url}]({page.metadata.source_url})\n"
                f"- **Dominio:** `{page.metadata.domain}` | **Fecha de Extracción:** `{page.metadata.extracted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
                f"- **Etiquetas:** {', '.join(f'`{t}`' for t in page.metadata.tags)}\n\n"
                f"---\n\n"
            )

            chapters.append(chapter_header + body_md)

        # Unir todo
        full_dossier = (
            frontmatter
            + header
            + "\n".join(table_rows)
            + "\n"
            + toc_section
            + "\n\n---\n\n".join(chapters)
            + "\n\n---\n\n*Fin del Dossier Técnico - Generado por DocScout para Google NotebookLM.*"
        )

        return full_dossier
