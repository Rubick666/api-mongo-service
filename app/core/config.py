from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "catalog_db"

    # Use an environment variable in real deployments.
    secret_key: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )

    testing: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

if settings.testing:
    settings.mongo_db_name = "catalog_test_db"