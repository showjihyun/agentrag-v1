"""Data tool integrations.

This module provides integrations for data services including:
- MongoDB
- PostgreSQL
- MySQL
- Supabase
- Pinecone
- Qdrant
- S3
- Redis
- Elasticsearch
- BigQuery
"""

import logging

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


# Supabase Query
@ToolRegistry.register(
    tool_id="supabase_query",
    name="Supabase Query",
    description="Query data from Supabase",
    category="data",
    params={
        "table": ParamConfig(type="string", description="Table name", required=True),
        "select": ParamConfig(type="string", description="Columns to select", default="*"),
        "filter": ParamConfig(type="object", description="Filter conditions", required=False)
    },
    outputs={
        "data": OutputConfig(type="array", description="Query results")
    },
    request=RequestConfig(
        method="GET",
        url="https://{{project_ref}}.supabase.co/rest/v1/{{table}}",
        headers={"Content-Type": "application/json", "apikey": "{{api_key}}"},
        query_params={"select": "{{select}}"}
    ),
    api_key_env="SUPABASE_API_KEY",
    transform_response=lambda x: {"data": x},
    icon="database",
    bg_color="#3ECF8E",
    docs_link="https://supabase.com/docs/reference/javascript/select"
)
class SupabaseQueryTool:
    pass


# Pinecone Upsert
@ToolRegistry.register(
    tool_id="pinecone_upsert",
    name="Pinecone Upsert Vectors",
    description="Upsert vectors to Pinecone index",
    category="data",
    params={
        "index_name": ParamConfig(type="string", description="Index name", required=True),
        "vectors": ParamConfig(type="array", description="Vectors to upsert", required=True),
        "namespace": ParamConfig(type="string", description="Namespace", required=False)
    },
    outputs={
        "upserted_count": OutputConfig(type="number", description="Number of vectors upserted")
    },
    request=RequestConfig(
        method="POST",
        url="https://{{index_name}}-{{project_id}}.svc.{{environment}}.pinecone.io/vectors/upsert",
        headers={"Content-Type": "application/json"},
        body_template={"vectors": "{{vectors}}", "namespace": "{{namespace}}"}
    ),
    api_key_env="PINECONE_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"upserted_count": "upsertedCount"}
    ),
    icon="database",
    bg_color="#000000",
    docs_link="https://docs.pinecone.io/reference/upsert"
)
class PineconeUpsertTool:
    pass


# Qdrant Insert
@ToolRegistry.register(
    tool_id="qdrant_insert",
    name="Qdrant Insert Points",
    description="Insert points into Qdrant collection",
    category="data",
    params={
        "collection_name": ParamConfig(type="string", description="Collection name", required=True),
        "points": ParamConfig(type="array", description="Points to insert", required=True)
    },
    outputs={
        "status": OutputConfig(type="string", description="Operation status")
    },
    request=RequestConfig(
        method="PUT",
        url="https://{{qdrant_url}}/collections/{{collection_name}}/points",
        headers={"Content-Type": "application/json"},
        body_template={"points": "{{points}}"}
    ),
    api_key_env="QDRANT_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"status": "status"}
    ),
    icon="database",
    bg_color="#DC244C",
    docs_link="https://qdrant.tech/documentation/concepts/points/"
)
class QdrantInsertTool:
    pass


# AWS S3 Upload
@ToolRegistry.register(
    tool_id="s3_upload",
    name="S3 Upload File",
    description="Upload file to AWS S3",
    category="data",
    params={
        "bucket": ParamConfig(type="string", description="S3 bucket name", required=True),
        "key": ParamConfig(type="string", description="Object key (path)", required=True),
        "content": ParamConfig(type="string", description="File content", required=True),
        "content_type": ParamConfig(type="string", description="Content type", default="application/octet-stream")
    },
    outputs={
        "url": OutputConfig(type="string", description="Object URL"),
        "etag": OutputConfig(type="string", description="ETag")
    },
    request=RequestConfig(
        method="PUT",
        url="https://{{bucket}}.s3.amazonaws.com/{{key}}",
        headers={"Content-Type": "{{content_type}}"},
        body_template="{{content}}"
    ),
    api_key_env="AWS_ACCESS_KEY_ID",
    icon="cloud",
    bg_color="#FF9900",
    docs_link="https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html"
)
class S3UploadTool:
    pass


# MongoDB Insert
@ToolRegistry.register(
    tool_id="mongodb_insert",
    name="MongoDB Insert Document",
    description="Insert document into MongoDB",
    category="data",
    params={
        "database": ParamConfig(type="string", description="Database name", required=True),
        "collection": ParamConfig(type="string", description="Collection name", required=True),
        "document": ParamConfig(type="object", description="Document to insert", required=True)
    },
    outputs={
        "inserted_id": OutputConfig(type="string", description="Inserted document ID")
    },
    request=RequestConfig(
        method="POST",
        url="https://{{cluster_url}}/app/{{app_id}}/endpoint/data/v1/action/insertOne",
        headers={"Content-Type": "application/json"},
        body_template={
            "dataSource": "{{cluster_name}}",
            "database": "{{database}}",
            "collection": "{{collection}}",
            "document": "{{document}}"
        }
    ),
    api_key_env="MONGODB_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"inserted_id": "insertedId"}
    ),
    icon="database",
    bg_color="#00ED64",
    docs_link="https://www.mongodb.com/docs/atlas/api/data-api/"
)
class MongoDBInsertTool:
    pass


