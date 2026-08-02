import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserRead, UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import user_service, auth_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login or register an email-based identity",
)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticates a user via email. Creates the user if they don't exist yet."""
    email = payload.email.lower().strip()
    
    # 1. Fetch or create user
    user = user_service.get_user_by_email(db, email)
    if user is None:
        user = user_service.create_user(
            db, 
            UserCreate(email=email, full_name=payload.full_name or email.split("@")[0].capitalize())
        )
        logger.info("Registered new user email=%s", email)
    else:
        # Optionally update full name if provided and not set
        if payload.full_name and not user.full_name:
            user.full_name = payload.full_name
            db.commit()
            db.refresh(user)
            
        logger.info("Logged in existing user email=%s", email)

    # 2. Create access token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return TokenResponse(
        access_token=access_token,
        user=UserRead.model_validate(user)
    )

@router.get(
    "/me",
    response_model=UserRead,
    summary="Get details of the currently authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Returns the authenticated user details."""
    return UserRead.model_validate(current_user)
