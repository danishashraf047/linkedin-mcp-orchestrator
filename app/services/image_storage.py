import mimetypes
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.utils.image_validation import validate_image_bytes

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


class ImageStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_dir = self.settings.local_storage_dir

    async def save_upload(self, file: UploadFile) -> dict:
        content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported image MIME type: {content_type}")
        suffix = mimetypes.guess_extension(content_type) or Path(file.filename or "").suffix or ".png"
        filename = f"{uuid.uuid4().hex}{suffix}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        destination = self.base_dir / filename
        data = await file.read()
        validate_image_bytes(data, content_type)
        destination.write_bytes(data)
        return {
            "filename": filename,
            "path": str(destination),
            "mime_type": content_type,
            "size_bytes": len(data),
            "url": f"{self.settings.public_base_url.rstrip('/')}/images/{filename}",
            "storage_backend": self.settings.storage_backend,
        }

    async def save_bytes(self, content: bytes, mime_type: str, original_name: str | None = None) -> dict:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported image MIME type: {mime_type}")
        validate_image_bytes(content, mime_type)
        suffix = mimetypes.guess_extension(mime_type) or Path(original_name or "").suffix or ".png"
        filename = f"{uuid.uuid4().hex}{suffix}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        destination = self.base_dir / filename
        destination.write_bytes(content)
        return {
            "filename": filename,
            "path": str(destination),
            "mime_type": mime_type,
            "size_bytes": len(content),
            "url": f"{self.settings.public_base_url.rstrip('/')}/images/{filename}",
            "storage_backend": self.settings.storage_backend,
        }
