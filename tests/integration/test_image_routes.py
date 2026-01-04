import pytest
import json
from unittest.mock import patch
from src.api.image_routes import get_manager, ImageManager


async def test_full_image_workflow(async_client):
    # 1. Test Upload
    files = {"file": ("test.jpg", b"fake_data", "image/jpeg")}
    data = {"tags": json.dumps(["nature", "vacation"])}

    response = await async_client.post("/images/upload", files=files, data=data)
    assert response.status_code == 201
    image_id = response.json()["data"]["ImageId"]

    # 2. Test List with Filter
    list_resp = await async_client.get("/images/", params={"tag": "nature"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Test Download URL
    view_resp = await async_client.get(f"/images/{image_id}")
    assert view_resp.status_code == 200
    assert "download_url" in view_resp.json()

    # 4. Test Delete
    del_resp = await async_client.delete(f"/images/{image_id}")
    assert del_resp.status_code == 204


async def test_upload_invalid_tags(async_client):
    files = {"file": ("test.jpg", b"data", "image/jpeg")}
    data = {"tags": "not-a-json-list"}

    response = await async_client.post("/images/upload", files=files, data=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Tags must be a valid JSON list"


async def test_upload_image_success(async_client):
    """Covers lines 11-27 (Success path)"""
    files = {"file": ("test.png", b"fakecontent", "image/png")}
    data = {"tags": json.dumps(["tag1", "tag2"])}
    response = await async_client.post("/images/upload", files=files, data=data)
    assert response.status_code == 201
    assert response.json()["message"] == "Upload successful"

async def test_upload_image_invalid_json_tags(async_client):
    """Covers lines 23-24 (ValueError for non-JSON tags)"""
    files = {"file": ("test.png", b"fakecontent", "image/png")}
    data = {"tags": "invalid-json"}
    response = await async_client.post("/images/upload", files=files, data=data)
    assert response.status_code == 400
    assert "JSON list" in response.json()["detail"]

async def test_upload_image_not_a_list(async_client):
    """Covers lines 21-22 (ValueError for JSON that isn't a list)"""
    files = {"file": ("test.png", b"fakecontent", "image/png")}
    data = {"tags": json.dumps({"not": "a-list"})}
    response = await async_client.post("/images/upload", files=files, data=data)
    assert response.status_code == 400

async def test_list_images_with_filters(async_client):
    """Covers lines 30-36 (List and Filters)"""
    # Test without filters
    response = await async_client.get("/images/")
    assert response.status_code == 200
    # Test with filters
    response = await async_client.get("/images/", params={"tag": "nature", "name": "test"})
    assert response.status_code == 200

async def test_get_image_url_not_found(async_client):
    """Covers lines 42-43 (404 Error)"""
    response = await async_client.get("/images/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"

async def test_get_image_url_success(async_client):
    """Covers lines 40-47 (Success path for View)"""
    # First upload an image to ensure it exists in metadata
    files = {"file": ("test.png", b"data", "image/png")}
    data = {"tags": json.dumps(["test"])}
    up = await async_client.post("/images/upload", files=files, data=data)
    image_id = up.json()["data"]["ImageId"]

    response = await async_client.get(f"/images/{image_id}")
    assert response.status_code == 200
    assert "download_url" in response.json()

async def test_delete_image_success(async_client):
    """Covers lines 50-54 (Success path for Delete)"""
    response = await async_client.delete("/images/some-id")
    assert response.status_code == 204

# async def test_delete_image_exception(async_client):
#     """Covers lines 55-57 (500 Error path)"""
#     # Mock process_deletion to raise an exception
#     with patch("src.api.image_routes.manager.process_deletion", side_effect=Exception("DB Error")):
#         response = await async_client.delete("/images/error-id")
#         assert response.status_code == 500
#         assert "Deletion failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_image_exception(async_client, mock_aws_env):
    """Covers lines 55-57 (500 Error path)"""
    class FailingManager(ImageManager):
        def process_deletion(self, image_id: str):
            raise Exception("DB Connection Failed")
    app.dependency_overrides[get_manager] = lambda: FailingManager()

    try:
        response = await async_client.delete("/images/error-id")
        assert response.status_code == 500
        assert "Deletion failed" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()