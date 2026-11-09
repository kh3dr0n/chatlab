from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"  # Ollama ignores it; real providers don't
    default_model: str = "llama3.2"
    llm_timeout_s: float = 120.0


settings = Settings()