from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.api import CustomApiPostPayload
from app.schemas.content import FollowUpContext, GeneratedPost, GeneratedPostRequest
from app.schemas.linkedin import LinkedInPublishRequest
from app.services.content_engine import ContentEngine
from app.services.custom_api import CustomApiClient
from app.services.image_storage import ImageStorage
from app.linkedin.client import LinkedInClient
from app.utils.storage_artifacts import verify_approved_image_artifact, verify_saved_post_json

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
    if not payload.approved:
        raise HTTPException(status_code=400, detail="Approval is required before sending to the custom API.")
    if not payload.image_url:
        raise HTTPException(
            status_code=400,
            detail="Image URL is required. Upload the generated image first, then send the post package.",
        )
    if payload.require_saved_artifacts:
        try:
            verify_approved_image_artifact(payload.saved_post_path, payload.image_path, payload.image_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await CustomApiClient().send_post(payload)


@router.post("/images")
async def upload_image(file: UploadFile = File(...)) -> dict:
    try:
        return await ImageStorage().save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/linkedin/publish")
async def publish_to_linkedin(request: LinkedInPublishRequest) -> dict:
    if not request.approved:
        raise HTTPException(status_code=400, detail="Approval is required before publishing to LinkedIn.")
    if request.require_image and not request.image_path:
        raise HTTPException(
            status_code=400,
            detail="Image is required for publishing. Upload/save the image first, then pass image_path.",
        )
    if request.require_saved_artifacts:
        try:
            verify_saved_post_json(request.saved_post_path)
            if request.require_image:
                verify_approved_image_artifact(request.saved_post_path, request.image_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    client = LinkedInClient()
    if request.image_path:
        result = await client.publish_image_post(request.content, request.image_path, request.visibility)
    else:
        result = await client.publish_text_post(request.content, request.visibility)
    return result.model_dump()
