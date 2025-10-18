"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Evolution API
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str
    EVOLUTION_INSTANCE_NAME: str = "neo-chat"
    EVOLUTION_TIMEOUT: int = 10

    # Google Cloud
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_TIMEOUT: int = 30

    # PostgreSQL Database with pgvector
    DATABASE_URL: str
    DATABASE_TIMEOUT: int = 5

    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE_MB: int = 16
    MAX_CONCURRENT_USERS: int = 100

    # Rate Limiting
    GEMINI_RATE_LIMIT_PER_MIN: int = 60
    WHATSAPP_RATE_LIMIT_PER_MIN: int = 60

    # Retry
    MAX_RETRIES: int = 5
    RETRY_BACKOFF_BASE: int = 1

    # Vector Search
    VECTOR_SIMILARITY_THRESHOLD: float = 0.7
    VECTOR_TOP_K: int = 5
    MAX_CONTEXT_TOKENS: int = 8000

    # Chunking
    MIN_CHUNK_TOKENS: int = 100
    MAX_CHUNK_TOKENS: int = 2000

    # Web Crawling
    MAX_CRAWL_PAGES: int = 100
    CRAWL_TIMEOUT_MINUTES: int = 5
    CRAWL_RATE_LIMIT_SECONDS: int = 1


# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance.
    
    Returns:
        Settings instance
    """
    return settings
