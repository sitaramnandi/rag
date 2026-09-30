from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimension: int = 1536

    aws_region: str = "us-east-1"
    s3_vector_bucket: str
    s3_vector_index: str

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_top_k: int = 5


settings = Settings()
