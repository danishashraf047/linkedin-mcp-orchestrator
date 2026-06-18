from typing import Any

from pydantic import BaseModel, Field


class CustomApiPostPayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    content: str = Field(..., min_length=1, max_length=3000)
    hashtags: list[str] = Field(default_factory=list)
    image_url: str = ""
    image_prompt: str = ""
    image_path: str | None = Field(default=None, exclude=True)
    saved_post_path: str | None = Field(default=None, exclude=True)
    approved: bool = Field(default=False, exclude=True)
    require_saved_artifacts: bool = Field(default=True, exclude=True)
    platform: str = "linkedin"
    author: str = ""
    tone: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
