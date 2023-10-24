from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import re

class DatabaseEmbedder:
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        self.model = BertModel.from_pretrained('bert-base-uncased')
        self.map_name_to_embeddings = {}
        self.map_name_to_table_def = {}


    def add_table(self, table_name: str, text_representation: str):
        self.map_name_to_embeddings[table_name] = self.compute_embeddings(
            text_representation
        )
        self.map_name_to_table_def[table_name] = text_representation


    def compute_embeddings(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt",
                                truncation=True, padding=True, max_length=512)
        outputs = self.model(**inputs)
        return outputs["pooler_output"].detach().numpy()


    def get_similar_tables_via_embeddings(self, query: str, n=3) -> list:
        query_embeddings = self.compute_embeddings(query)
        similarities = {}
        for table_name, table_embeddings in self.map_name_to_embeddings.items():
            similarities =  {   
                table: cosine_similarity(query_embeddings, table_embeddings)[0][0] 
                for table, table_embeddings in self.map_name_to_embeddings.items()
            }
        return sorted(similarities, key = similarities.get, reverse=True)[:n]

    def get_similar_table_names_via_wordmatch(self, query: str) -> list:
        query_words = re.sub(r'[,";\']', '', query.lower()).split(" ")
        similarities = []
        for table_name in self.map_name_to_table_def.keys():
            if table_name.lower() in query_words:
                similarities.append(table_name)
        return similarities

    def get_similar_tables(self, query: str, n=3)-> set:
        similar_tables_via_embeddings = self.get_similar_tables_via_embeddings(query, n)
        similar_tables_via_wordmatch = self.get_similar_table_names_via_wordmatch(query)
        return list(set(similar_tables_via_wordmatch + similar_tables_via_embeddings))

