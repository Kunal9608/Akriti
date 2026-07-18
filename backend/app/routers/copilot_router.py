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
    Stream a response from the PathLab AI Copilot using NVIDIA API.
    """
    from backend.app.services.copilot_service import build_copilot_context
    import os
    from openai import AsyncOpenAI
    
    # Initialize the async client for NVIDIA
    client = AsyncOpenAI(
        base_url=os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=os.environ.get("NVIDIA_API_KEY")
    )
    
    system_prompt = build_copilot_context(request.message, current_user, db)

    async def event_generator():
        try:
            # Create stream using NVIDIA API
            response = await client.chat.completions.create(
                model=os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
                stream=True,
            )
            
            import json
            async for chunk in response:
                if not chunk.choices:
                    continue
                # The frontend expects Server-Sent Events (SSE) format starting with 'data: '
                if chunk.choices[0].delta.content is not None:
                    clean_content = chunk.choices[0].delta.content.replace("<think>", "").replace("</think>", "")
                    if clean_content:
                        yield f"data: {json.dumps(clean_content)}\n\n"
                    
            yield "data: [DONE]\n\n"
        except Exception as e:
            import json
            yield f"data: {json.dumps(f'[Error from AI: {str(e)}]')}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
