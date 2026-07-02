"""Configuration for Leads Service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Leads service configuration loaded from environment."""

    SERVICE_NAME: str = "leads-service"
    SERVICE_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/abacus_db"
    DB_SCHEMA: str = "leads"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    # Redis
    REDIS_URL: str = "redis://redis:6379/12"

    # Email / SMTP
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@lynteron.app"
    SALES_EMAIL: str = "sales@lynteron.app"

    model_config = {"env_prefix": "LEADS_"}


settings = Settings()
