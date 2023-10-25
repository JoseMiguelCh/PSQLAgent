from abc import ABC, abstractmethod

class DatabaseManager(ABC):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def connect_with_url(self, url):
        pass

    def upsert(self, table_name, _dict):
        pass

    def delete(self, table_name, _id):
        pass

    def get(self, table_name, _id):
        pass

    def get_all(self, table_name, limit=100):
        pass

    def run_sql(self, sql):
        pass

    def save_results(self, result_data):
        pass
    
    @abstractmethod
    def get_table_definitions(self, table_name):
        pass
    
    @abstractmethod
    def get_all_table_names(self):
        pass
    
    @abstractmethod
    def get_table_definition_for_prompt(self, table_name):
        pass

    @abstractmethod
    def get_table_definition_map_for_embedding(self, table_name) -> dict:
        pass
    
    @abstractmethod
    def get_tables_definition_for_prompt(self, table_names: list):
        pass