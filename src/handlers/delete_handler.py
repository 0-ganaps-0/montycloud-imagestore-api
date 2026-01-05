
import os
from common.aws_clients import s3_client, ddb_resource
from common.response import json_response, no_content


def handler(event, context):
    BUCKET = os.getenv("S3_BUCKET_NAME", "image-service-bucket")
    IMAGES_TABLE = os.getenv("IMAGES_TABLE_NAME", "images")
    TAGS_TABLE = os.getenv("IMAGE_TAGS_TABLE_NAME", "image_tags")
    try:
        path_params = event.get("pathParameters") or {}
        image_id = path_params.get("image_id")
        if not image_id:
            raw_path = event.get("rawPath") or event.get("path") or ""
            if raw_path.startswith("/images/"):
                parts = raw_path.strip("/").split("/")
                if len(parts) >= 2:
                    image_id = parts[1]
        if not image_id:
            return json_response(400, {"error": "image_id required"})

        ddb = ddb_resource()
        images_tbl = ddb.Table(IMAGES_TABLE)
        tags_tbl = ddb.Table(TAGS_TABLE)
        r = images_tbl.get_item(Key={"image_id": image_id})
        item = r.get("Item")
        if not item:
            return json_response(404, {"error": "Not found"})

        s3 = s3_client()
        s3.delete_object(Bucket=item['s3_bucket'], Key=item['s3_key'])

        images_tbl.delete_item(Key={"image_id": image_id})

        tags = item.get("tags", [])
        with tags_tbl.batch_writer() as batch:
            for t in tags:
                batch.delete_item(Key={"tag": t, "image_id": image_id})

        return no_content()
    except Exception as e:
        return json_response(500, {"error": f"Delete failed: {e}"})
