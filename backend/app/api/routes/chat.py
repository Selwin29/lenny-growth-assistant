"""Chat session and message endpoints.

Covers session lifecycle (create/list/get/update/delete) and posting
messages into a session. Message persistence only — no LLM/agent
response generation yet (that arrives in a later milestone).
"""

import logging
import uuid

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.chat_session import (
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
    ChatSessionUpdate,
)
from app.schemas.message import MessageCreate, MessageRead
from app.services import chat_session_service, message_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post(
    "/new",
    response_model=ChatSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_chat_session(
    payload: ChatSessionCreate = ChatSessionCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionRead:
    """Start a new chat session for the current user."""
    chat_session = chat_session_service.create_chat_session(db, current_user.id, payload)
    return ChatSessionRead.model_validate(chat_session)


@router.get(
    "",
    response_model=list[ChatSessionRead],
    summary="List chat sessions",
)
async def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionRead]:
    """List all chat sessions belonging to the current user, most recent first."""
    sessions = chat_session_service.list_chat_sessions(db, current_user.id)
    return [ChatSessionRead.model_validate(s) for s in sessions]


@router.get(
    "/{session_id}",
    response_model=ChatSessionDetail,
    summary="Get a chat session with its messages",
)
async def get_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionDetail:
    """Fetch a single chat session, including its full message history."""
    chat_session = chat_session_service.get_chat_session(db, session_id, with_messages=True)
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this chat session",
        )
    return ChatSessionDetail.model_validate(chat_session)


@router.patch(
    "/{session_id}",
    response_model=ChatSessionRead,
    summary="Update a chat session",
)
async def update_chat_session(
    session_id: uuid.UUID,
    payload: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionRead:
    """Partially update a chat session (e.g. rename it)."""
    chat_session = chat_session_service.get_chat_session(db, session_id)
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this chat session",
        )
    chat_session = chat_session_service.update_chat_session(db, session_id, payload)
    return ChatSessionRead.model_validate(chat_session)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session",
)
async def delete_chat_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a chat session and all of its messages/artifacts."""
    chat_session = chat_session_service.get_chat_session(db, session_id)
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this chat session",
        )
    chat_session_service.delete_chat_session(db, session_id)


from app.agents.router import AgentRouter
from app.schemas.artifact import ArtifactCreate
from app.services import artifact_service

@router.post(
    "/{session_id}/message",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post a message to a chat session",
)
async def create_message(
    session_id: uuid.UUID,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageRead:
    """Persist a user message, run the agent routing layer to generate a grounded response,
    persist the assistant response and any optional artifacts, and return the user message.
    """
    chat_session = chat_session_service.get_chat_session(db, session_id)
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this chat session",
        )
        
    # 1. Validate provider against allowlist if provided
    ALLOWED_PROVIDERS = {"ollama", "gemini", "anthropic"}
    if payload.provider:
        clean_provider = payload.provider.strip().lower()
        if clean_provider not in ALLOWED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: '{payload.provider}'. Allowed providers: {', '.join(sorted(ALLOWED_PROVIDERS))}",
            )

    # 2. Create and persist user message
    user_message = message_service.create_message(db, session_id, payload)
    
    # 3. Retrieve session history context — trimmed to last 2 messages (1 exchange)
    #    for token efficiency. Full history is always persisted in the DB.
    history_messages = message_service.list_messages(db, session_id)
    context = [{"role": msg.role.value, "content": msg.content} for msg in history_messages]
    context = context[-2:]  # keep only the most recent 1 exchange
    
    # 4. Route and execute Agent logic
    try:
        router_instance = AgentRouter()
        agent_res = await router_instance.route_and_execute(
            payload.content, context, mode=payload.mode, provider=payload.provider
        )
        
        # 5. Save Assistant message
        assistant_payload = MessageCreate(
            content=agent_res["content"],
            role="assistant"
        )
        assistant_message = message_service.create_message(db, session_id, assistant_payload)
        
        # 6. Save Artifact if generated
        if "artifact" in agent_res and agent_res["artifact"]:
            art_data = agent_res["artifact"]
            art_payload = ArtifactCreate(
                title=art_data["title"],
                artifact_type=art_data["artifact_type"],
                content=art_data["content"]
            )
            artifact_service.create_artifact(db, assistant_message.id, art_payload)
            
    except Exception as e:
        logger.error(f"Failed to generate assistant response: {e}", exc_info=True)
        # Clean user-facing error message without exposing secrets or stack traces
        err_msg = str(e)
        if "API key" in err_msg or "unauthorized" in err_msg.lower() or "configured" in err_msg.lower():
            p_label = payload.provider.capitalize() if payload.provider else "LLM"
            user_err_text = f"{p_label} API key is not configured or invalid. Please check your backend/.env settings."
        elif "rate limit" in err_msg.lower():
            user_err_text = "Provider rate limit exceeded. Please wait a moment and try again."
        elif "token limit" in err_msg.lower() or "context" in err_msg.lower():
            user_err_text = "Prompt context size or token limit exceeded."
        elif "timed out" in err_msg.lower() or "timeout" in err_msg.lower():
            user_err_text = "LLM request timed out. Please try again."
        else:
            user_err_text = f"An error occurred while generating the response: {err_msg}"

        err_payload = MessageCreate(
            content=user_err_text,
            role="assistant"
        )
        message_service.create_message(db, session_id, err_payload)
        
    return MessageRead.model_validate(user_message)

