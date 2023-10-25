from psqlagent.modules.db.dbmanager import DatabaseManager

base_config = {
    "use_cache": False,
    "temperature": 0,
    "config_list": [{"model": "gpt-4"}],
    "request_timeout": 120,
}

run_sql_config = {
    **base_config,
    "functions": [
        {
            "name": "run_sql",
                    "description": "Run the SQL query against the postgres database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "The SQL query to run",
                            }
                        },
                        "required": ["sql"]
                    }
        }
    ]
}

def build_function_map_run_query(db: DatabaseManager):
    return {
        "run_sql": db.run_sql
    }
