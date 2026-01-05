
# tests/conftest.py
import os
import sys
import json
import base64
import uuid
import pytest
import boto3
from moto import mock_aws

# Ensure "src/" is on module path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Keep unit tests isolated from LocalStack & external endpoints
os.environ.pop("AWS_ENDPOINT_URL", None)
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

# Constants used across tests
BUCKET_NAME = "test-bucket"
IMAGES_TABLE = "images"
TAGS_TABLE = "image_tags"

def _create_s3_bucket():
    s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    s3.create_bucket(Bucket=BUCKET_NAME)

def _create_tables():
    ddb = boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])
    # images table with GSI: user_id-index
    ddb.create_table(
        TableName=IMAGES_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "image_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        KeySchema=[{"AttributeName": "image_id", "KeyType": "HASH"}],
        BillingMode="PAY_PER_REQUEST",
        GlobalSecondaryIndexes=[{
            "IndexName": "user_id-index",
            "KeySchema": [
                {"AttributeName": "user_id", "KeyType": "HASH"},
                {"AttributeName": "created_at", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        }],
    )
    # image_tags table for tag queries
    ddb.create_table(
        TableName=TAGS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "tag", "AttributeType": "S"},
            {"AttributeName": "image_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "tag", "KeyType": "HASH"},
            {"AttributeName": "image_id", "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

@pytest.fixture(autouse=True)
def moto_env():
    """
    Auto-use fixture: spins up moto across each test function,
    sets essential env vars for handlers, and prepares S3 & DynamoDB.
    """
    os.environ["S3_BUCKET_NAME"] = BUCKET_NAME
    os.environ["IMAGES_TABLE_NAME"] = IMAGES_TABLE
    os.environ["IMAGE_TAGS_TABLE_NAME"] = TAGS_TABLE

    m = mock_aws()
    m.start()
    try:
        _create_s3_bucket()
        _create_tables()
        yield
    finally:
        m.stop()

@pytest.fixture
def upload_req():
    """
    Produce a basic valid upload payload (PNG base64).
    """
    png_bytes = b"\x89PNG\r\n\x1a\n" + os.urandom(16)  # small fake PNG
    return {
        "user_id": "u1",
        "title": "Sample",
        "description": "desc",
        "tags": ["demo", "Test"],
        "content_type": "image/png",
        "image_base64": base64.b64encode(png_bytes).decode(),
    }

@pytest.fixture
def upload_req_minimal():
    """
    Minimal valid upload payload (no description).
    """
    return {
        "user_id": "u2",
        "title": "T",
        "tags": ["onlytag"],
        "content_type": "image/jpeg",
        "image_base64": base64.b64encode(b"abc").decode(),
    }

def make_event(body_dict):
    return {"body": json.dumps(body_dict)}

def random_image_id():
    return str(uuid.uuid4())
