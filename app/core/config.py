from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "corporate_sales"
    api_base_path: str = "/corporate-sales/v1"


settings = Settings()
