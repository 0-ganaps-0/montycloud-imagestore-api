
# src/common/aws_clients.py
import os
import boto3
from botocore.config import Config

REGION = os.getenv("AWS_REGION", "us-east-1")
ENDPOINT = os.getenv("AWS_ENDPOINT_URL")

def s3_client():
    """
    Use path-style ONLY when talking to a custom endpoint (e.g., LocalStack).
    Under moto (endpoint is None), use default config to avoid unexpected validation issues.
    """
    if ENDPOINT:
        cfg = Config(s3={"addressing_style": "path"})
        return boto3.client("s3", region_name=REGION, endpoint_url=ENDPOINT, config=cfg)
    return boto3.client("s3", region_name=REGION)

def ddb_resource():
    # Endpoint is only needed for LocalStack. Under moto, leave it None.
    if ENDPOINT:
        return boto3.resource("dynamodb", region_name=REGION, endpoint_url=ENDPOINT)
    return boto3.resource("dynamodb", region_name=REGION)

def ddb_client():
    if ENDPOINT:
        return boto3.client("dynamodb", region_name=REGION, endpoint_url=ENDPOINT)
    return boto3.client("dynamodb", region_name=REGION)
