from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.user import User
from models.session import ChatSession
from routers import auth, chat, history
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGO_URI)
    await init_beanie(
        database=client[settings.DB_NAME],
        document_models=[User, ChatSession]
    )
    print("✅ Connected to MongoDB")
    yield
    # Shutdown
    client.close()


app = FastAPI(
    title="EmoAgent API",
    description="AI-powered empathetic mental health chatbot",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(history.router, prefix="/api/history", tags=["history"])


@app.get("/")
async def root():
    return {"status": "EmoAgent running", "version": "1.0.0"}
