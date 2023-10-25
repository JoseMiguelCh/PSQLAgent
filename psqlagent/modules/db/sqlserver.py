import pyodbc
from psqlagent.modules.db.dbmanager import DatabaseManager

class SQLServerManager(DatabaseManager):
    def __init__(self, schema_name='dbo'):
        self.conn = None
        self.schema_name = schema_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None:
            self.conn.close()

    def connect_with_url(self, url):
        self.conn = pyodbc.connect(url)

    def upsert(self, table_name, _dict):
        keys = _dict.keys()
        values = _dict.values()
        columns = ','.join(keys)
        placeholders = ','.join(['?'] * len(values))
        query = f"MERGE INTO {table_name} AS target " \
                f"USING (VALUES ({placeholders})) AS source ({columns}) " \
                f"ON (target.id = source.id) " \
                f"WHEN MATCHED THEN " \
                f"UPDATE SET {','.join([f'target.{key}=source.{key}' for key in keys])} " \
                f"WHEN NOT MATCHED THEN " \
                f"INSERT ({columns}) VALUES ({placeholders});"

        with self.conn.cursor() as cur:
            cur.execute(query, list(values))
            self.conn.commit()

    def delete(self, table_name, _id):
        query = f"DELETE FROM {table_name} WHERE id = ?"

        with self.conn.cursor() as cur:
            cur.execute(query, (_id,))
            self.conn.commit()

    def get(self, table_name, _id):
        query = f"SELECT * FROM {table_name} WHERE id = ?"

        with self.conn.cursor() as cur:
            cur.execute(query, (_id,))
            row = cur.fetchone()

        return row

    def get_all(self, table_name, limit=100):
        query = f"SELECT TOP {limit} * FROM {self.schema_name}.{table_name}"

        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return rows

    def run_sql(self, sql):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                return self.save_results(cur.fetchall())
        except Exception as e:
            print("Error executing SQL:", e)

    def save_results(self, result_data):
        with open("results.txt", "w") as file:
            file.write(str(result_data))
        return "Successfully delivered results to json file."

    def get_table_definitions(self, table_name):
        select_query = """
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(select_query, (table_name,))
            results = cursor.fetchall()
            definition = [
                f"name: {row[0]}, data_type: {row[1]}" +
                (f"({row[2]})" if row[2] else "")
                for row in results
            ]
            return "; ".join(definition)

    def get_table_definitions_test(self, table_name):
        get_def_stmt = """
            EXEC sp_columns @table_name = ?;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(get_def_stmt, (table_name,))
            rows = cursor.fetchall()
            create_table_stmt = "CREATE TABLE {} (\n".format(table_name)
            for row in rows:
                create_table_stmt += "{} {},\n".format(row.column_name, row.type_name)
            create_table_stmt = create_table_stmt.rstrip(',\n') + "\n);"
            return create_table_stmt

    def get_all_table_names(self):
        query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{self.schema_name}'"
        with self.conn.cursor() as cur:
            cur.execute(query)
            table_names = [row[0] for row in cur.fetchall()]

        return table_names

    def get_table_definition_for_prompt(self, table_name):
        table_definitions = []
        if table_name == '*':
            table_names = self.get_all_table_names()
        else:
            table_names = [table_name]
        for name in table_names:
            definition = self.get_table_definitions(name)
            table_definitions.append(
                f"TABLE_NAME {name}, COLUMNS: {{definition}}")
        return "\n".join(table_definitions)

    def get_table_definition_map_for_embedding(self, table_name) -> dict:
        if table_name == '*':
            table_names = self.get_all_table_names()
        else:
            table_names = [table_name]
        definitions = {}
        for name in table_names:
            definitions[name] = self.get_table_definitions(name)
        return definitions

    def get_tables_definition_for_prompt(self, table_names: list):
        table_definitions = []
        for name in table_names:
            definition = self.get_table_definitions(name)
            table_definitions.append(
                f"TABLE_NAME {name}: COLUMNS: [{definition}]")
        return "\n".join(table_definitions)
