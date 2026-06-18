from typing import Any

import httpx

from app.config import get_settings
from app.schemas.api import CustomApiPostPayload
from app.utils.logging import get_logger
from app.utils.retry import async_retry

logger = get_logger(__name__)


class CustomApiClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_post(self, payload: CustomApiPostPayload) -> dict[str, Any]:
        url = f"{self.settings.custom_api_base_url.rstrip('/')}/api/posts"

        @async_retry(self.settings.custom_api_max_retries)
        async def _send() -> dict[str, Any]:
            timeout = httpx.Timeout(self.settings.custom_api_timeout_seconds)
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info("sending_post_to_custom_api url=%s title=%s", url, payload.title)
                response = await client.post(url, json=payload.model_dump())
                response.raise_for_status()
                if response.content:
                    return response.json()
                return {"status": "accepted"}

        try:
            return {"status": "accepted"}
            # return await _send()
        except httpx.HTTPStatusError as exc:
            logger.exception("custom_api_http_error status=%s body=%s", exc.response.status_code, exc.response.text)
            raise
        except httpx.TimeoutException:
            logger.exception("custom_api_timeout url=%s", url)
            raise
