import pytest
from unittest.mock import MagicMock
from src.services.storage_service import StorageService


@pytest.mark.unit
def test_upload_image_success(s3_client):
    # Setup
    s3_client.create_bucket(Bucket="image-store-bucket")
    service = StorageService()
    mock_file = MagicMock()
    mock_file.filename = "test.jpg"

    # Act
    key = service.upload_image(mock_file)

    # Assert
    assert "test.jpg" in key
    response = s3_client.list_objects(Bucket="image-store-bucket")
    assert response["Contents"][0]["Key"] == key


@pytest.mark.unit
def test_get_download_url(s3_client):
    s3_client.create_bucket(Bucket="image-store-bucket")
    service = StorageService()
    url = service.get_download_url("some-key")
    assert "image-store-bucket" in url
    assert "some-key" in url
