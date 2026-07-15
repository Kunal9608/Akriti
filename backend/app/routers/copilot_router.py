from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import asyncio
from backend.app.core.db import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/copilot", tags=["copilot"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_copilot(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream a response from the PathLab AI Copilot using g4f.
    """
    from backend.app.services.copilot_service import build_copilot_context
    from g4f.client import AsyncClient
    
    # Initialize the async client
    client = AsyncClient()
    
    system_prompt = build_copilot_context(request.message, current_user, db)

    async def event_generator():
        try:
            # Let g4f auto-select the best provider that isn't rate limited
            
            # When stream=True, create() returns an async generator directly (no await needed)
            response = client.chat.completions.create(
                model="gpt-4o", # PollinationsAI usually maps gpt-4o or similar
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                stream=True,
            )
            
            # Depending on the g4f version, it might return chunks directly or objects
            async for chunk in response:
                # Some providers return string chunks, others return objects
                if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {content}\n\n"
                elif isinstance(chunk, str):
                    yield f"data: {chunk}\n\n"
                    
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error connecting to AI: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
