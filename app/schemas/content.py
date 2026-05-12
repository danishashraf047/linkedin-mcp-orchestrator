from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PostStyle(StrEnum):
    founder_story = "founder story"
    controversial_opinion = "controversial opinion"
    educational = "educational"
    technical_breakdown = "technical breakdown"
    motivational = "motivational"
    case_study = "case study"
    personal_lesson = "personal lesson"
    saas_growth = "SaaS growth"
    ai_automation = "AI automation"
    startup_insights = "startup insights"
    engineering_leadership = "engineering leadership"
    developer_productivity = "developer productivity"


class FollowUpContext(BaseModel):
    topic: str = Field(..., min_length=3)
    target_audience: str | None = None
    tone: str | None = None
    topic_depth: str | None = None
    platform_goal: str | None = None
    desired_emotional_impact: str | None = None
    image_style: str | None = None
    branding_preference: str | None = None
    cta_preference: str | None = None
    author: str | None = None
    preferred_style: PostStyle | None = None


class FollowUpQuestion(BaseModel):
    key: str
    question: str
    reason: str
    required: bool = True


class GeneratedPostRequest(FollowUpContext):
    answers: dict[str, str] = Field(default_factory=dict)


class GeneratedPost(BaseModel):
    title: str = Field(..., min_length=4, max_length=140)
    content: str = Field(..., min_length=40, max_length=3000)
    hashtags: list[str] = Field(default_factory=list, max_length=12)
    image_prompt: str = Field(..., min_length=10, max_length=1200)
    style: str
    tone: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("hashtags")
    @classmethod
    def normalize_hashtags(cls, value: list[str]) -> list[str]:
        normalized = []
        for tag in value:
            clean = tag.strip().replace(" ", "")
            if not clean:
                continue
            normalized.append(clean if clean.startswith("#") else f"#{clean}")
        return list(dict.fromkeys(normalized))


class QualityValidationResult(BaseModel):
    passed: bool
    score: float = Field(..., ge=0, le=1)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PostMetadata(BaseModel):
    estimated_read_time_seconds: int
    character_count: int
    hashtag_count: int
    detected_structure: str
    style_fingerprint: str
    content_warnings: list[str] = Field(default_factory=list)
