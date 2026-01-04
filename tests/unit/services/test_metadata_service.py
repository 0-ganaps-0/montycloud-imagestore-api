import boto3
import pytest
from moto import mock_aws
from src.services.metadata_service import MetadataService


@pytest.mark.unit
def test_save_and_list_with_filters(table_setup):
    service = MetadataService()
    service.save_metadata("id1", "vacation.png", "image/png", ["holiday", "blue"])

    # Test filtering by tag
    results = service.list_images(tag_filter="holiday")
    assert len(results) == 1
    assert results[0]["Filename"] == "vacation.png"

    # Test filtering by name
    results = service.list_images(name_filter="vacation")
    assert len(results) == 1


