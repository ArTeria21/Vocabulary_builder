from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENROUTER_API_KEY: SecretStr = Field(..., env="OPENROUTER_API_KEY")
    MODEL_ID: str = Field(default="x-ai/grok-4.1-fast")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    class Config:
        env_file = ".env"