from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "emoagent"

    SECRET_KEY: str = "9f3c8e2a7b4d6f1c5e8a9b0d3c2f7a6e4b1c9d8e7f6a5b4c3d2e1f0a9b8c7d6"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    AI_PROVIDER: str = "mock"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Gemini — add later
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Mistral — add after fine-tuning
    MODEL_PATH: str = "./adapter"
    MISTRAL_BASE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    class Config:
        env_file = ".env"

settings = Settings()