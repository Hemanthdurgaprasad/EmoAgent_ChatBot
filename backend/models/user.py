from beanie import Document
from pydantic import EmailStr
from datetime import datetime


class User(Document):
    email: EmailStr
    hashed_password: str
    name: str
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
