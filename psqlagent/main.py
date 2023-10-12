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

        # build the gpt_cofiguration object
        
        # build the function map

        # create our terminate msg function

        # create a set of agents with specific functions
        # admin user proxy agent - takes in the prompt and manages the group chat
        # data engineer agent - generates the sql query
        # sr data analyst agent - run the sql query and generate the response
        # product manager -  validates the response to make sure it is correct

        # create a group chat and initialize the chat.
        
if __name__ == '__main__':
    main()
