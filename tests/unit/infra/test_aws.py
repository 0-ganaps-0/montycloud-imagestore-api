import pytest
from src.infra.aws import get_s3_client, get_dynamodb_resource

@pytest.mark.unit
def test_get_s3_client_initialization(s3_client):
    """Verify S3 client is initialized with correct config."""
    assert s3_client.meta.region_name == "us-east-1"
    # Verify we can actually use the client
    response = s3_client.list_buckets()
    assert "Buckets" in response

@pytest.mark.unit
def test_get_dynamodb_resource_initialization(table_setup):
    """Verify DynamoDB resource is initialized and table is accessible."""
    assert table_setup.table_name == "ImageMetadataTable"
    table_setup.load() 
    assert table_setup.table_status == "ACTIVE"


@pytest.mark.unit
def test_aws_endpoint_override(mocker):
    """Test that the client respects the endpoint_url (Crucial for LocalStack)."""
    # Mock settings to simulate a LocalStack environment
    mocker.patch("src.infra.aws.settings.AWS_ENDPOINT_URL", "http://localhost:4566")
    
    override_client = get_s3_client()
    assert override_client._endpoint.host == "http://localhost:4566"
