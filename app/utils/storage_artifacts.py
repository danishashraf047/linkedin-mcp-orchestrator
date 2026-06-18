import hashlib
import json
from pathlib import Path

from app.config import get_settings


def verify_saved_post_json(path: str | None) -> Path:
    return _verify_storage_file(path, Path("storage/posts"), "Saved post JSON", ".json")


def verify_saved_image(path: str | None) -> Path:
    return _verify_storage_file(path, get_settings().local_storage_dir, "Saved image")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_approved_image_artifact(
    saved_post_path: str | None,
    image_path: str | None,
    image_url: str | None = None,
) -> dict:
    post_path = verify_saved_post_json(saved_post_path)
    stored_image_path = verify_saved_image(image_path)
    post = json.loads(post_path.read_text(encoding="utf-8"))
    artifact = post.get("metadata", {}).get("approved_image")
    if not isinstance(artifact, dict):
        raise ValueError("Saved post JSON does not include metadata.approved_image.")

    artifact_path = Path(str(artifact.get("path", ""))).expanduser().resolve()
    if artifact_path != stored_image_path:
        raise ValueError("Image path does not match the approved image recorded in the saved post JSON.")

    artifact_sha = artifact.get("sha256")
    if not artifact_sha:
        raise ValueError("Saved post JSON approved image is missing sha256.")
    if artifact_sha != file_sha256(stored_image_path):
        raise ValueError("Image file hash does not match the approved image recorded in the saved post JSON.")

    artifact_url = artifact.get("url")
    if image_url is not None and artifact_url != image_url:
        raise ValueError("Image URL does not match the approved image recorded in the saved post JSON.")

    return artifact


def _verify_storage_file(path: str | None, storage_dir: Path, label: str, suffix: str | None = None) -> Path:
    if not path:
        raise ValueError(f"{label} path is required.")

    storage_root = storage_dir.expanduser().resolve()
    candidate = Path(path).expanduser().resolve()

    if not candidate.is_relative_to(storage_root):
        raise ValueError(f"{label} must be stored under {storage_root}.")
    if not candidate.exists() or not candidate.is_file():
        raise ValueError(f"{label} not found: {path}")
    if suffix and candidate.suffix.lower() != suffix:
        raise ValueError(f"{label} must be a {suffix} file.")

    return candidate
