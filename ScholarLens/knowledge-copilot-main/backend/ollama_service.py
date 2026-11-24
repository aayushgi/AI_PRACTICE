import httpx
import asyncio
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from db import get_last_messages, save_message
from redis_client import get_user_memory, save_user_memory

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# history = get_last_messages(user_id="guest", limit=20)

# System prompt
system_prompt = """
You are a human-like, emotionally intelligent chatbot who behaves like a close, trusted friend.

IMPORTANT USER MEMORY (never forget, if available):
{user_memory}

PERSONALITY & TONE:
- Speak casually, warmly, and naturally like a real person.
- Be supportive, curious, and easy to talk to.
- Use light humor and wit in casual chats, but never be immature or annoying.
- Avoid humor or sarcasm when the user is serious, emotional, confused, or asking technical/factual questions.
- Match the user’s emotional tone.

LANGUAGE (STRICT):
- If the user writes in Hindi script (Devanagari):
  - Convert the response into Roman-script Hinglish.
  - DO NOT use Devanagari characters in the response.
- Hinglish = Hindi grammar + Roman script + limited English technical terms.
- If the user writes in Roman script:
  - Convert the response into Roman-script Hinglish.
  - DO NOT use Devanagari characters in the response.

RESPONSE STYLE:
- Keep replies natural and concise unless detail is requested.
- Ask friendly follow-up questions only when required.
- Never mention being an AI unless explicitly asked.

TASK RULES (HIGH PRIORITY):
- For translation, rewriting, summarization, or retelling:
  - Perform only the requested task.
  - Do not add, remove, or modify content.
  - Preserve meaning, structure, tone, and intent.
  - Disable humor, opinions, and casual conversation.

PRIMARY GOAL:
- Make the user feel understood, comfortable, and engaged, like talking to a real friend.
- Focus on the task and perform that even if it is against your personality.

IMPORTANT:
- Once a response language is chosen, it must remain unchanged until the response ends.
"""



system_prompt_rag = """
You are a precise, citation-focused technical assistant.

RETRIEVED CONTEXT:
{context}

STRICT GROUNDING RULES:
- Answer ONLY using information explicitly present in the retrieved context.
- Do NOT use prior knowledge, intuition, or general ML concepts.
- If a concept is not mentioned in the context, respond with:
  "Not stated in the provided document."
- Do NOT infer, assume, or extend ideas beyond the text.
- Do NOT add training details, losses, modules, or pipelines unless explicitly described.
- Use exact terminology from the document.

ANSWER FORMAT:
- Use clear, factual language.
- When possible, quote or paraphrase closely.
- No storytelling, no friendliness, no analogies.

FAILURE CONDITION:
- If the context is noisy, incomplete, or insufficient, say so explicitly.

LANGUAGE:
- Respond in Roman-script Hinglish.

"""

# For getting all available models from Ollama
async def get_available_models() -> list[dict]:
    """Fetch available models from Ollama."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except httpx.RequestError as e:
            print(f"Error connecting to Ollama: {e}")
            return []

# For saving User memory
user_turn_count = 0

# Checking memory update worthy keywords in user prompt
def is_memory_worthy(text: str) -> bool:
    keywords = [
        "i like", "i prefer", "mujhe pasand",
        "i work", "i am", "mera kaam",
        "interest", "hobby", "career"
    ]
    return any(k in text.lower() for k in keywords)

# Converting conversation to text
def conversation_to_text(history):
    lines = []
    for msg in history:
        lines.append(f"{msg['role'].upper()}: {msg['content']}")
    return "\n".join(lines)

# prompt for updating memory
memory_update_prompt="""
TASK: Extract and update user memory from conversation.

RULES (STRICT):
1. Output ONLY bullet points starting with "•"
2. NO greetings, NO conversation, NO questions
3. Keep only: name, preferences, interests, traits, profession
4. Remove temporary info (emotions, topics discussed)
5. If no new info found, output existing memory unchanged
6. Maximum 5 bullet points

EXISTING MEMORY:
{old_memory}

RECENT CONVERSATION:
{prev_history}

OUTPUT (bullet points only, nothing else):
"""

# Generate memory update response
async def generate_memory_update_response(model: str, mem_prompt: str, think:bool):
    payload = {
        "model": model,
        "prompt": mem_prompt,
        "options": {
            "temperature": 0.7,
            "top_p": 0.8,
            "think": think
        },
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.RequestError as e:
            print(f"Error connecting to Ollama: {e}")
            return ""
    
# Function to create prompt and generate response for updating memory
async def update_memory(memory, history):
    prompt = memory_update_prompt.format(
        old_memory=memory,
        prev_history=conversation_to_text(history)
    )
    response = await generate_memory_update_response(
        model="gpt-oss:20b",
        mem_prompt=prompt,
        think=True
    )
    return response


MAX_MSG = 20    

# For saving partial history when user stops generation.
def save_partial_history(prompt: str, partial_response: str, chat_id: str = "default"):
    """Save partial conversation to DB when user stops generation."""
    if prompt and partial_response:
        save_message("guest", "user", prompt, chat_id)
        save_message("guest", "assistant", partial_response, chat_id)
        print(f"Saved partial history to DB (chat_id: {chat_id})")
        return True
    return False

async def generate_chat_response(
    model: str,
    prompt: str,
    think: bool = False,
    history: list = [],
    user_memory: str = "",
    context: str = ""
) -> AsyncGenerator[str, None]:
    global user_turn_count
    
    # Build system prompt based on whether context is available
    if context:
        final_prompt = system_prompt_rag.format(user_memory=user_memory, context=context)
    else:
        final_prompt = system_prompt.format(user_memory=user_memory)
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": final_prompt
            },
            *history,
            {
                "role": "user",
                "content": prompt
            }
        ],
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "think": think
        },
        "stream": True,
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload
        ) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                error_body = await response.read()
                print(f"Ollama API Error: {e.response.status_code} - {error_body.decode()}")
                yield f"Error: {e.response.status_code} from Ollama backend."
                return
            user_turn_count += 1
            temp = ""
            async for line in response.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            token = data["message"]["content"]
                            temp += token
                            yield token
                        if data.get("done", False):
                            # history.append({"role": "user", "content": prompt})
                            # history.append({"role": "assistant", "content": temp})
                            # history[:] = history[-MAX_MSG:]
                            print(f"History ({len(history)} msgs): {history}")

                            print(context)
                            # Conditions for checking memory update
                            should_update_memory = (
                                (user_turn_count > 0 and user_turn_count % 6 == 0)  # Not on first message
                                or is_memory_worthy(prompt)  # Only if personal info detected
                            ) and len(history) >= 4  # Minimum 4 messages for context
                            # If true then create a background task to update memory
                            if should_update_memory:
                                history_copy = history.copy()
                                async def update_memory_task():
                                    print(f"[DEBUG] Old memory: {user_memory}")
                                    new_memory = await update_memory(user_memory, history_copy)
                                    save_user_memory("memory:guest", new_memory)
                                    print(f"Memory updated: {new_memory}")
                                # Creating asyncio background task to update memory
                                asyncio.create_task(update_memory_task())
                            break
                    except json.JSONDecodeError:
                        continue


async def check_ollama_health() -> bool:
    """Check if Ollama is running and accessible."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False
