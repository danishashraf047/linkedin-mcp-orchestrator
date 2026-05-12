import base64
import binascii
import mimetypes
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.linkedin.client import LinkedInClient
from app.schemas.api import CustomApiPostPayload, ToolResponse
from app.schemas.content import GeneratedPost, PostMetadata, QualityValidationResult
from app.schemas.linkedin import LinkedInPublishRequest
from app.services.content_engine import ContentEngine
from app.services.custom_api import CustomApiClient
from app.services.image_storage import ImageStorage
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _ok(message: str, **data: Any) -> dict[str, Any]:
    return ToolResponse(success=True, message=message, data=data).model_dump()


def _err(message: str, exc: Exception) -> dict[str, Any]:
    logger.exception("%s error=%s", message, exc)
    return ToolResponse(success=False, message=message, error=str(exc)).model_dump()


async def save_generated_post(post: dict[str, Any], filename: str | None = None) -> dict[str, Any]:
    """Persist a generated LinkedIn post as JSON in local storage."""
    try:
        validated = GeneratedPost(**post)
        storage_dir = Path("storage/posts")
        storage_dir.mkdir(parents=True, exist_ok=True)
        safe_name = filename or f"{validated.metadata.get('fingerprint', 'post')}.json"
        path = storage_dir / safe_name
        path.write_text(validated.model_dump_json(indent=2), encoding="utf-8")
        return _ok("Generated post saved", path=str(path), post=validated.model_dump())
    except (ValidationError, OSError) as exc:
        return _err("Failed to save generated post", exc)


async def upload_generated_image(image_base64: str, mime_type: str, original_name: str | None = None) -> dict[str, Any]:
    """Upload a generated image from base64 into the configured storage backend."""
    try:
        content = base64.b64decode(image_base64, validate=True)
        result = await ImageStorage().save_bytes(content, mime_type, original_name)
        return _ok("Image uploaded", image=result)
    except (binascii.Error, ValueError, OSError) as exc:
        return _err("Failed to upload generated image", exc)


async def upload_image_file(image_path: str, mime_type: str | None = None, original_name: str | None = None) -> dict[str, Any]:
    """Upload an existing generated image file from disk into the configured storage backend."""
    try:
        path = Path(image_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        detected_mime_type = mime_type or mimetypes.guess_type(path.name)[0]
        if not detected_mime_type:
            raise ValueError(f"Could not detect MIME type for image: {path}")

        result = await ImageStorage().save_bytes(path.read_bytes(), detected_mime_type, original_name or path.name)
        return _ok("Image file uploaded", image=result, source_path=str(path))
    except (ValueError, OSError) as exc:
        return _err("Failed to upload image file", exc)


async def publish_to_linkedin(content: str, image_path: str | None = None, visibility: str = "PUBLIC") -> dict[str, Any]:
    """Publish text or image content to LinkedIn through LinkedIn REST APIs."""
    try:
        request = LinkedInPublishRequest(content=content, image_path=image_path, visibility=visibility)
        client = LinkedInClient()
        if request.image_path:
            result = await client.publish_image_post(request.content, request.image_path, request.visibility)
        else:
            result = await client.publish_text_post(request.content, request.visibility)
        return _ok("LinkedIn post published", linkedin=result.model_dump())
    except Exception as exc:
        return _err("Failed to publish to LinkedIn", exc)


async def send_to_custom_api(payload: dict[str, Any]) -> dict[str, Any]:
    """Send generated content to the configured custom API POST /api/posts endpoint."""
    try:
        validated = CustomApiPostPayload(**payload)
        result = await CustomApiClient().send_post(validated)
        return _ok("Post sent to custom API", response=result)
    except Exception as exc:
        return _err("Failed to send to custom API", exc)


async def generate_post_metadata(post: dict[str, Any]) -> dict[str, Any]:
    """Generate structured metadata for a LinkedIn post."""
    try:
        validated = GeneratedPost(**post)
        metadata: PostMetadata = await ContentEngine().metadata(validated)
        return _ok("Post metadata generated", metadata=metadata.model_dump())
    except ValidationError as exc:
        return _err("Failed to generate post metadata", exc)


async def validate_post_quality(post: dict[str, Any]) -> dict[str, Any]:
    """Validate content quality, repetition risks, hashtag hygiene, and AI-style phrasing."""
    try:
        validated = GeneratedPost(**post)
        result: QualityValidationResult = await ContentEngine().validate_quality(validated)
        return _ok("Post quality validated", validation=result.model_dump())
    except ValidationError as exc:
        return _err("Failed to validate post quality", exc)

