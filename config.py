"""Configuration management for HN Agent."""
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # Provider switch: "openai" or "hf_inference"
    MODEL_PROVIDER: str = "openai"

    # API Keys
    HF_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Model Configuration
    MODEL_ID: str = "gpt-4o-mini"
    MAX_AGENT_STEPS: int = 6

    # HN Configuration
    DEFAULT_THREAD_COUNT: int = 5
    MAX_THREAD_COUNT: int = 10
    MAX_COMMENTS_PER_THREAD: int = 5

    # Cache Configuration
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # UI Configuration
    GRADIO_PORT: int = 7860
    GRADIO_SHARE: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
