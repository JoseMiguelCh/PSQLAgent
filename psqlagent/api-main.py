import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psqlagent.modules.llm import add_cap_ref, prompt as llm_prompt
from dotenv import load_dotenv
import os
from psqlagent.agents.agents import build_team_orchestrator
from psqlagent.modules import embeddings
from psqlagent.modules.db.postgres import PostgresManager
from psqlagent.modules.db.sqlserver import SQLServerManager
from psqlagent.modules.db.dbmanager import DatabaseManager

load_dotenv()
assert os.getenv(
    'DATABASE_URL') is not None, 'DATABASE_URL env variable not set'
assert os.getenv('SCHEMA_NAME') is not None, 'SCHEMA_NAME env variable not set'
assert os.getenv(
    'OPENAI_APIKEY') is not None, 'OPENAI_API_KEY env variable not set'

DATABASE_URL = os.getenv('DATABASE_URL')
SCHEMA_NAME = os.getenv('SCHEMA_NAME')
OPENAI_APIKEY = os.getenv('OPENAI_APIKEY')
DATABASE_ENGINE = os.getenv('DATABASE_ENGINE')

POSTGRES_TABLE_DEFINITIONS_CAP_REF = "TABLE_DEFINITIONS"
TABLE_RESPONSE_FORMAT_CAP_REF = "TABLE_FORMAT"
SQL_QUERY_DELIMITER = "--------"

app = FastAPI()
origins = [
    "http://localhost:4200",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/query")
async def query(user_query: str):
    with create_database_manager() as db:
        db.connect_with_url(DATABASE_URL)

        map_table_name_to_table_def = db.get_table_definition_map_for_embedding("*")
        database_embedder = embeddings.DatabaseEmbedder()
        for name, table_def in map_table_name_to_table_def.items():
            database_embedder.add_table(name, table_def)
        
        similar_tables = database_embedder.get_similar_tables(user_query)
        table_definitions = db.get_tables_definition_for_prompt(similar_tables)

        prompt = add_cap_ref(
            user_query,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the previous database query. Have in mind the SCHEMA_NAME is {SCHEMA_NAME}",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions)

        datateam_orchestrator = build_team_orchestrator(
            "Data Engineering Orchestrator", db)
        success, messages = datateam_orchestrator.sequential_conversation(
            prompt)
        datateam_cost, datateam_tokens = datateam_orchestrator.get_cost_and_tokens()
        print(f"Datateam cost: {datateam_cost}")
        print(f"Datateam no. tokens: {datateam_tokens}")
        
        return success, messages

def create_database_manager(database_type = DATABASE_ENGINE, schema_name = SCHEMA_NAME) -> DatabaseManager:
    print(f"Creating database manager for {database_type}")
    if database_type == "SqlServer":
        return SQLServerManager(schema_name=schema_name)
    if database_type == "Postgres":
        return PostgresManager(schema_name=schema_name)
    
    raise ValueError("Invalid database type")


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
