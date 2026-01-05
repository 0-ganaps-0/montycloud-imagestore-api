
# tests/test_list_extended.py
import json
import base64

from src.handlers import upload_handler, list_handler

def _upload(user_id, tags):
    ev = {"body": json.dumps({
        "user_id": user_id,
        "title": "t",
        "tags": tags,
        "content_type": "image/png",
        "image_base64": base64.b64encode(b"xyz").decode(),
    })}
    return upload_handler.handler(ev, None)

def test_list_requires_filter():
    resp = list_handler.handler({"queryStringParameters": {}}, None)
    assert resp["statusCode"] == 400

def test_list_by_user_and_tag_and_pagination():
    # uA: 3 images with tag 'demo'; uB: 1 image with tag 'other'
    _upload("uA", ["demo"])
    _upload("uA", ["demo", "extra"])
    _upload("uA", ["demo"])
    _upload("uB", ["other"])

    # by user_id only, limit=1 -> expect next_token
    resp = list_handler.handler({"queryStringParameters": {"user_id": "uA", "limit": "1"}}, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert len(body["items"]) == 1
    assert body["next_token"] is not None

    # use next_token to fetch next page
    resp2 = list_handler.handler({"queryStringParameters": {"user_id": "uA", "limit": "1", "last_evaluated_key": body["next_token"]}}, None)
    body2 = json.loads(resp2["body"])
    assert len(body2["items"]) == 1

    # by tag only
    rt = list_handler.handler({"queryStringParameters": {"tag": "demo"}}, None)
    assert rt["statusCode"] == 200
    assert len(json.loads(rt["body"])["items"]) >= 3

    # intersection: user_id=uA AND tag=demo -> 3 items
    r3 = list_handler.handler({"queryStringParameters": {"user_id": "uA", "tag": "demo"}}, None)
    assert r3["statusCode"] == 200
    assert len(json.loads(r3["body"])["items"]) == 3

    # intersection empty: user_id=uB AND tag=demo -> 0
    r4 = list_handler.handler({"queryStringParameters": {"user_id": "uB", "tag": "demo"}}, None)
    assert r4["statusCode"] == 200
    assert len(json.loads(r4["body"])["items"]) == 0

def test_list_bad_pagination_token():
    # invalid token -> should bubble up as 500 (json.loads failure)
    resp = list_handler.handler({"queryStringParameters": {"user_id": "uA", "last_evaluated_key": "not-json"}}, None)
    assert resp["statusCode"] == 500
