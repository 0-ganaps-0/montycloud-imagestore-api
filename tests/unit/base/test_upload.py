
import os
import json
import base64
from moto import mock_aws
import boto3

from src.handlers import upload_handler

@mock_aws
def test_upload_success():
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['IMAGES_TABLE_NAME'] = 'images'
    os.environ['IMAGE_TAGS_TABLE_NAME'] = 'image_tags'

    s3 = boto3.client('s3', region_name='us-east-1')
    ddb = boto3.client('dynamodb', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')

    payload = {
        'user_id': 'u1',
        'title': 't1',
        'description': 'd',
        'tags': ['demo','Test'],
        'content_type': 'image/png',
        'image_base64': base64.b64encode(b'1234').decode()
    }
    event = {'body': json.dumps(payload)}
    resp = upload_handler.handler(event, None)
    print("UPLOAD BODY:", resp["body"])  # <-- temporary debug
    assert resp['statusCode'] == 201
    body = json.loads(resp['body'])
    assert body['user_id'] == 'u1'
    assert body['tags'] == ['demo','test']
    assert body['size'] == 4

@mock_aws
def test_upload_missing_fields():
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['IMAGES_TABLE_NAME'] = 'images'
    os.environ['IMAGE_TAGS_TABLE_NAME'] = 'image_tags'
    boto3.client('s3', region_name='us-east-1').create_bucket(Bucket='test-bucket')
    event = {'body': json.dumps({'user_id':'x'})}
    resp = upload_handler.handler(event, None)
    assert resp['statusCode'] == 400
