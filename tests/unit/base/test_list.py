
import os
import json
from moto import mock_aws
import boto3

from src.handlers import list_handler, upload_handler

@mock_aws
def test_list_by_user_and_tag():
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['IMAGES_TABLE_NAME'] = 'images'
    os.environ['IMAGE_TAGS_TABLE_NAME'] = 'image_tags'
    boto3.client('s3', region_name='us-east-1').create_bucket(Bucket='test-bucket')
    ddb = boto3.client('dynamodb', region_name='us-east-1')

    # upload two images
    for t in (["demo","sunset"],["demo"]):
        event = {'body': json.dumps({'user_id':'u1','title':'x','tags':t,'content_type':'image/png','image_base64':'MTIz'})}
        upload_handler.handler(event, None)

    resp = list_handler.handler({'queryStringParameters': {'user_id':'u1'}}, None)
    assert resp['statusCode'] == 200
    assert len(json.loads(resp['body'])['items']) == 2

    resp2 = list_handler.handler({'queryStringParameters': {'tag':'sunset'}}, None)
    assert resp2['statusCode'] == 200
    assert len(json.loads(resp2['body'])['items']) == 1

    resp3 = list_handler.handler({'queryStringParameters': {'user_id':'u1','tag':'demo'}}, None)
    assert resp3['statusCode'] == 200
    assert len(json.loads(resp3['body'])['items']) == 2
