from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.api import CustomApiPostPayload
from app.schemas.content import FollowUpContext, GeneratedPost, GeneratedPostRequest
from app.schemas.linkedin import LinkedInPublishRequest
from app.services.content_engine import ContentEngine
from app.services.custom_api import CustomApiClient
from app.services.image_storage import ImageStorage
from app.linkedin.client import LinkedInClient

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/content/follow-up-questions")
async def follow_up_questions(context: FollowUpContext) -> dict:
    questions = await ContentEngine().build_follow_up_questions(context)
    return {"questions": [question.model_dump() for question in questions]}


@router.post("/content/generate", response_model=GeneratedPost)
async def generate_content(request: GeneratedPostRequest) -> GeneratedPost:
    merged = request.model_dump()
    for key, value in request.answers.items():
        if key in merged and not merged[key]:
            merged[key] = value
    return await ContentEngine().generate(FollowUpContext(**merged))


@router.post("/posts")
async def receive_post(payload: CustomApiPostPayload) -> dict:
    return {"status": "stored", "post": payload.model_dump()}


@router.post("/integrations/custom-api")
async def send_to_custom_api(payload: CustomApiPostPayload) -> dict:
    return await CustomApiClient().send_post(payload)


@router.post("/images")
async def upload_image(file: UploadFile = File(...)) -> dict:
    try:
        return await ImageStorage().save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/linkedin/publish")
async def publish_to_linkedin(request: LinkedInPublishRequest) -> dict:
    client = LinkedInClient()
    if request.image_path:
        result = await client.publish_image_post(request.content, request.image_path, request.visibility)
    else:
        result = await client.publish_text_post(request.content, request.visibility)
    return result.model_dump()
