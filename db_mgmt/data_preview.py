# data_preview.py


class DataPreviewService:
    def __init__(self, db):
        self.db = db

    def preview_data(
        self, table_name: str, limit: int, offset: int, correlation_id: str
    ) -> list:
        return self.db.execute_query(
            f"SELECT * FROM {table_name} LIMIT %s OFFSET %s",
            (limit, offset),
            correlation_id=correlation_id,
            query_name=f"preview_{table_name}",
        )

    def get_row_count(self, table_name: str, correlation_id: str) -> int:
        result = self.db.execute_query(
            f"SELECT COUNT(*) FROM {table_name}",
            correlation_id=correlation_id,
            query_name=f"count_{table_name}",
        )
        return result[0]["count"] if result else 0
