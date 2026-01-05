
# src/handlers/list_handler.py

import os
import json
from typing import Dict, List, Set

from common.aws_clients import ddb_resource
from common.response import json_response


def handler(event, context):
    IMAGES_TABLE = os.getenv("IMAGES_TABLE_NAME", "images")
    TAGS_TABLE = os.getenv("IMAGE_TAGS_TABLE_NAME", "image_tags")
    try:
        params = event.get("queryStringParameters") or {}
        user_id = params.get("user_id") if params else None
        tag = params.get("tag") if params else None
        limit = int(params.get("limit", 20))
        next_token = params.get("last_evaluated_key")

        ddb = ddb_resource()
        images_tbl = ddb.Table(IMAGES_TABLE)
        tags_tbl = ddb.Table(TAGS_TABLE)

        items: List[Dict] = []
        token_out = None

        if tag and not user_id:
            from boto3.dynamodb.conditions import Key
            query_kwargs = {
                "KeyConditionExpression": Key("tag").eq(tag.lower()),
                "Limit": limit,
            }
            if next_token:
                query_kwargs["ExclusiveStartKey"] = json.loads(next_token)

            resp = tags_tbl.query(**query_kwargs)
            image_ids = [r["image_id"] for r in resp.get("Items", [])]
            token_out = json.dumps(resp.get("LastEvaluatedKey")) if resp.get("LastEvaluatedKey") else None

            if image_ids:
                got = []
                for iid in image_ids:
                    r = images_tbl.get_item(Key={"image_id": iid})
                    if "Item" in r:
                        got.append(r["Item"])
                items = got

        elif user_id and not tag:
            from boto3.dynamodb.conditions import Key
            query_kwargs = {
                "IndexName": "user_id-index",
                "KeyConditionExpression": Key("user_id").eq(user_id),
                "Limit": limit,
            }
            if next_token:
                query_kwargs["ExclusiveStartKey"] = json.loads(next_token)

            q = images_tbl.query(**query_kwargs)
            items = q.get("Items", [])
            token_out = json.dumps(q.get("LastEvaluatedKey")) if q.get("LastEvaluatedKey") else None

        elif user_id and tag:
            from boto3.dynamodb.conditions import Key
            tag_q_kwargs = {
                "KeyConditionExpression": Key("tag").eq(tag.lower()),
                "Limit": limit,
            }
            if next_token:
                tag_q_kwargs["ExclusiveStartKey"] = json.loads(next_token)

            resp = tags_tbl.query(**tag_q_kwargs)
            tag_ids: Set[str] = set([r["image_id"] for r in resp.get("Items", [])])

            user_q = images_tbl.query(
                IndexName="user_id-index",
                KeyConditionExpression=Key("user_id").eq(user_id),
                Limit=limit,
            )
            items = [it for it in user_q.get("Items", []) if it.get("image_id") in tag_ids]
            token_out = json.dumps(resp.get("LastEvaluatedKey")) if resp.get("LastEvaluatedKey") else None

        else:
            return json_response(400, {"error": "Provide at least one filter: user_id or tag"})

        return json_response(200, {"items": items, "next_token": token_out})

    except Exception as e:
        return json_response(500, {"error": f"List failed: {e}"})

