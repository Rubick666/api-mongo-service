from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    mongo_uri: str = Field("mongodb://localhost:27017", env="MONGO_URI")
    mongo_db_name: str = Field("catalog_db", env="MONGO_DB_NAME")
    secret_key: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()