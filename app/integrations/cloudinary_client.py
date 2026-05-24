import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.logging import logger

class CloudinaryClient:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )

    def upload_certificate(self, file_path_or_bytes, public_id: str):
        try:
            response = cloudinary.uploader.upload(
                file_path_or_bytes,
                public_id=f"certificates/{public_id}",
                resource_type="raw" # PDFs are treated as raw in Cloudinary for best compatibility
            )
            return response.get("secure_url")
        except Exception as e:
            logger.error("cloudinary_upload_failed", error=str(e))
            raise

cloudinary_client = CloudinaryClient()
