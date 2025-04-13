# table_structure.py


class TableStructureService:
    def __init__(self, db):
        self.db = db

    def get_table_columns(self, table_name: str, correlation_id: str) -> list:
        return self.db.execute_query(
            """SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position""",
            ("jec", table_name),
            return_results=True,  # Critical parameter
            correlation_id=correlation_id,
            query_name="get_table_columns",
        )

    def get_constraints(self, table_name: str, correlation_id: str) -> list:
        return self.db.execute_query(
            """SELECT conname, contype, conkey 
            FROM pg_constraint
            JOIN pg_class ON conrelid = pg_class.oid 
            WHERE relname = %s""",
            (table_name,),
            return_results=True,  # Critical parameter
            correlation_id=correlation_id,
            query_name="get_table_constraints",
        )

    def get_foreign_keys(self, table_name: str, correlation_id: str) -> list:
        """Get foreign key relationships"""
        return self.db.execute_query(
            """SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s""",
            (table_name,),
            correlation_id=correlation_id,
            query_name="get_foreign_keys",
        )
