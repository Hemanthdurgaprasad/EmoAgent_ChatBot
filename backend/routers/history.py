from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from models.session import ChatSession
from core.security import get_current_user

router = APIRouter()


@router.get("/sessions")
async def get_sessions(current_user: User = Depends(get_current_user)):
    """Returns all sessions for the current user, newest first."""
    sessions = await ChatSession.find(
        ChatSession.user_id == str(current_user.id)
    ).sort(-ChatSession.updated_at).to_list()

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "message_count": len(s.messages),
            "updated_at": s.updated_at.isoformat(),
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Returns full message history for a session."""
    session = await ChatSession.get(session_id)
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "title": session.title,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in session.messages
        ],
        "created_at": session.created_at.isoformat(),
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    session = await ChatSession.get(session_id)
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    await session.delete()
