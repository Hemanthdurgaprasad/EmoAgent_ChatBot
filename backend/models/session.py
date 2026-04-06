from beanie import Document
from pydantic import BaseModel
from datetime import datetime
from typing import Literal
from bson import ObjectId


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = datetime.utcnow()


class ChatSession(Document):
    user_id: str
    title: str = "New conversation"
    messages: list[Message] = []
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "chat_sessions"
