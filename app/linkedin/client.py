from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.schemas.linkedin import LinkedInPublishResult
from app.utils.logging import get_logger
from app.utils.retry import async_retry

logger = get_logger(__name__)


class LinkedInClient:
    base_url = "https://api.linkedin.com/rest"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        if not self.settings.linkedin_access_token:
            raise ValueError("LINKEDIN_ACCESS_TOKEN is required")
        return {
            "Authorization": f"Bearer {self.settings.linkedin_access_token}",
            "LinkedIn-Version": self.settings.linkedin_api_version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": content_type,
        }

    def _author(self) -> str:
        if not self.settings.linkedin_person_urn:
            raise ValueError("LINKEDIN_PERSON_URN is required")
        return self.settings.linkedin_person_urn

    async def validate_token(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.linkedin.com/v2/userinfo", headers=self._headers())
            response.raise_for_status()
            logger.info("linkedin_token_validated")
            return response.json()

    async def publish_text_post(self, content: str, visibility: str = "PUBLIC") -> LinkedInPublishResult:
        payload = {
            "author": self._author(),
            "commentary": content,
            "visibility": visibility,
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        result = await self._post_ugc(payload)
        return LinkedInPublishResult(post_id=result.get("id"), status="published", raw_response=result)

    async def publish_image_post(self, content: str, image_path: str, visibility: str = "PUBLIC") -> LinkedInPublishResult:
        asset_urn = await self.upload_image_asset(image_path)
        payload = {
            "author": self._author(),
            "commentary": content,
            "visibility": visibility,
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"id": asset_urn}},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        result = await self._post_ugc(payload)
        return LinkedInPublishResult(post_id=result.get("id"), asset_urn=asset_urn, status="published", raw_response=result)

    async def upload_image_asset(self, image_path: str) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        init_payload = {"initializeUploadRequest": {"owner": self._author()}}
        async with httpx.AsyncClient(timeout=30) as client:
            init_response = await client.post(
                f"{self.base_url}/images?action=initializeUpload",
                json=init_payload,
                headers=self._headers(),
            )
            init_response.raise_for_status()
            init_data = init_response.json()["value"]
            upload_url = init_data["uploadUrl"]
            image_urn = init_data["image"]
            upload_response = await client.put(
                upload_url,
                content=path.read_bytes(),
                headers={"Authorization": f"Bearer {self.settings.linkedin_access_token}", "Content-Type": "application/octet-stream"},
            )
            upload_response.raise_for_status()
            logger.info("linkedin_image_uploaded asset=%s", image_urn)
            return image_urn

    async def _post_ugc(self, payload: dict[str, Any]) -> dict[str, Any]:
        @async_retry(3)
        async def _send() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{self.base_url}/posts", json=payload, headers=self._headers())
                response.raise_for_status()
                logger.info("linkedin_post_published status=%s", response.status_code)
                if response.content:
                    return response.json()
                return {"id": response.headers.get("x-restli-id"), "status_code": response.status_code}

        return await _send()
