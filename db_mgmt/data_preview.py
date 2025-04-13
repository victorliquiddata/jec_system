from db_mgmt.services.validation import DBMgmtValidator


class DataPreviewService:
    def __init__(self, db):
        self.db = db

    def preview_data(
        self, table_name: str, limit: int, offset: int, correlation_id: str
    ) -> list:
        safe_limit = DBMgmtValidator.sanitize_limit(limit)
        return (
            self.db.execute_query(
                "SELECT * FROM {table} LIMIT %s OFFSET %s".format(table=table_name),
                (safe_limit, offset),
                return_results=True,  # Critical fix
                correlation_id=correlation_id,
                query_name=f"preview_{table_name}",
            )
            or []
        )  # Fallback for safety

    def get_row_count(self, table_name: str, correlation_id: str) -> int:
        result = self.db.execute_query(
            "SELECT COUNT(*) AS count FROM {table}".format(
                table=table_name
            ),  # Add alias
            return_results=True,  # Critical fix
            correlation_id=correlation_id,
            query_name=f"count_{table_name}",
        )
        return result[0].get("count", 0) if result else 0
