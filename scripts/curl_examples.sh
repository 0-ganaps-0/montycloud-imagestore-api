
#!/usr/bin/env bash
set -euo pipefail

API_ID=$(awslocal apigateway get-rest-apis --query 'items[?name==`images-api`].id' --output text)
BASE="http://localhost:4566/restapis/${API_ID}/dev/_user_request_"

case "$1" in
  upload)
    IMG_PATH=${2:-/tmp/red.png}
    B64=$(base64 -w0 "$IMG_PATH")
    curl -s -X POST "${BASE}/images" -H 'Content-Type: application/json' -d @- <<JSON
{
  "user_id": "user123",
  "title": "Sample",
  "description": "Demo",
  "tags": ["demo","sample"],
  "content_type": "image/png",
  "image_base64": "${B64}"
}
JSON
    ;;
  list_user)
    USER=${2}
    curl -s "${BASE}/images?user_id=${USER}" ;;
  list_tag)
    TAG=${2}
    curl -s "${BASE}/images?tag=${TAG}" ;;
  get)
    ID=${2}
    curl -s "${BASE}/images/${ID}" ;;
  download)
    ID=${2}
    curl -s "${BASE}/images/${ID}/download" ;;
  delete)
    ID=${2}
    curl -s -X DELETE "${BASE}/images/${ID}" ;;
  *)
    echo "Usage: $0 [upload <img_path>|list_user <user>|list_tag <tag>|get <id>|download <id>|delete <id>]" ;;
 esac
