from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    SERVICE_NAME: str = "notification-service"

    class Config:
        env_file = ".env"


settings = Settings()
