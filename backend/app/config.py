from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://esg:changeme_in_production@db:5432/esg_advisor"
    JWT_SECRET: str = "changeme_random_secret_64chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24h

    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "anthropic/claude-sonnet-4-5-20250514"

    APP_URL: str = "http://localhost:3000"

    # Embeddings (Voyage AI)
    VOYAGE_API_KEY: str = ""

    # Speech-to-Text (Whisper via Replicate)
    REPLICATE_API_TOKEN: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
