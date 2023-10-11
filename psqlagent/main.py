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

def main():
    # parse prompt parameter using argparse

    # connect to database using with statement and create a db_manager
    with PostgresManager(schema_name=SCHEMA_NAME) as db:
        db.connect_with_url(DATABASE_URL)
        #print(db.get_table_definition_for_prompt('*', schema_name=SCHEMA_NAME))
        pasos = db.get_all('pasos')
        print(pasos)

    # call db_manager.get_table_definition_for_prompt() to get tables in prompt ready form

    # create two balck calls to llm.add_cap_ref() that update our currrent prompt passed in from cli

    # call llm.prompt() to get the prompt_response variable

    # parse sql response from prompt_response using SQL_QUERY_DELIMITER '--------'

    # call db_manager.execute_sql() on each sql query

    pass

if __name__ == '__main__':
    main()