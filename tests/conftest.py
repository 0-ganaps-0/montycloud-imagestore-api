import os
import pytest
import boto3
from moto import mock_aws
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.core.config import settings
import pytest_asyncio


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_REGION"] = "us-east-1"

def setup_mocks(aws_credentials):
    with mock_aws():
        # 1. Create resources
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        
        db = boto3.resource("dynamodb", region_name="us-east-1")
        db.create_table(...) # (Your table creation code)

        # 2. OVERRIDE the manager to ensure it uses the mock clients
        def override_get_manager():
            return ImageManager()
        
        app.dependency_overrides[get_manager] = override_get_manager
        yield
        app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_aws_env():
    """Setup mock S3 bucket and DynamoDB table."""
    with mock_aws():
        # Setup S3
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)

        # Setup DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        dynamodb.create_table(
            TableName=settings.DYNAMODB_TABLE_NAME,
            KeySchema=[{"AttributeName": "ImageId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "ImageId", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )
        yield s3, dynamodb

@pytest_asyncio.fixture
async def async_client(mock_aws_env):
    """Async client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def s3_client(aws_credentials):
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
        yield client

@pytest.fixture
def table_setup(aws_credentials):
    with mock_aws():
        db = boto3.resource("dynamodb", region_name="us-east-1")
        table = db.create_table(
            TableName="ImageMetadataTable",
            KeySchema=[{"AttributeName": "ImageId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "ImageId", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1}
        )
        table.meta.client.get_waiter('table_exists').wait(TableName="ImageMetadataTable")
        yield table