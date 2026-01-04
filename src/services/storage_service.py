import uuid
from fastapi import UploadFile
from src.infra.aws import get_s3_client
from src.core.config import settings


class StorageService:
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME

    @property
    def s3(self):
        """Lazily initialize client to catch the active mock context."""
        return get_s3_client()

    async def upload_image(self, file: UploadFile) -> str:
        file_key = f"{uuid.uuid4()}-{file.filename}"
        self.s3.upload_fileobj(file.file, self.bucket, file_key)
        return file_key

    def delete_image(self, file_key: str):
        self.s3.delete_object(Bucket=self.bucket, Key=file_key)

    def get_download_url(self, file_key: str):
        # Generates a temporary URL for viewing/downloading
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": file_key},
            ExpiresIn=3600,
        )
