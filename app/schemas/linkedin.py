from pydantic import BaseModel, Field


class LinkedInPublishRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    image_path: str | None = None
    image_url: str | None = None
    visibility: str = "PUBLIC"


class LinkedInPublishResult(BaseModel):
    post_id: str | None = None
    asset_urn: str | None = None
    status: str
    raw_response: dict = Field(default_factory=dict)
