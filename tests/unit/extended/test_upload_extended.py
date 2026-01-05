
# tests/test_upload_extended.py
import json
import base64
import pytest

from src.handlers import upload_handler

def test_upload_success(upload_req):
    ev = {"body": json.dumps(upload_req)}
    resp = upload_handler.handler(ev, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["user_id"] == "u1"
    # tags normalized to lowercase
    assert body["tags"] == ["demo", "test"]
    assert body["content_type"] == "image/png"
    assert body["s3_bucket"] == "test-bucket"
    assert "image_id" in body
    assert "checksum" in body
    assert "created_at" in body

def test_upload_minimal(upload_req_minimal):
    ev = {"body": json.dumps(upload_req_minimal)}
    resp = upload_handler.handler(ev, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["description"] == ""  # defaulted
    assert body["tags"] == ["onlytag"]
    assert body["user_id"] == "u2"

def test_upload_missing_fields():
    # missing tags, content_type, image_base64
    bad = {"user_id": "u1", "title": "x"}
    resp = upload_handler.handler({"body": json.dumps(bad)}, None)
    assert resp["statusCode"] == 400
    assert "Missing fields" in json.loads(resp["body"])["error"]

def test_upload_empty_tags():
    bad = {"user_id": "u1", "title": "x", "tags": [], "content_type": "image/png", "image_base64": base64.b64encode(b"123").decode()}
    resp = upload_handler.handler({"body": json.dumps(bad)}, None)
    assert resp["statusCode"] == 400
    assert "must be a non-empty list" in json.loads(resp["body"])["error"]

def test_upload_invalid_base64():
    bad = {"user_id": "u1", "title": "x", "tags": ["a"], "content_type": "image/png", "image_base64": "!!!not-b64!!!"}
    resp = upload_handler.handler({"body": json.dumps(bad)}, None)
    assert resp["statusCode"] == 400
    assert "Invalid base64" in json.loads(resp["body"])["error"]

def test_upload_s3_failure(monkeypatch, upload_req):
    class FakeS3:
        def put_object(self, **kwargs):
            raise Exception("S3 put failed")
    monkeypatch.setattr("src.handlers.upload_handler.s3_client", lambda: FakeS3())

    resp = upload_handler.handler({"body": json.dumps(upload_req)}, None)
    assert resp["statusCode"] == 500
    assert "Upload failed" in json.loads(resp["body"])["error"]

def test_upload_ddb_failure(monkeypatch, upload_req):
    class FakeTable:
        def put_item(self, Item):
            raise Exception("DDB put failed")
    class FakeResource:
        def Table(self, name):
            return FakeTable()
    monkeypatch.setattr("src.handlers.upload_handler.ddb_resource", lambda: FakeResource())

    resp = upload_handler.handler({"body": json.dumps(upload_req)}, None)
    assert resp["statusCode"] == 500
    assert "Upload failed" in json.loads(resp["body"])["error"]
