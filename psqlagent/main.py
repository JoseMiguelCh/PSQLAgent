from psqlagent.modules.db import PostgresManager
from dotenv import load_dotenv
import os

# get env variables
load_dotenv()
assert os.getenv('DATABASE_URL') is not None, 'DATABASE_URL env variable not set'
assert os.getenv('SCHEMA_NAME') is not None, 'SCHEMA_NAME env variable not set'
assert os.getenv('OPENAI_APIKEY') is not None, 'OPENAI_API_KEY env variable not set'

DATABASE_URL = os.getenv('DATABASE_URL')
SCHEMA_NAME = os.getenv('SCHEMA_NAME')
OPENAI_APIKEY = os.getenv('OPENAI_APIKEY')

import argparse
from psqlagent.modules.llm import add_cap_ref, prompt

def main():
    # parse prompt parameter using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Initial prompt for the AI")
    args = parser.parse_args()

    # connect to database using with statement and create a db_manager
    with PostgresManager(schema_name=SCHEMA_NAME) as db:
        db.connect_with_url(DATABASE_URL)

        # call db_manager.get_table_definition_for_prompt() to get tables in prompt ready form
        table_definitions = db.get_table_definition_for_prompt('*')

    # create two black calls to llm.add_cap_ref() that update our currrent prompt passed in from cli
    prompt_with_ref = add_cap_ref(args.prompt, "Please provide the SQL queries for the following table definitions:", "TABLE_DEFINITIONS", table_definitions)
    prompt_with_ref = add_cap_ref(prompt_with_ref, "Please provide the SQL queries for the following table definitions:", "TABLE_DEFINITIONS", table_definitions)

    # call llm.prompt() to get the prompt_response variable
    prompt_response = prompt(prompt_with_ref)

    # parse sql response from prompt_response using SQL_QUERY_DELIMITER '--------'
    sql_queries = prompt_response.split('--------')

    # call db_manager.execute_sql() on each sql query
    for sql_query in sql_queries:
        db.run_sql(sql_query.strip())

if __name__ == '__main__':
    main()
