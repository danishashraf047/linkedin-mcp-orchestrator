import os

from mcp.server.fastmcp import FastMCP

from app.tools.mcp_tools import (
    generate_post_metadata as generate_post_metadata_impl,
    publish_to_linkedin as publish_to_linkedin_impl,
    save_generated_post as save_generated_post_impl,
    send_to_custom_api as send_to_custom_api_impl,
    upload_generated_image as upload_generated_image_impl,
    upload_image_file as upload_image_file_impl,
    validate_post_quality as validate_post_quality_impl,
)
from app.utils.logging import configure_logging

configure_logging()

mcp = FastMCP(
    name="LinkedIn Content Automation",
    instructions=(
        "Generate varied LinkedIn content, validate quality, store generated images, "
        "send content to a custom API, and optionally publish through LinkedIn REST APIs."
    ),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def save_generated_post(
    post: dict,
    filename: str | None = None,
    image_path: str | None = None,
    image_url: str | None = None,
    source_image_path: str | None = None,
    require_source_image: bool = True,
) -> dict:
    """Persist a generated LinkedIn post as JSON in local storage with optional approved image metadata."""
    return await save_generated_post_impl(
        post,
        filename,
        image_path,
        image_url,
        source_image_path,
        require_source_image,
    )


@mcp.tool()
async def upload_generated_image(image_base64: str, mime_type: str, original_name: str | None = None) -> dict:
    """Upload a generated image from base64 into the configured storage backend."""
    return await upload_generated_image_impl(image_base64, mime_type, original_name)


@mcp.tool()
async def upload_image_file(image_path: str, mime_type: str | None = None, original_name: str | None = None) -> dict:
    """Upload an existing generated image file from disk into the configured storage backend."""
    return await upload_image_file_impl(image_path, mime_type, original_name)


@mcp.tool()
async def publish_to_linkedin(
    content: str,
    image_path: str | None = None,
    saved_post_path: str | None = None,
    visibility: str = "PUBLIC",
    post_as: str = "personal",
    require_image: bool = True,
    require_saved_artifacts: bool = True,
    approved: bool = False,
) -> dict:
    """Publish image content to LinkedIn by default; set require_image=false for text-only posts."""
    return await publish_to_linkedin_impl(
        content,
        image_path,
        saved_post_path,
        visibility,
        post_as,
        require_image,
        require_saved_artifacts,
        approved,
    )


@mcp.tool()
async def send_to_custom_api(
    payload: dict,
    saved_post_path: str | None = None,
    image_path: str | None = None,
    require_saved_artifacts: bool = True,
    approved: bool = False,
) -> dict:
    """Send generated content to the configured custom API POST /api/posts endpoint."""
    return await send_to_custom_api_impl(payload, saved_post_path, image_path, require_saved_artifacts, approved)


@mcp.tool()
async def generate_post_metadata(post: dict) -> dict:
    """Generate structured metadata for a LinkedIn post."""
    return await generate_post_metadata_impl(post)


@mcp.tool()
async def validate_post_quality(post: dict) -> dict:
    """Validate post quality and repetition risks."""
    return await validate_post_quality_impl(post)


def main() -> None:
    transport = os.getenv("LINKEDIN_MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(f"Unsupported LINKEDIN_MCP_TRANSPORT: {transport}")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
