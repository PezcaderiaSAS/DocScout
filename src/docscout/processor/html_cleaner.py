"""Limpiador quirúrgico de HTML para documentación técnica con BeautifulSoup4."""

import re
from typing import Optional, Set
from bs4 import BeautifulSoup, Tag

# Etiquetas que siempre representan ruido o scripts
NOISY_TAGS: Set[str] = {
    "script",
    "style",
    "noscript",
    "iframe",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "svg",
    "canvas",
    "meta",
    "link",
}

# Patrones Regex para clases e identificadores de ruido web (banners, cookies, ads, feedback)
NOISY_ATTR_PATTERNS: re.Pattern = re.compile(
    r"(cookie|banner|consent|sidebar|navbar|nav-menu|advertisement|ads|social-share|feedback|popup|modal|announcement|search-box|site-header|site-footer|theme-toggle)",
    re.IGNORECASE,
)

# Selectores CSS prioritarios para ubicar el contenido principal de documentación
MAIN_CONTENT_SELECTORS = [
    "main",
    "article",
    '[role="main"]',
    ".markdown-section",
    ".md-content",
    ".docs-content",
    ".documentation-content",
    "#main-content",
    "#content",
    "#doc-content",
    ".content",
    ".document",
]


class HTMLCleaner:
    """Procesador especializado en eliminar ruido web preservando la integridad del contenido técnico."""

    @staticmethod
    def clean_html(raw_html: str, preserve_code_blocks: bool = True) -> str:
        """Limpia el HTML crudo eliminando elementos irrelevantes y aislando el contenido técnico.

        Args:
            raw_html: Cadena de texto con el código HTML original.
            preserve_code_blocks: Si es True, asegura la protección de tags pre/code.

        Returns:
            HTML limpio y optimizado para la conversión a Markdown.
        """
        if not raw_html or not raw_html.strip():
            return ""

        soup = BeautifulSoup(raw_html, "html.parser")

        # 1. Eliminar etiquetas ruidosas absolutas
        for tag_name in NOISY_TAGS:
            for element in soup.find_all(tag_name):
                # Proteger si accidentalmente está dentro de un bloque pre
                if preserve_code_blocks and element.find_parent("pre"):
                    continue
                element.decompose()

        # 2. Eliminar contenedores ruidosos por clase o ID
        for element in list(soup.find_all(True)):
            if not isinstance(element, Tag) or element.attrs is None:
                continue
            # No eliminar si es pre, code o table
            if element.name in {"pre", "code", "table", "th", "tr", "td"}:
                continue
            if element.find_parent("pre"):
                continue

            raw_classes = element.attrs.get("class", [])
            classes = " ".join(raw_classes) if isinstance(raw_classes, list) else str(raw_classes or "")
            elem_id = str(element.attrs.get("id", ""))
            role = str(element.attrs.get("role", ""))

            if (
                NOISY_ATTR_PATTERNS.search(classes)
                or NOISY_ATTR_PATTERNS.search(elem_id)
                or role in {"navigation", "banner", "complementary"}
            ):
                element.decompose()

        # 3. Localizar el contenedor principal de la documentación
        main_container: Optional[Tag] = None
        for selector in MAIN_CONTENT_SELECTORS:
            candidate = soup.select_one(selector)
            if candidate and len(candidate.get_text(strip=True)) > 100:
                main_container = candidate
                break

        target_root = main_container if main_container is not None else soup.body or soup

        # 4. Desempaquetar o limpiar atributos innecesarios excepto href, src y class de lenguaje en code
        for tag in target_root.find_all(True):
            if not isinstance(tag, Tag) or tag.attrs is None:
                continue
            attrs_to_keep = {}
            if tag.name == "a" and tag.has_attr("href"):
                attrs_to_keep["href"] = tag["href"]
            elif tag.name == "code" and tag.has_attr("class"):
                # Preservar clases de resaltado de sintaxis como language-python
                raw_c = tag.get("class", [])
                classes_list = raw_c if isinstance(raw_c, list) else [str(raw_c)]
                lang_classes = [c for c in classes_list if "lang" in c or "highlight" in c or "py" in c or "js" in c or "sh" in c]
                if lang_classes:
                    attrs_to_keep["class"] = lang_classes
            tag.attrs = attrs_to_keep

        return str(target_root)
