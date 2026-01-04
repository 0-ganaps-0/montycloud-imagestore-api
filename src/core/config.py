from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # AWS / LocalStack Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    # Set to None or empty string in production to use real AWS endpoints
    AWS_ENDPOINT_URL: Optional[str] = "http://localhost:4566"

    # S3 & DynamoDB Names
    S3_BUCKET_NAME: str = "image-store-bucket"
    DYNAMODB_TABLE_NAME: str = "ImageMetadataTable"

    # Load from .env file if it exists
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
