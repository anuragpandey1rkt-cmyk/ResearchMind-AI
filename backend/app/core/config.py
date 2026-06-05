from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResearchMind"
    environment: str = "development"
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = "llama-3.1-70b-versatile"
    groq_timeout_seconds: int = 60
    groq_max_retries: int = 3

    database_url: str = Field(
        default="sqlite+aiosqlite:///./researchmind.db",
        validation_alias="DATABASE_URL",
    )
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    chroma_path: str = "./chroma"
    upload_dir: str = "./storage/uploads"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    rate_limit_per_minute: int = 30
    max_upload_mb: int = 25
    chunk_size: int = 900
    chunk_overlap: int = 140
    default_top_k: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
