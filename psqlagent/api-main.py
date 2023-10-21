from psqlagent.utils.prompts import COMPLETION_PROMPT
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psqlagent.modules.llm import add_cap_ref, prompt as llm_prompt
from psqlagent.modules.db import PostgresManager
from dotenv import load_dotenv
import os
from autogen import (
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager,
    config_list_from_json,
    config_list_from_models
)
from psqlagent.modules.orchestrator import Orchestrator
from psqlagent.utils.prompts import (
    USER_PROXY_PROMPT,
    SECRETARY_PROMPT,
    TRANSLATOR_PROMPT,
    DATA_ENGINEER_PROMPT,
    DATA_ANALYST_PROMPT,
    PRODUCT_MANAGER_PROMPT
)

load_dotenv()
assert os.getenv(
    'DATABASE_URL') is not None, 'DATABASE_URL env variable not set'
assert os.getenv('SCHEMA_NAME') is not None, 'SCHEMA_NAME env variable not set'
assert os.getenv(
    'OPENAI_APIKEY') is not None, 'OPENAI_API_KEY env variable not set'

DATABASE_URL = os.getenv('DATABASE_URL')
SCHEMA_NAME = os.getenv('SCHEMA_NAME')
OPENAI_APIKEY = os.getenv('OPENAI_APIKEY')

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
    with PostgresManager(schema_name=SCHEMA_NAME) as db:

        db.connect_with_url(DATABASE_URL)
        table_definitions = db.get_table_definition_for_prompt('*')

        prompt = add_cap_ref(
            user_query,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the previous database query. Have in mind the SCHEMA_NAME is {SCHEMA_NAME}",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions)

        gpt4_config = {
            "seed": 42,
            "temperature": 0,
            "config_list": [{"model": "gpt-4"}],
            "request_timeout": 120,
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

        function_map = {
            "run_sql": db.run_sql
        }

        def is_termination_msg(content):
            have_content = content.get("content", None) is not None
            if have_content and "APPROVED" in content["content"]:
                return True
            return False

        user_proxy = UserProxyAgent(
            name="Admin",
            system_message=USER_PROXY_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg
        )

        secretary = AssistantAgent(
            name="Secretary",
            llm_config=gpt4_config,
            system_message=SECRETARY_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg
        )

        translator = AssistantAgent(
            name="Translator",
            llm_config=gpt4_config,
            system_message=TRANSLATOR_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg
        )

        engineer = AssistantAgent(
            name="Engineer",
            llm_config=gpt4_config,
            system_message=DATA_ENGINEER_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
            function_map=function_map
        )

        data_analyst = AssistantAgent(
            name="SrDataAnalyst",
            llm_config=gpt4_config,
            system_message=DATA_ANALYST_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
            # function_map=function_map
        )

        planner = AssistantAgent(
            name="ProductManager",
            system_message=PRODUCT_MANAGER_PROMPT,
            code_execution_config=False,
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg
        )

        data_engineering_agents = [user_proxy, engineer, data_analyst, planner]
        data_eng_orchestrator = Orchestrator(
            name="Data Engineering Orchestrator", agents=data_engineering_agents)
        responses = data_eng_orchestrator.sequential_conversation(prompt)
        return responses


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
