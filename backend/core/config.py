from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "emoagent"

    SECRET_KEY: str = "change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    AI_PROVIDER: str = "mock"

    # Gemini — add later
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Mistral — add after fine-tuning
    MODEL_PATH: str = "./adapter"
    MISTRAL_BASE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    class Config:
        env_file = ".env"

settings = Settings()