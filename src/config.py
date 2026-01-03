from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram settings
    TELEGRAM_BOT_TOKEN: SecretStr = Field(..., description="Telegram bot API token")
    ALLOWED_USER_ID: int = Field(
        ..., description="Telegram user ID allowed to use the bot"
    )

    # OpenRouter/LLM settings
    OPENROUTER_API_KEY: SecretStr = Field(..., description="OpenRouter API key")
    MODEL_ID: str = Field(default="x-ai/grok-4.1-fast", description="LLM model ID")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # Data paths (output files in Quizlet Custom Import format .txt)
    ENGLISH_CSV_PATH: str = Field(default="data/english.txt")
    GERMAN_CSV_PATH: str = Field(default="data/german.txt")

    class Config:
        env_file = ".env"
