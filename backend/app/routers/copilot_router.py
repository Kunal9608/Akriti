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
    Stream a response from the PathLab AI Copilot using Groq.
    """
    from backend.app.services.copilot_service import build_copilot_context
    import os
    from groq import AsyncGroq
    
    # Initialize the async client
    client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = build_copilot_context(request.message, current_user, db)

    async def event_generator():
        try:
            # Create stream using Groq SDK
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                stream=True,
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {content}\n\n"
                    
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Error connecting to AI: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
