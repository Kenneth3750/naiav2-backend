import redis 
from openai import OpenAI
import json
import numpy as np
from redis.commands.search.field import TextField, TagField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.search.query import Query
from redis.exceptions import ResponseError
from tqdm import tqdm
import time


VSS_INDEX_TYPE = "HNSW"
VSS_DATA_TYPE = "FLOAT32"
VSS_DISTANCE= "COSINE"
VSS_DIMENSION = 500
VSS_MINIMUM_SCORE= 0.3
VSS_K = 5

r = redis.Redis(host='localhost', port=6379, db=0)

def create_idx():
    try:
        r.ft('gov_idx').dropindex(True)
    except ResponseError:
        pass
    index_def = IndexDefinition(prefix=["gov:faqs:"])
    schema = (  TextField("title", as_name="title"),
                TextField("content", as_name="content"),
                TextField("link", as_name="link"),
                VectorField("embedding", VSS_INDEX_TYPE, {"TYPE": VSS_DATA_TYPE, "DIM": VSS_DIMENSION, "DISTANCE_METRIC": VSS_DISTANCE}))
    r.ft('gov_idx').create_index(schema, definition=index_def)
    print("Index created successfully")

def add_faqs_to_hash(faqs_array):
    index = 0
    for faq in tqdm(faqs_array):
        embedding_list = json.loads(faq["embedding"])
        embedding = np.array(embedding_list, dtype=np.float32).tobytes()
        r.hset(
            f"gov:faqs:{index}",
            mapping={
                "title": faq["title"],
                "content": faq["content"],
                "link": faq["link"],
                "embedding": embedding
            }
        )
        index += 1


if __name__ == "__main__":
    create_idx()
    with open("faqs_with_embeddings.json", "r") as f:
        faqs_array = json.load(f)
    add_faqs_to_hash(faqs_array)
    print("All FAQs added to Redis successfully")
