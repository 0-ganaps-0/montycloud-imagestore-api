from datetime import datetime
from src.infra.aws import get_dynamodb_resource
from src.core.config import settings
from boto3.dynamodb.conditions import Attr


class MetadataService:
    def __init__(self):
        self._db_resource = None 
        self.table_name = settings.DYNAMODB_TABLE_NAME

    @property
    def table(self):
        """Lazily initialize and return the DynamoDB Table object."""
        if self._db_resource is None:
            self._db_resource = get_dynamodb_resource()
        return self._db_resource.Table(self.table_name)

    def save_metadata(
        self, image_id: str, filename: str, content_type: str, tags: list
    ):
        item = {
            "ImageId": image_id,
            "Filename": filename,
            "ContentType": content_type,
            "Tags": tags,
            "UploadDate": datetime.utcnow().isoformat(),
        }
        self.table.put_item(Item=item)
        return item

    def list_images(self, tag_filter: str = None, name_filter: str = None):
        if not tag_filter and not name_filter:
            return self.table.scan().get("Items", [])

        # Supporting at least two filters
        filter_expr = None
        if tag_filter:
            filter_expr = Attr("Tags").contains(tag_filter)
        if name_filter:
            name_condition = Attr("Filename").contains(name_filter)
            filter_expr = (
                filter_expr & name_condition if filter_expr else name_condition
            )

        return self.table.scan(FilterExpression=filter_expr).get("Items", [])

    def delete_metadata(self, image_id: str):
        self.table.delete_item(Key={"ImageId": image_id})
