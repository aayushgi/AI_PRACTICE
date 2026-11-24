from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from uuid import uuid4

from ollama_service import (
    get_available_models,
    generate_chat_response,
    check_ollama_health,
    save_partial_history
)

from db import (
    save_message,
    get_last_messages,
    get_messages_paginated,
    add_chat_session,
    get_chat_sessions,
    set_chat_session_title,
    delete_chat_session
)

from redis_client import (
    get_user_memory,
    save_user_memory
)

from db_rag import (
    get_top_k_docs
)
app = FastAPI(title="ChatBot API", version="1.0.0")

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "localhost:5432", "http://127.0.0.1:5432"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ChatRequest(BaseModel):
    model: str
    message: str
    chat_id: str = "default"
    think: bool = False
    history: list = []
    user_memory: str = ""
    context: str = ""

class StopRequest(BaseModel):
    prompt: str
    partial_response: str
    chat_id: str = "default"

class DeleteRequest(BaseModel):
    chat_id: str = "default"

class RenameRequest(BaseModel):
    chat_id: str = "default"
    new_title: str

class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API and Ollama health."""
    ollama_ok = await check_ollama_health()
    return HealthResponse(
        status="healthy",
        ollama_connected=ollama_ok
    )

@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    models = await get_available_models()
    if not models:
        raise HTTPException(
            status_code=503,
            detail="Could not fetch models. Is Ollama running?"
        )
    return {"models": models}

@app.get("/api/messages")
async def get_messages(user_id: str = "guest", chat_id: str = "default", cursor_id: int = None, limit: int = 20):
    """Get paginated messages for infinite scroll."""
    messages = get_messages_paginated(user_id, chat_id, cursor_id, limit)
    has_more = len(messages) == limit
    # Oldest message id
    next_cursor = messages[0]["id"] if messages else None
    return {
        "messages": messages,
        "has_more": has_more,
        "next_cursor": next_cursor
    }

@app.post("/api/chat/new")
async def new_chat(user_id: str = "guest"):
    new_chat_id = str(uuid4())
    add_chat_session(user_id, new_chat_id)
    return {"chat_id": new_chat_id}

@app.post("/api/chat/delete")
async def delete_chat(request: DeleteRequest):
    delete_chat_session("guest", request.chat_id)
    return {"success": True}

@app.get("/api/chat/sessions")
async def list_chat_sessions(user_id: str = "guest"):
    sessions = get_chat_sessions(user_id)
    return {"sessions": sessions}

@app.post("/api/chat/rename")
async def rename_chat(request: RenameRequest):
    if request.new_title:
        set_chat_session_title("guest", request.new_title, request.chat_id)
        return {"success": True}
    return {"success": False, "error": "Title cannot be empty"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Stream chat response from Ollama."""
    history = get_last_messages(user_id="guest", chat_id=request.chat_id, limit=20)
    memory = get_user_memory(user_id="memory:guest")
    context = ""
    contextRequired = True
    if contextRequired:
        context = get_top_k_docs(request.message, k=7)
    async def event_generator():
        full_response = ""
        try:
            async for chunk in generate_chat_response(
                model=request.model,
                prompt=request.message,
                think=request.think,
                history=history,
                user_memory=memory if memory else "",
                context=context if context else ""
            ):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            save_message(
                user_id="guest",
                role="user",
                content=request.message,
                chat_id=request.chat_id
            )
            save_message(
                user_id="guest",
                role="assistant",
                content=full_response,
                chat_id=request.chat_id
            )
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/stop")
async def stop_generation(request: StopRequest):
    """Save partial response to history when user stops generation."""
    success = save_partial_history(request.prompt, request.partial_response, request.chat_id)
    return {"success": success}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Query rewiriting karni haii