# PostgreSQL Query (via Supabase-style REST API)
@ToolRegistry.register(
    tool_id="postgresql_query",
    name="PostgreSQL Query",
    description="Execute PostgreSQL query via REST API",
    category="data",
    params={
        "query": ParamConfig(type="string", description="SQL query", required=True),
        "params": ParamConfig(type="array", description="Query parameters", required=False)
    },
    outputs={
        "rows": OutputConfig(type="array", description="Query results")
    },
    request=RequestConfig(
        method="POST",
        url="{{postgresql_api_url}}/query",
        headers={"Content-Type": "application/json"},
        body_template={"query": "{{query}}", "params": "{{params}}"}
    ),
    api_key_env="POSTGRESQL_API_KEY",
    transform_response=lambda x: {"rows": x.get("rows", [])},
    icon="database",
    bg_color="#336791",
    docs_link="https://www.postgresql.org/docs/"
)
class PostgreSQLQueryTool:
    pass


# MySQL Query
@ToolRegistry.register(
    tool_id="mysql_query",
    name="MySQL Query",
    description="Execute MySQL query via REST API",
    category="data",
    params={
        "query": ParamConfig(type="string", description="SQL query", required=True),
        "params": ParamConfig(type="array", description="Query parameters", required=False)
    },
    outputs={
        "rows": OutputConfig(type="array", description="Query results")
    },
    request=RequestConfig(
        method="POST",
        url="{{mysql_api_url}}/query",
        headers={"Content-Type": "application/json"},
        body_template={"query": "{{query}}", "params": "{{params}}"}
    ),
    api_key_env="MYSQL_API_KEY",
    transform_response=lambda x: {"rows": x.get("rows", [])},
    icon="database",
    bg_color="#00758F",
    docs_link="https://dev.mysql.com/doc/"
)
class MySQLQueryTool:
    pass


# Redis Set
@ToolRegistry.register(
    tool_id="redis_set",
    name="Redis Set Key",
    description="Set key-value in Redis",
    category="data",
    params={
        "key": ParamConfig(type="string", description="Key", required=True),
        "value": ParamConfig(type="string", description="Value", required=True),
        "ex": ParamConfig(type="number", description="Expiration in seconds", required=False)
    },
    outputs={
        "status": OutputConfig(type="string", description="Operation status")
    },
    request=RequestConfig(
        method="POST",
        url="{{redis_api_url}}/set",
        headers={"Content-Type": "application/json"},
        body_template={"key": "{{key}}", "value": "{{value}}", "ex": "{{ex}}"}
    ),
    api_key_env="REDIS_API_KEY",
    transform_response=lambda x: {"status": "OK"},
    icon="database",
    bg_color="#DC382D",
    docs_link="https://redis.io/commands/set/"
)
class RedisSetTool:
    pass


# Elasticsearch Index
@ToolRegistry.register(
    tool_id="elasticsearch_index",
    name="Elasticsearch Index Document",
    description="Index document in Elasticsearch",
    category="data",
    params={
        "index": ParamConfig(type="string", description="Index name", required=True),
        "document": ParamConfig(type="object", description="Document to index", required=True),
        "id": ParamConfig(type="string", description="Document ID", required=False)
    },
    outputs={
        "id": OutputConfig(type="string", description="Document ID"),
        "result": OutputConfig(type="string", description="Index result")
    },
    request=RequestConfig(
        method="POST",
        url="{{elasticsearch_url}}/{{index}}/_doc/{{id}}",
        headers={"Content-Type": "application/json"},
        body_template="{{document}}"
    ),
    api_key_env="ELASTICSEARCH_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        field_mapping={"id": "_id", "result": "result"}
    ),
    icon="search",
    bg_color="#005571",
    docs_link="https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html"
)
class ElasticsearchIndexTool:
    pass


# Google BigQuery Query
@ToolRegistry.register(
    tool_id="bigquery_query",
    name="BigQuery Query",
    description="Execute query in Google BigQuery",
    category="data",
    params={
        "project_id": ParamConfig(type="string", description="Project ID", required=True),
        "query": ParamConfig(type="string", description="SQL query", required=True)
    },
    outputs={
        "rows": OutputConfig(type="array", description="Query results")
    },
    request=RequestConfig(
        method="POST",
        url="https://bigquery.googleapis.com/bigquery/v2/projects/{{project_id}}/queries",
        headers={"Content-Type": "application/json"},
        body_template={"query": "{{query}}", "useLegacySql": False}
    ),
    api_key_env="GOOGLE_CLOUD_API_KEY",
    transform_response=ResponseTransformer.create_transformer(
        array_path="rows"
    ),
    icon="database",
    bg_color="#4285F4",
    docs_link="https://cloud.google.com/bigquery/docs/reference/rest/v2/jobs/query"
)
class BigQueryQueryTool:
    pass


logger.info("Registered 10 data tools")
