
import os
from common.aws_clients import s3_client, ddb_resource
from common.response import json_response


def handler(event, context):
    BUCKET = os.getenv("S3_BUCKET_NAME", "image-service-bucket")
    IMAGES_TABLE = os.getenv("IMAGES_TABLE_NAME", "images")
    try:
        raw_path = event.get("rawPath") or event.get("path") or ""
        path_params = event.get("pathParameters") or {}
        image_id = path_params.get("image_id")
        if not image_id:
            if raw_path.startswith("/images/"):
                parts = raw_path.strip("/").split("/")
                if len(parts) >= 2:
                    image_id = parts[1]
        if not image_id:
            return json_response(400, {"error": "image_id required"})

        ddb = ddb_resource()
        images_tbl = ddb.Table(IMAGES_TABLE)
        r = images_tbl.get_item(Key={"image_id": image_id})
        item = r.get("Item")
        if not item:
            return json_response(404, {"error": "Not found"})

        if raw_path.rstrip("/").endswith("download"):
            s3 = s3_client()
            url = s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={'Bucket': item['s3_bucket'], 'Key': item['s3_key']},
                ExpiresIn=3600
            )
            return json_response(200, {"url": url})

        return json_response(200, item)
    except Exception as e:
        return json_response(500, {"error": f"Get failed: {e}"})
