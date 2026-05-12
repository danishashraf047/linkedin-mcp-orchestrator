from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    custom_api_base_url: str = "http://localhost:8000"
    custom_api_timeout_seconds: float = 15
    custom_api_max_retries: int = 3

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_access_token: str = ""
    linkedin_person_urn: str = ""
    linkedin_api_version: str = "202506"

    storage_backend: str = "local"
    local_storage_dir: Path = Field(default=Path("storage/images"))
    public_base_url: str = "http://localhost:8000"

    content_history_path: Path = Field(default=Path("storage/content_history.json"))

    @property
    def linkedin_enabled(self) -> bool:
        return bool(self.linkedin_access_token and self.linkedin_person_urn)


@lru_cache
def get_settings() -> Settings:
    return Settings()
