from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5256000
    API_KEY_WAPPI: str
    PROFILE_ID_WAPPI: str
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    REGISTRATION_SECRET_TOKEN: str

    class Config:
        env_file = ".env"

settings = Settings()