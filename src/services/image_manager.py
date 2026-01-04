from src.services.storage_service import StorageService
from src.services.metadata_service import MetadataService


class ImageManager:
    def __init__(self):
        self.storage = StorageService()
        self.metadata = MetadataService()

    async def process_upload(self, file, tags):
        # 1. Upload to S3
        file_key = await self.storage.upload_image(file)
        # 2. Save to DynamoDB
        metadata = self.metadata.save_metadata(
            image_id=file_key,
            filename=file.filename,
            content_type=file.content_type,
            tags=tags,
        )
        return metadata

    def process_deletion(self, image_id: str):
        # Delete from both
        self.storage.delete_image(image_id)
        self.metadata.delete_metadata(image_id)
