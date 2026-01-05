
# tests/test_get_delete_extended.py
import json
import base64
import pytest

from src.handlers import upload_handler, get_handler, delete_handler

def _do_upload():
    ev = {"body": json.dumps({
        "user_id": "u1",
        "title": "x",
        "tags": ["demo"],
        "content_type": "image/png",
        "image_base64": base64.b64encode(b"xyz").decode(),
    })}
    up = upload_handler.handler(ev, None)
    assert up["statusCode"] == 201
    return json.loads(up["body"])["image_id"]

def test_get_metadata_and_download():
    iid = _do_upload()

    # get metadata by pathParameters
    r = get_handler.handler({"pathParameters": {"image_id": iid}, "rawPath": f"/images/{iid}"}, None)
    assert r["statusCode"] == 200
    assert json.loads(r["body"])["image_id"] == iid

    # get presigned URL via /download
    r2 = get_handler.handler({"pathParameters": {"image_id": iid}, "rawPath": f"/images/{iid}/download"}, None)
    assert r2["statusCode"] == 200
    assert "url" in json.loads(r2["body"])

def test_get_missing_image_id():
    r = get_handler.handler({"pathParameters": {}, "rawPath": "/images/"}, None)
    assert r["statusCode"] == 400

def test_get_not_found():
    r = get_handler.handler({"pathParameters": {"image_id": "does-not-exist"}, "rawPath": "/images/does-not-exist"}, None)
    assert r["statusCode"] == 404

def test_get_presigned_error(monkeypatch):
    iid = _do_upload()
    class FakeS3:
        def generate_presigned_url(self, *a, **k):
            raise Exception("boom")
    monkeypatch.setattr("src.handlers.get_handler.s3_client", lambda: FakeS3())

    r = get_handler.handler({"pathParameters": {"image_id": iid}, "rawPath": f"/images/{iid}/download"}, None)
    # our handler bubbles exception as 500
    assert r["statusCode"] == 500

def test_delete_success_and_errors():
    iid = _do_upload()

    # delete success
    d = delete_handler.handler({"pathParameters": {"image_id": iid}, "rawPath": f"/images/{iid}"}, None)
    assert d["statusCode"] == 204

    # delete not found
    d2 = delete_handler.handler({"pathParameters": {"image_id": "does-not-exist"}, "rawPath": "/images/does-not-exist"}, None)
    assert d2["statusCode"] == 404

def test_delete_missing_id():
    d = delete_handler.handler({"pathParameters": {}, "rawPath": "/images/"}, None)
    assert d["statusCode"] == 400

def test_delete_s3_error(monkeypatch):
    iid = _do_upload()
    class FakeS3:
        def delete_object(self, **kwargs):
            raise Exception("S3 delete failed")
    monkeypatch.setattr("src.handlers.delete_handler.s3_client", lambda: FakeS3())

    d = delete_handler.handler({"pathParameters": {"image_id": iid}, "rawPath": f"/images/{iid}"}, None)
    assert d["statusCode"] == 500
