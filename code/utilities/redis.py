'''Helper function for Redis'''

import logging
from typing import Any, Callable, List

from langchain.vectorstores.redis import Redis
import pandas as pd
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.field import VectorField, TextField

logger = logging.getLogger()

class RedisExtended(Redis):
    'Helper class for Redis'
    def __init__(
        self,
        redis_url: str,
        index_name: str,
        embedding_function: Callable,
        **kwargs: Any,
    ):
        super().__init__(redis_url, index_name, embedding_function)

        # Check if index exists
        try:
            self.client.ft("prompt-index").info()
        # pylint disable=bare-except
        except:
            # Create Redis Index
            self.create_prompt_index()

        try:
            self.client.ft(self.index_name).info()
        # pylint disable=bare-except
        except:
            # Create Redis Index
            self.create_index()

    def check_existing_index(self, index_name: str = ''):
        'Check if the index exists'
        try:
            self.client.ft(index_name if index_name else self.index_name).info()
            return True
        # pylint disable=bare-except
        except:
            return False

    def delete_keys(self, keys: List[str]) -> None:
        'Delete keys from Redis'
        for key in keys:
            self.client.delete(key)

    def delete_keys_pattern(self, pattern: str) -> None:
        'Delete keys from Redis based on pattern'
        keys = self.client.keys(pattern)
        self.delete_keys(keys)

    def create_index(self, prefix = "doc", distance_metric:str="COSINE"):
        'Create Redis Index'
        content = TextField(name="content")
        metadata = TextField(name="metadata")
        content_vector = VectorField("content_vector",
                    "HNSW", {
                        "TYPE": "FLOAT32",
                        "DIM": 1536,
                        "DISTANCE_METRIC": distance_metric,
                        "INITIAL_CAP": 1000,
                    })
        # Create index
        self.client.ft(self.index_name).create_index(
            fields = [content, metadata, content_vector],
            definition = IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
        )

    # Prompt management
    def create_prompt_index(self, index_name="prompt-index", prefix = "prompt"):
        'Create Redis Index for prompt results'
        result = TextField(name="result")
        filename = TextField(name="filename")
        prompt = TextField(name="prompt")
        # Create index
        self.client.ft(index_name).create_index(
            fields = [result, filename, prompt],
            definition = IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
        )

    def add_prompt_result(self, id, result, filename="", prompt=""):
        'Add prompt result to Redis'
        self.client.hset(
            f"prompt:{id}",
            mapping={
                "result": result,
                "filename": filename,
                "prompt": prompt
            }
        )

    def get_prompt_results(self, prompt_index_name="prompt-index", number_of_results: int=3155):
        'Get prompt results from Redis'
        base_query = '*'
        return_fields = ['id','result','filename','prompt']
        query = Query(base_query)\
            .paging(0, number_of_results)\
            .return_fields(*return_fields)\
            .dialect(2)
        results = self.client.ft(prompt_index_name).search(query)
        if results.docs:
            # pylint disable=line-too-long
            return pd.DataFrame(list(map(lambda x: {'id' : x.id, 'filename': x.filename, 'prompt': x.prompt, 'result': x.result.replace('\n',' ').replace('\r',' '),}, results.docs))).sort_values(by='id')

        return pd.DataFrame()

    def delete_prompt_results(self, prefix="prompt*"):
        'Delete prompt results from Redis'
        self.delete_keys_pattern(pattern=prefix)
