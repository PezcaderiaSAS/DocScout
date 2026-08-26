"""Generador automático de snippets de configuración MCP para Google Gemini, Antigravity y Claude."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class MCPConfigGenerator:
    """Genera configuraciones estandarizadas para conectar DocScout a clientes MCP."""

    @classmethod
    def generate_config(
        cls,
        python_path: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Construye el objeto JSON con la definición del servidor MCP para DocScout.

        Args:
            python_path: Ruta al ejecutable de Python (por defecto sys.executable).
            project_root: Directorio raíz del proyecto (por defecto el directorio actual).

        Returns:
            Estructura de configuración compatible con Claude Desktop, Gemini y Antigravity.
        """
        py_exec = python_path or sys.executable
        root = Path(project_root or Path.cwd()).resolve()
        src_path = root / "src"

        return {
            "mcpServers": {
                "docscout": {
                    "command": py_exec,
                    "args": [
                        "-m",
                        "docscout.mcp.server",
                    ],
                    "env": {
                        "PYTHONPATH": str(src_path),
                    },
                }
            }
        }

    @classmethod
    def export_config_file(
        cls,
        output_file: str = "mcp_config.json",
        project_root: Optional[str] = None,
        python_path: Optional[str] = None,
    ) -> str:
        """Escribe el archivo mcp_config.json en disco y retorna su ruta absoluta."""
        config_data = cls.generate_config(python_path=python_path, project_root=project_root)
        out_path = Path(output_file).resolve()
        out_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
        return str(out_path)
