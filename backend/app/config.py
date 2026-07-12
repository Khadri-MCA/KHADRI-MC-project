
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = "dummy-key-replace-me"
    groq_primary_model: str = "gemma2-9b-it"
    groq_context_model: str = "llama-3.3-70b-versatile"

    database_url: str = "sqlite:///./crm_hcp.db"

    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()

print("API KEY:", settings.groq_api_key[:10] + "...")
print("MODEL:", settings.groq_primary_model)
