import psycopg2
from psqlagent.modules.db.dbmanager import DatabaseManager

class PostgresManager(DatabaseManager):
    def __init__(self, schema_name='public'):
        self.conn = None
        self.schema_name = schema_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None:
            self.conn.close()

    def connect_with_url(self, url):
        self.conn = psycopg2.connect(url)

    def upsert(self, table_name, _dict):
        keys = _dict.keys()
        values = _dict.values()
        columns = ','.join(keys)
        placeholders = ','.join(['%s'] * len(values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES({placeholders}) ON CONFLICT (id) DO UPDATE SET "
        query += ', '.join([f"{key}=excluded.{key}" for key in keys])

        with self.conn.cursor() as cur:
            cur.execute(query, list(values))
            self.conn.commit()

    def delete(self, table_name, _id):
        query = f"DELETE FROM {table_name} WHERE id = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (_id,))
            self.conn.commit()

    def get(self, table_name, _id):
        query = f"SELECT * FROM {table_name} WHERE id = %s"

        with self.conn.cursor() as cur:
            cur.execute(query, (_id,))
            row = cur.fetchone()

        return row

    def get_all(self, table_name, limit=100):
        query = f"SELECT * FROM {self.schema_name}.{table_name} LIMIT {limit}"

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
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s;
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

    def get_all_table_names(self):
        query = f"SELECT tablename FROM pg_tables WHERE schemaname = '{self.schema_name}'"
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