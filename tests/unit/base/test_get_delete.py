
import os, json, base64
from moto import mock_aws
import boto3

from src.handlers import upload_handler, get_handler, delete_handler

@mock_aws
def test_get_and_delete():
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['S3_BUCKET_NAME'] = 'test-bucket'
    os.environ['IMAGES_TABLE_NAME'] = 'images'
    os.environ['IMAGE_TAGS_TABLE_NAME'] = 'image_tags'
    boto3.client('s3', region_name='us-east-1').create_bucket(Bucket='test-bucket')
    ddb = boto3.client('dynamodb', region_name='us-east-1')

    ev = {'body': json.dumps({'user_id':'u1','title':'x','tags':['demo'],'content_type':'image/png','image_base64': base64.b64encode(b'xyz').decode()})}
    up = upload_handler.handler(ev, None)
    print("UPLOAD BODY:", up["body"])    # <-- temporary debug
    iid = json.loads(up['body'])['image_id']

    # get metadata
    r = get_handler.handler({'pathParameters': {'image_id': iid}, 'rawPath': f'/images/{iid}'}, None)
    assert r['statusCode'] == 200
    assert json.loads(r['body'])['image_id'] == iid

    # get download url
    r2 = get_handler.handler({'pathParameters': {'image_id': iid}, 'rawPath': f'/images/{iid}/download'}, None)
    assert r2['statusCode'] == 200
    assert 'url' in json.loads(r2['body'])

    # delete
    d = delete_handler.handler({'pathParameters': {'image_id': iid}, 'rawPath': f'/images/{iid}'}, None)
    assert d['statusCode'] == 204
