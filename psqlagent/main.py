from psqlagent.modules.llm import add_cap_ref, prompt as llm_prompt
import argparse
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Initial prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return

    with PostgresManager(schema_name=SCHEMA_NAME) as db:

        db.connect_with_url(DATABASE_URL)
        table_definitions = db.get_table_definition_for_prompt('*')

        prompt = add_cap_ref(
            args.prompt,
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query. Have in mind the SCHEMA_NAME is {SCHEMA_NAME}",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions)

        gpt4_config = {
            "seed": 42,
            "temperature": 0,
            "config_list": config_list_from_models(["gpt-4"]),
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
            is_termination_msg=is_termination_msg
        )

        scientist = AssistantAgent(
            name="SrDataAnalyst",
            llm_config=gpt4_config,
            system_message=DATA_ANALYST_PROMPT,
            code_execution_config=False,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg,
            function_map=function_map
        )

        planner = AssistantAgent(
            name="ProductManager",
            system_message=PRODUCT_MANAGER_PROMPT,
            code_execution_config=False,
            llm_config=gpt4_config,
            human_input_mode="NEVER",
            is_termination_msg=is_termination_msg
        )

        groupchat = GroupChat(
            agents=[user_proxy, secretary, translator, engineer, scientist, planner], messages=[], max_round=10)
        manager = GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

        user_proxy.initiate_chat(manager, clear_history=True, message=prompt)


if __name__ == '__main__':
    main()
