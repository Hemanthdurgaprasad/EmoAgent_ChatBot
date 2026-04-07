from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import json

from models.user import User
from models.session import ChatSession, Message
from core.security import get_current_user
from core.ai_provider import stream_response
from middleware.safety import check_for_crisis, get_crisis_level, prepend_safety_message

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


async def _get_user_session(session_id: str, user_id: str):
    try:
        session = await ChatSession.get(session_id)
    except Exception:
        return None
    if not session or session.user_id != user_id:
        return None
    return session


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    # Load or create session
    if body.session_id:
        session = await _get_user_session(body.session_id, str(current_user.id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=str(current_user.id))
        await session.insert()

    # Multi-layer crisis detection
    crisis_detected = check_for_crisis(body.message)
    crisis_level    = get_crisis_level(body.message)

    if crisis_detected:
        print(f"[CRISIS DETECTED] level={crisis_level} user={str(current_user.id)[:8]}...")

    # Build history for context (last 10 messages)
    history = [
        {"role": m.role, "content": m.content}
        for m in session.messages[-10:]
    ]

    # Save user message immediately
    user_msg = Message(role="user", content=body.message)
    session.messages.append(user_msg)

    # Auto-title session from first message
    if len(session.messages) == 1:
        session.title = body.message[:50] + ("…" if len(body.message) > 50 else "")

    session.updated_at = datetime.utcnow()
    await session.save()

    async def generate():
        full_response = ""

        # Send session_id first so frontend can track it
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': str(session.id)})}\n\n"

        # Inject safety message if crisis detected — stream char by char
        if crisis_detected:
            safety_prefix = prepend_safety_message("")
            for char in safety_prefix:
                yield f"data: {json.dumps({'type': 'token', 'token': char})}\n\n"
            full_response += safety_prefix

            # Also send a crisis metadata event so frontend can optionally
            # highlight the message or show a special UI banner
            yield f"data: {json.dumps({'type': 'crisis', 'level': crisis_level})}\n\n"

        # Stream AI tokens
        try:
            async for token in stream_response(history, body.message):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # Save full conversation turn to MongoDB
        try:
            assistant_msg = Message(role="assistant", content=full_response)
            session.messages.append(assistant_msg)
            session.updated_at = datetime.utcnow()
            await session.save()
        except Exception as e:
            print(f"Session save error: {e}")

        # Signal completion with crisis level included
        yield f"data: {json.dumps({'type': 'done', 'session_id': str(session.id), 'crisis_level': crisis_level})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )