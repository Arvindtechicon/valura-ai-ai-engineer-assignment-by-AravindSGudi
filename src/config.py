from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    openai_api_key: str = "mock-key"
    model_dev: str = "gpt-4o-mini"
    model_eval: str = "gpt-4.1"
    active_model: str = "gpt-4o-mini"  # override in prod
    session_ttl_seconds: int = 3600
    request_timeout_seconds: int = 25

settings = Settings()
