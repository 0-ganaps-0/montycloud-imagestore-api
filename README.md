
# Instagram-like Image Service (LocalStack) — API Gateway v1 (REST)

A scalable image upload service using **API Gateway (v1 REST)**, **Lambda**, **S3**, and **DynamoDB** with **Python 3.7+**. Metadata is stored in DynamoDB; binary images in S3. Designed for local development via **LocalStack**.

> **LocalStack Note:** API Gateway **v2 (HTTP/WebSocket)** requires LocalStack **Base/Pro**. This project uses **API Gateway v1 (REST API)** for broad compatibility with the **Free** plan. If you upgrade LocalStack, you can switch back to the v2 deploy script. 

---
## Features
- **Upload** image (base64) with metadata (user_id, title, description, tags, content_type)
- **List** images by **user_id** and/or **tag** (two filters, paginated)
- **Get** metadata or **download** via pre-signed URL
- **Delete** image and corresponding metadata/tag mappings
- **Scalable**: DynamoDB primary table + GSI for `user_id`; Tag queries use a dedicated `image_tags` table keyed by `tag`
- **IaC-free option**: Deploy via `awslocal` CLI script for simplicity & speed
- **Unit tests** using `pytest` and `moto`/`botocore` stubs
- **OpenAPI** documentation for the HTTP API

---
## Quickstart

### 1) Prerequisites
- Docker & Docker Compose
- Python 3.9 (3.7+ works, but tests target 3.9)
- `pip` / `venv`
- LocalStack & AWS CLI local helper: `pip install localstack awscli-local` (or use `requirements.txt`)

### 2) Start LocalStack
```bash
make up
```

### 3) Install dependencies (for tests & helpers)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Deploy the stack (S3, DynamoDB, IAM, Lambda, API Gateway v1 REST)
```bash
make deploy
```
This will:
- create S3 bucket: `image-service-bucket`
- create DynamoDB tables: `images` (GSI on `user_id`) and `image_tags`
- build & upload 4 Lambda functions
- create REST API routes at `/images`, `/images/{image_id}`, `/images/{image_id}/download`

### 5) Try the API

#### Upload (POST /images)
```bash
# Create a small sample image
python scripts/sample_image.py > /tmp/red.png

# Upload JSON (base64 payload)
curl -s -X POST "http://localhost:4566/restapis/$(awslocal apigateway get-rest-apis --query 'items[?name==\`images-api\`].id' -o text)/dev/_user_request_/images"   -H 'Content-Type: application/json'   -d @- <<'JSON'
{
  "user_id": "user123",
  "title": "Sunset",
  "description": "Evening sky",
  "tags": ["nature", "sunset"],
  "content_type": "image/png",
  "image_base64": "$(base64 -w0 /tmp/red.png)"
}
JSON
```

Alternatively, use the helper script:
```bash
scripts/curl_examples.sh upload /tmp/red.png
```

#### List by user_id (GET /images?user_id=user123)
```bash
scripts/curl_examples.sh list_user user123
```

#### List by tag (GET /images?tag=sample)
```bash
scripts/curl_examples.sh list_tag sample
```

#### Get metadata (GET /images/{image_id})
```bash
scripts/curl_examples.sh get <image_id>
```

#### Get pre-signed download URL (GET /images/{image_id}/download)
```bash
scripts/curl_examples.sh download <image_id>
```

#### Delete (DELETE /images/{image_id})
```bash
scripts/curl_examples.sh delete <image_id>
```

### 6) Run tests
```bash
pytest -q
```

### 7) Tear down
```bash
make destroy
make down
```

---
## Design Notes
- **Metadata table**: `images` with PK=`image_id`, and GSI `user_id-index` (partition=`user_id`, sort=`created_at`) for scalable user listings.
- **Tag index table**: `image_tags` with PK=`tag`, SK=`image_id` to support scalable tag queries without scans.
- **Upload path**: decode base64 → compute SHA256 → S3 put → metadata to `images` → tag mappings to `image_tags`.
- **List path**: by `user_id` (GSI query) OR by `tag` (query `image_tags` + batch get). If both provided, intersect results without scans.
- **Get path**: return metadata, or a pre-signed S3 URL for download.
- **Delete path**: delete S3 object, remove item in `images`, and tag mappings in `image_tags`.

---
## Environment Variables (Lambda)
- `S3_BUCKET_NAME`
- `IMAGES_TABLE_NAME` (default: `images`)
- `IMAGE_TAGS_TABLE_NAME` (default: `image_tags`)
- `AWS_REGION` (default: `us-east-1`)
- `AWS_ENDPOINT_URL` (optional; set to `http://localhost:4566` in LocalStack)

---
## API Docs
See [`api/openapi.yaml`](api/openapi.yaml) for request/response schemas and curl examples.

---
## License
MIT
