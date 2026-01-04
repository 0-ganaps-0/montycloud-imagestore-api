from fastapi import FastAPI
from src.api.image_routes import router as image_router
from src.core.config import settings

# Auto-generate OpenAPI schema at /docs
app = FastAPI(
    title="Acme ImageStore API",
    version="1.0.0",
    description="Production-grade API for image management with S3 and DynamoDB",
)

# Include the image routes
app.include_router(image_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "environment": settings.AWS_ENDPOINT_URL or "production",
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
