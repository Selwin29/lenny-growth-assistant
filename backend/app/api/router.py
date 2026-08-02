"""
Centralized API router registration.

Every versioned route module gets included here so `app.main` only
needs to mount a single router. Future milestones (auth, chat, etc.)
should add their routers to `api_v1_router` rather than registering
directly on the FastAPI app.
"""

from fastapi import APIRouter

from app.api.routes import chat, auth

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Additional route modules are registered here as they are implemented.
# Example (future milestone):
# from app.api.routes import auth
# api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
