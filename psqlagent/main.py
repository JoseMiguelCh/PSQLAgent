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
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Initial prompt for the AI")
    args = parser.parse_args()

    if not args.prompt:
        print("Please provide a prompt")
        return
    #print("Prompt V1", args.prompt)

    with PostgresManager(schema_name=SCHEMA_NAME) as db:
        
        db.connect_with_url(DATABASE_URL)
        table_definitions = db.get_table_definition_for_prompt('*')
        #print("Table_definitions", table_definitions)

        prompt = add_cap_ref(
            args.prompt, 
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query. Have in mind the SCHEMA_NAME is {SCHEMA_NAME}",
            POSTGRES_TABLE_DEFINITIONS_CAP_REF,
            table_definitions)
        #print("Prompt V2", prompt)

        prompt = add_cap_ref(
            prompt,
            f"\nRespond in this format {TABLE_RESPONSE_FORMAT_CAP_REF}. I need to be able to easily parse the sql query from your response.",
            TABLE_RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
            {SQL_QUERY_DELIMITER}
            <sql query exclusively as raw text>""")
        #print("Prompt V3", prompt)

        prompt_response = llm_prompt(prompt)
        #print("Prompt Response", prompt_response)

        sql_query = prompt_response.split(SQL_QUERY_DELIMITER)[1].strip()
        print("===== SQL QUERY =====") 
        print(sql_query)

        result = db.run_sql(sql_query)
        print("\n====== AGENT RESPONSE =====")
        print(result)

if __name__ == '__main__':
    main()
