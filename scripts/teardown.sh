
#!/usr/bin/env bash
set -euo pipefail
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=000000000000
API_NAME=images-api

export AWS_DEFAULT_REGION=${REGION}

if ! command -v awslocal >/dev/null 2>&1; then
  echo "awslocal not found. Install with: pip install awscli-local" && exit 1
fi

API_ID=$(awslocal apigateway get-rest-apis --query "items[?name=='${API_NAME}'].id" --output text || true)
if [ -n "${API_ID}" ]; then
  awslocal apigateway delete-rest-api --rest-api-id ${API_ID} || true
fi

for FN in images-upload images-list images-get images-delete; do
  awslocal lambda delete-function --function-name "$FN" || true
done

awslocal iam delete-role-policy --role-name lambda-exec --policy-name lambda-inline || true
awslocal iam delete-role --role-name lambda-exec || true

awslocal dynamodb delete-table --table-name images || true
awslocal dynamodb delete-table --table-name image_tags || true

awslocal s3 rb s3://image-service-bucket --force || true

echo "Teardown complete"
