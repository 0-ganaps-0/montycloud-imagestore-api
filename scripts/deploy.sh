
#!/usr/bin/env bash
set -euo pipefail

REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=000000000000
BUCKET=image-service-bucket
IMAGES_TABLE=images
TAGS_TABLE=image_tags
API_NAME=images-api
STAGE=dev

export AWS_DEFAULT_REGION=${REGION}

if ! command -v awslocal >/dev/null 2>&1; then
  echo "awslocal not found. Install with: pip install awscli-local" && exit 1
fi

# --- S3 bucket ---
## awslocal s3api create-bucket --bucket ${BUCKET} --create-bucket-configuration LocationConstraint=${REGION} || true
awslocal s3api create-bucket --bucket ${BUCKET} || true
# --- DynamoDB tables ---
awslocal dynamodb create-table \
  --table-name ${IMAGES_TABLE} \
  --attribute-definitions \
    AttributeName=image_id,AttributeType=S \
    AttributeName=user_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=image_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes 'IndexName=user_id-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}' || true

awslocal dynamodb create-table \
  --table-name ${TAGS_TABLE} \
  --attribute-definitions \
    AttributeName=tag,AttributeType=S \
    AttributeName=image_id,AttributeType=S \
  --key-schema AttributeName=tag,KeyType=HASH AttributeName=image_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST || true

# --- IAM role & inline policy for Lambda ---
ROLE_NAME=lambda-exec
TRUST_POLICY='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
awslocal iam create-role --role-name ${ROLE_NAME} --assume-role-policy-document "${TRUST_POLICY}" || true

POLICY_DOC='{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"},
    {"Effect":"Allow","Action":["dynamodb:*"],"Resource":"*"},
    {"Effect":"Allow","Action":["s3:*"],"Resource":"*"}
  ]
}'
awslocal iam put-role-policy --role-name ${ROLE_NAME} --policy-name lambda-inline --policy-document "${POLICY_DOC}" || true

# --- Build lambda zip (if not already) ---
[ -f lambda.zip ] || (cd src && zip -r ../lambda.zip . >/dev/null)

# --- Create Lambda functions ---
create_lambda() {
  local NAME=$1 HANDLER=$2
  awslocal lambda create-function \
    --function-name ${NAME} \
    --runtime python3.9 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME} \
    --handler ${HANDLER} \
    --zip-file fileb://lambda.zip \
    --timeout 30 \
    --environment "Variables={S3_BUCKET_NAME=${BUCKET},IMAGES_TABLE_NAME=${IMAGES_TABLE},IMAGE_TAGS_TABLE_NAME=${TAGS_TABLE},AWS_REGION=${REGION},AWS_ENDPOINT_URL=http://localstack:4566}" || true
}
create_lambda images-upload handlers.upload_handler.handler
create_lambda images-list   handlers.list_handler.handler
create_lambda images-get    handlers.get_handler.handler
create_lambda images-delete handlers.delete_handler.handler

# --- API Gateway v1 (REST API) ---
API_ID=$(awslocal apigateway create-rest-api --name ${API_NAME} --query 'id' --output text || true)
if [ -z "${API_ID}" ]; then
  API_ID=$(awslocal apigateway get-rest-apis --query "items[?name=='${API_NAME}'].id" --output text || true)
fi
echo "API_ID=${API_ID}"

# Root resource
ROOT_ID=$(awslocal apigateway get-resources --rest-api-id ${API_ID} --query "items[?path=='/'].id" --output text)

# Create resource tree: /images, /images/{image_id}, /images/{image_id}/download
IMAGES_ID=$(awslocal apigateway create-resource --rest-api-id ${API_ID} --parent-id ${ROOT_ID} --path-part images --query 'id' --output text || \
            awslocal apigateway get-resources --rest-api-id ${API_ID} --query "items[?path=='/images'].id" --output text)

IMAGE_ID_RES=$(awslocal apigateway create-resource --rest-api-id ${API_ID} --parent-id ${IMAGES_ID} --path-part "{image_id}" --query 'id' --output text || \
               awslocal apigateway get-resources --rest-api-id ${API_ID} --query "items[?path=='/images/{image_id}'].id" --output text)

DOWNLOAD_ID=$(awslocal apigateway create-resource --rest-api-id ${API_ID} --parent-id ${IMAGE_ID_RES} --path-part "download" --query 'id' --output text || \
              awslocal apigateway get-resources --rest-api-id ${API_ID} --query "items[?path=='/images/{image_id}/download'].id" --output text)

# --- Lambda proxy integration helper (Option A: unique statement-ids per route) ---
# Args:
#   $1 = RESOURCE_ID
#   $2 = METHOD (GET/POST/DELETE/etc.)
#   $3 = FUNCTION_NAME
#   $4 = SID_SUFFIX (unique identifier per route)
#   $5 = SOURCE_PATH (path to scope the permission, e.g., '/*', '/images/*', '/images/*/download')
put_lambda_proxy() {
  local RESOURCE_ID=$1 METHOD=$2 FUNCTION_NAME=$3 SID_SUFFIX=$4 SOURCE_PATH=$5
  local FN_ARN=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}

  # Method
  awslocal apigateway put-method \
    --rest-api-id ${API_ID} --resource-id ${RESOURCE_ID} \
    --http-method ${METHOD} --authorization-type NONE >/dev/null

  # Integration (Lambda proxy)
  awslocal apigateway put-integration \
    --rest-api-id ${API_ID} --resource-id ${RESOURCE_ID} \
    --http-method ${METHOD} \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${FN_ARN}/invocations >/dev/null

  # Permission with UNIQUE statement-id and PATH-SCOPED source ARN
  awslocal lambda add-permission \
    --function-name ${FUNCTION_NAME} \
    --statement-id ${FUNCTION_NAME}-${METHOD}-${SID_SUFFIX} \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/${METHOD}${SOURCE_PATH} || true
}

# --- Routes with unique statement IDs and path-scoped source ARNs ---
# POST /images -> images-upload
put_lambda_proxy ${IMAGES_ID}     POST   images-upload  "post-images"           "/*"

# GET /images -> images-list (query by user_id/tag)
put_lambda_proxy ${IMAGES_ID}     GET    images-list    "get-images-list"       "/*"

# GET /images/{image_id} -> images-get (metadata)
put_lambda_proxy ${IMAGE_ID_RES}  GET    images-get     "get-images-metadata"   "/images/*"

# GET /images/{image_id}/download -> images-get (presigned URL)
put_lambda_proxy ${DOWNLOAD_ID}   GET    images-get     "get-images-download"   "/images/*/download"

# DELETE /images/{image_id} -> images-delete
put_lambda_proxy ${IMAGE_ID_RES}  DELETE images-delete  "delete-images"         "/*"

# --- Deploy & stage ---
awslocal apigateway create-deployment --rest-api-id ${API_ID} --stage-name ${STAGE} >/dev/null || true

echo "REST API deployed. Invoke base: http://localhost:4566/restapis/${API_ID}/${STAGE}/_user_request_"
