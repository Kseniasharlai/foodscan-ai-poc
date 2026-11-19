from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FoodScan AI — Аналізатор складу харчових продуктів"
    app_version: str = "1.0.0"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    openfoodfacts_base_url: str = "https://world.openfoodfacts.org/api/v2/product"
    request_timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
