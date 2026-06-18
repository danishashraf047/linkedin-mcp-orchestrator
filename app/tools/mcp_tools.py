import base64
import binascii
import hashlib
import mimetypes
import re
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
from app.utils.storage_artifacts import file_sha256, verify_approved_image_artifact, verify_saved_image, verify_saved_post_json

logger = get_logger(__name__)

GENERIC_POST_FILENAMES = {"post.json", "generated-post.json", "linkedin-post.json"}


def _ok(message: str, **data: Any) -> dict[str, Any]:
    return ToolResponse(success=True, message=message, data=data).model_dump()


def _err(message: str, exc: Exception) -> dict[str, Any]:
    logger.exception("%s error=%s", message, exc)
    return ToolResponse(success=False, message=message, error=str(exc)).model_dump()


def _post_filename(post: GeneratedPost, filename: str | None) -> str:
    requested = Path(filename).name if filename else ""
    if requested and requested.lower() not in GENERIC_POST_FILENAMES:
        return requested if requested.endswith(".json") else f"{requested}.json"

    slug = re.sub(r"[^a-z0-9]+", "-", post.title.lower()).strip("-") or "linkedin-post"
    slug = slug[:80].strip("-")
    fingerprint = (
        post.metadata.get("fingerprint")
        or post.metadata.get("style_fingerprint")
        or post.metadata.get("post_metadata", {}).get("style_fingerprint")
        or hashlib.sha256(post.content.encode("utf-8")).hexdigest()[:12]
    )
    return f"{slug}-{fingerprint}.json"


async def save_generated_post(
    post: dict[str, Any],
    filename: str | None = None,
    image_path: str | None = None,
    image_url: str | None = None,
    source_image_path: str | None = None,
    require_source_image: bool = True,
) -> dict[str, Any]:
    """Persist a generated LinkedIn post as JSON in local storage."""
    try:
        validated = GeneratedPost(**post)
        if image_path:
            stored_image_path = verify_saved_image(image_path)
            if require_source_image and not source_image_path:
                raise ValueError("Source image path is required to prove the stored image matches the generated image.")
            approved_image = {
                "path": str(stored_image_path),
                "url": image_url,
                "sha256": file_sha256(stored_image_path),
            }
            if source_image_path:
                source_path = Path(source_image_path).expanduser().resolve()
                if not source_path.exists() or not source_path.is_file():
                    raise FileNotFoundError(f"Source image not found: {source_image_path}")
                source_sha = file_sha256(source_path)
                if source_sha != approved_image["sha256"]:
                    raise ValueError("Stored image does not match the generated source image.")
                approved_image["source_path"] = str(source_path)
                approved_image["source_sha256"] = source_sha

            validated.metadata["approved_image"] = approved_image

        storage_dir = Path("storage/posts")
        storage_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _post_filename(validated, filename)
        path = storage_dir / safe_name
        path.write_text(validated.model_dump_json(indent=2), encoding="utf-8")
        return _ok("Generated post saved", path=str(path), post=validated.model_dump())
    except (ValidationError, ValueError, OSError) as exc:
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

        source_content = path.read_bytes()
        result = await ImageStorage().save_bytes(source_content, detected_mime_type, original_name or path.name)
        result["source_path"] = str(path)
        result["source_sha256"] = file_sha256(path)
        return _ok("Image file uploaded", image=result, source_path=str(path))
    except (ValueError, OSError) as exc:
        return _err("Failed to upload image file", exc)


async def publish_to_linkedin(
    content: str,
    image_path: str | None = None,
    saved_post_path: str | None = None,
    visibility: str = "PUBLIC",
    post_as: str = "personal",
    require_image: bool = True,
    require_saved_artifacts: bool = True,
    approved: bool = False,
) -> dict[str, Any]:
    """Publish text or image content to LinkedIn through LinkedIn REST APIs."""
    try:
        request = LinkedInPublishRequest(
            content=content,
            image_path=image_path,
            saved_post_path=saved_post_path,
            visibility=visibility,
            post_as=post_as,
            require_image=require_image,
            require_saved_artifacts=require_saved_artifacts,
            approved=approved,
        )
        if not request.approved:
            raise ValueError("Approval is required before publishing to LinkedIn.")
        if request.require_image and not request.image_path:
            raise ValueError("Image is required for publishing. Upload/save the image first, then pass image_path.")
        if request.require_saved_artifacts:
            verify_saved_post_json(request.saved_post_path)
            if request.require_image:
                verify_approved_image_artifact(request.saved_post_path, request.image_path)
        client = LinkedInClient()
        if request.image_path:
            result = await client.publish_image_post(request.content, request.image_path, request.visibility, request.post_as)
        else:
            result = await client.publish_text_post(request.content, request.visibility, request.post_as)
        return _ok("LinkedIn post published", linkedin=result.model_dump())
    except Exception as exc:
        return _err("Failed to publish to LinkedIn", exc)


async def send_to_custom_api(
    payload: dict[str, Any],
    saved_post_path: str | None = None,
    image_path: str | None = None,
    require_saved_artifacts: bool = True,
    approved: bool = False,
) -> dict[str, Any]:
    """Send generated content to the configured custom API POST /api/posts endpoint."""
    try:
        validated = CustomApiPostPayload(**payload)
        saved_post_path = saved_post_path or validated.saved_post_path
        image_path = image_path or validated.image_path
        approved = approved or validated.approved
        require_saved_artifacts = require_saved_artifacts and validated.require_saved_artifacts
        if not approved:
            raise ValueError("Approval is required before sending to the custom API.")
        if not validated.image_url:
            raise ValueError("Image URL is required. Upload the generated image first, then send the post package.")
        if require_saved_artifacts:
            verify_approved_image_artifact(saved_post_path, image_path, validated.image_url)
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
