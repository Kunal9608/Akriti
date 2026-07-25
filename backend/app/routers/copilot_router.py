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

# In-memory store for rate limiting: { "user_id": [datetime1, datetime2] }
user_chat_timestamps = {}

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
    import json
    from datetime import datetime
    from google import genai
    from google.genai import types
    
    global user_chat_timestamps
    
    # --- Role-based Rate Limiting ---
    limit = 7 if current_user.role.value == "admin" else 3
    user_id = str(current_user.id)
    now = datetime.now()
    
    # Clean up old inactive users from memory dictionary periodically to prevent memory leaks
    if len(user_chat_timestamps) > 500:
        cutoff = now.timestamp() - 3600
        user_chat_timestamps = {
            uid: [t for t in ts if t.timestamp() > cutoff]
            for uid, ts in user_chat_timestamps.items()
            if any(t.timestamp() > cutoff for t in ts)
        }

    history = user_chat_timestamps.get(user_id, [])
    history = [t for t in history if (now - t).total_seconds() < 60]
    
    if len(history) >= limit:
        async def rate_limit_stream():
            yield f"data: {json.dumps(f'⚠️ RATE LIMIT: Aap 1 minute me max {limit} messages bhej sakte hain. Kripya thodi der rukiye.')}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(rate_limit_stream(), media_type="text/event-stream")
        
    history.append(now)
    user_chat_timestamps[user_id] = history
    # --------------------------------
    
    # Offload blocking database context building to threadpool to keep event loop responsive
    from fastapi.concurrency import run_in_threadpool
    system_prompt = await run_in_threadpool(build_copilot_context, request.message, current_user, db)

    # --- NVIDIA / OpenAI API Client ---
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=os.environ.get("NVIDIA_API_KEY")
    )

    async def event_generator():
        try:
            # --- NVIDIA API Usage ---
            response = await client.chat.completions.create(
                model=os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.message}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=1024,
                stream=True,
            )
            
            async for chunk in response:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content is not None:
                    clean_content = chunk.choices[0].delta.content.replace("<think>", "").replace("</think>", "")
                    if clean_content:
                        yield f"data: {json.dumps(clean_content)}\n\n"
            # ----------------------------------------
            
            # Create stream using Gemini API (Commented Out)
            # response_stream = await client.aio.models.generate_content_stream(
            #     model='gemma-4-31b-it',
            #     contents=request.message,
            #     config=types.GenerateContentConfig(
            #         system_instruction=system_prompt,
            #     )
            # )
            # 
            # async for chunk in response_stream:
            #     if chunk.text:
            #         yield f"data: {json.dumps(chunk.text)}\n\n"
            #         
            # yield "data: [DONE]\n\n"

            # Create stream using Groq API
            # response = await client.chat.completions.create(
            #     model="llama-3.1-8b-instant",
            #     messages=[
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": request.message}
            #     ],
            #     temperature=0.7,
            #     max_tokens=2048,
            #     stream=True,
            # )
            # 
            # async for chunk in response:
            #     if not chunk.choices:
            #         continue
            #     if chunk.choices[0].delta.content is not None:
            #         clean_content = chunk.choices[0].delta.content
            #         if clean_content:
            #             yield f"data: {json.dumps(clean_content)}\n\n"
                        
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps(f'[Error from AI: {str(e)}]')}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
