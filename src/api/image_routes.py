import json
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from src.services.image_manager import ImageManager

router = APIRouter(prefix="/images", tags=["Images"])

def get_manager():
    return ImageManager()


@router.post("/upload", status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    tags: str = Form(
        ..., description='JSON string of tags, e.g., \'["vacation", "nature"]\''
    ),
    manager: ImageManager = Depends(get_manager)
):
    """1. Uploading image with metadata"""
    try:
        tag_list = json.loads(tags)
        if not isinstance(tag_list, list):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Tags must be a valid JSON list")

    metadata = await manager.process_upload(file, tag_list)
    return {"message": "Upload successful", "data": metadata}


@router.get("/",response_model=List[dict])
async def list_images(
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    name: Optional[str] = Query(None, description="Filter by filename"),
    manager: ImageManager = Depends(get_manager)
):
    """2. List all images, support at least two filters to search"""
    return manager.metadata.list_images(tag_filter=tag, name_filter=name)


@router.get("/{image_id}")
async def get_image_url(image_id: str, manager:ImageManager = Depends(get_manager)):
    """3. View/download image (Generates a secure presigned URL)"""
    # Verify metadata exists first
    images = manager.metadata.list_images()
    if not any(img["ImageId"] == image_id for img in images):
        raise HTTPException(status_code=404, detail="Image not found")

    url = manager.storage.get_download_url(image_id)
    return {"image_id": image_id, "download_url": url}


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: str, manager: ImageManager = Depends(get_manager)):
    """4. Delete an image"""
    try:
        manager.process_deletion(image_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
