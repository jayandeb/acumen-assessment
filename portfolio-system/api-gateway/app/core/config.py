from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    PORTFOLIO_SERVICE_URL: str = "http://portfolio-service:8001"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8002"
    SERVICE_NAME: str = "api-gateway"

    class Config:
        env_file = ".env"


settings = Settings()
