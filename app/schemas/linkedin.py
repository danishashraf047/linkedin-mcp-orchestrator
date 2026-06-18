from typing import Literal

from pydantic import BaseModel, Field


class LinkedInPublishRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    image_path: str | None = None
    image_url: str | None = None
    saved_post_path: str | None = None
    visibility: str = "PUBLIC"
    post_as: Literal["personal", "company"] = "personal"
    require_image: bool = True
    require_saved_artifacts: bool = True
    approved: bool = False


class LinkedInPublishResult(BaseModel):
    post_id: str | None = None
    asset_urn: str | None = None
    post_as: str | None = None
    author: str | None = None
    status: str
    raw_response: dict = Field(default_factory=dict)
