
import os
import json
from typing import List

from common.aws_clients import s3_client, ddb_resource
from common.response import json_response
from common.utils import decode_b64, sha256_hex, gen_id, now_iso


def _validate(payload: dict):
    required = ["user_id", "title", "tags", "content_type", "image_base64"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")
    if not isinstance(payload.get("tags"), list) or not payload["tags"]:
        raise ValueError("'tags' must be a non-empty list")


def handler(event, context):
    BUCKET = os.getenv("S3_BUCKET_NAME", "image-service-bucket")
    IMAGES_TABLE = os.getenv("IMAGES_TABLE_NAME", "images")
    TAGS_TABLE = os.getenv("IMAGE_TAGS_TABLE_NAME", "image_tags")
    try:
        payload = json.loads(event.get("body") or "{}")
        _validate(payload)
        user_id = payload["user_id"]
        title = payload["title"]
        description = payload.get("description", "")
        tags: List[str] = [t.strip().lower() for t in payload["tags"] if t and isinstance(t, str)]
        content_type = payload["content_type"]
        image_bytes = decode_b64(payload["image_base64"])
        checksum = sha256_hex(image_bytes)
        size = len(image_bytes)
        image_id = gen_id()
        s3_key = f"images/{image_id}"
        created_at = now_iso()

        s3 = s3_client()
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=image_bytes, ContentType=content_type,
                      Metadata={"user_id": user_id, "title": title})

        ddb = ddb_resource()
        images_tbl = ddb.Table(IMAGES_TABLE)
        tags_tbl = ddb.Table(TAGS_TABLE)

        item = {
            "image_id": image_id,
            "user_id": user_id,
            "title": title,
            "description": description,
            "tags": tags,
            "content_type": content_type,
            "s3_bucket": BUCKET,
            "s3_key": s3_key,
            "size": size,
            "checksum": checksum,
            "created_at": created_at,
        }
        images_tbl.put_item(Item=item)

        with tags_tbl.batch_writer() as batch:
            for t in tags:
                batch.put_item(Item={"tag": t, "image_id": image_id, "user_id": user_id, "created_at": created_at})

        return json_response(201, item)

    except ValueError as ve:
        return json_response(400, {"error": str(ve)})
    except Exception as e:
        return json_response(500, {"error": f"Upload failed: {e}"})
