from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from bson import ObjectId


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(Document):
    user_id: str
    title: str = "New conversation"
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_sessions"
