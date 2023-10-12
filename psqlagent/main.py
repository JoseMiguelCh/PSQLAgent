from psqlagent.modules.llm import add_cap_ref, prompt as llm_prompt
import argparse
from psqlagent.modules.db import PostgresManager
from dotenv import load_dotenv
import os

# get env variables
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
    # parse prompt parameter using argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Initial prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return

    # connect to database using with statement and create a db_manager
    with PostgresManager(schema_name=SCHEMA_NAME) as db:
        print("Prompt V1", args.prompt)
        db.connect_with_url(DATABASE_URL)
        # call db_manager.get_table_definition_for_prompt() to get tables in prompt ready form
        table_definitions = db.get_table_definition_for_prompt('*')
        print("Table_definitions", table_definitions)

        # create two black calls to llm.add_cap_ref() that update our currrent prompt passed in from cli
        prompt = add_cap_ref(
            args.prompt, 
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query. Have in mind the SCHEMA_NAME is {SCHEMA_NAME}",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions)
        print("Prompt V2", prompt)

        prompt = add_cap_ref(
            prompt,
            f"Respond in this format {TABLE_RESPONSE_FORMAT_CAP_REF}",
            TABLE_RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
            {SQL_QUERY_DELIMITER}
            <sql query exclusively as raw text>""")
        print("Prompt V3", prompt)

        # call llm.prompt() to get the prompt_response variable
        prompt_response = llm_prompt(prompt)
        print("Prompt Response", prompt_response)

        # parse sql response from prompt_response using SQL_QUERY_DELIMITER '--------'
        sql_query = prompt_response.split(SQL_QUERY_DELIMITER)[1].strip()
        print("SQL Query", sql_query)

        # call db_manager.execute_sql() on each sql query
        result = db.run_sql(sql_query)
        print("---AGENT RESPONSE---")
        print(result)

if __name__ == '__main__':
    main()
