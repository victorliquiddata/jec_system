# validation.py

import re
from typing import Optional


class DBMgmtValidator:
    @staticmethod
    def validate_table_name(name: str) -> bool:
        """Validate against SQL injection and schema boundaries"""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$", name)) and name in {
            "usuarios",
            "partes",
            "categorias_causas",
            "processos",
            "partes_processo",
            "documentos",
        }

    @staticmethod
    def sanitize_limit(limit: Optional[int]) -> int:
        """Ensure safe row limits"""
        return min(abs(limit or 100), 1000)  # Max 1000 rows

    @staticmethod
    def validate_sql_readonly(query: str) -> bool:
        """Block dangerous operations in preview mode"""
        blocked_keywords = {"insert", "update", "delete", "drop", "alter", "grant"}
        return not any(keyword in query.lower() for keyword in blocked_keywords)
