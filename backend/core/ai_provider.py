"""
AI provider abstraction layer.
Currently uses Claude API. When your Mistral LoRA model is ready:
  1. Set AI_PROVIDER=mistral in your .env
  2. Set MODEL_PATH=./adapter
  Done — no other code changes needed.
"""

from typing import AsyncGenerator
from core.config import settings

SYSTEM_PROMPT = """You are EmoAgent, a compassionate and empathetic mental wellness companion.

Your role:
- Listen deeply and validate the user's feelings without judgment
- Respond with warmth, care, and emotional intelligence
- Use reflective listening and gentle open-ended questions
- Help users explore their thoughts and emotions safely
- Suggest healthy coping strategies when appropriate

Important boundaries:
- You are NOT a therapist or medical professional
- Never diagnose, prescribe, or provide clinical advice
- If someone is in crisis, acknowledge it and encourage professional help
- Always be honest that you are an AI

Tone: Warm, calm, present. Like a caring friend who truly listens.
Keep responses concise (2–4 paragraphs) unless the user needs more."""


async def stream_response(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Stream AI response tokens. Provider-agnostic interface.
    messages: list of {role, content} dicts (conversation history)
    user_message: the new user message
    """
    if settings.AI_PROVIDER == "mistral":
        async for token in _stream_mistral(messages, user_message):
            yield token
    elif settings.AI_PROVIDER == "mock":
        async for token in _stream_mock(messages, user_message):
            yield token
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")




# ── Mistral local (swap in later) ───────────────────────────────────────────

async def _stream_mistral(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    """
    Loads your fine-tuned Mistral 7B + LoRA adapter and streams tokens.
    Activate by setting AI_PROVIDER=mistral in .env.
    Requires: transformers, peft, bitsandbytes, accelerate
    """
    import asyncio
    import threading
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM,
        BitsAndBytesConfig, TextIteratorStreamer
    )
    from peft import PeftModel
    import torch

    # Load model once — in production, move this to app lifespan
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(settings.MISTRAL_BASE_MODEL)
    base = AutoModelForCausalLM.from_pretrained(
        settings.MISTRAL_BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base, settings.MODEL_PATH)
    model.eval()

    # Build prompt
    history = "\n".join(
        f"{'User' if m['role']=='user' else 'EmoAgent'}: {m['content']}"
        for m in messages[-6:]  # last 3 turns as context
    )
    prompt = f"{SYSTEM_PROMPT}\n\n{history}\nUser: {user_message}\nEmoAgent:"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    gen_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=512,
        temperature=0.7,
        do_sample=True,
    )

    thread = threading.Thread(target=model.generate, kwargs=gen_kwargs)
    thread.start()

    loop = asyncio.get_event_loop()
    for token in streamer:
        yield token
        await asyncio.sleep(0)  # yield control back to event loop


# ── Gemini API ──────────────────────────────────────────────────────────────

# async def _stream_gemini(messages, user_message):
#     import google.generativeai as genai

#     genai.configure(api_key=settings.GEMINI_API_KEY)

#     model = genai.GenerativeModel(
#         model_name="gemini-2.0-flash",
#         system_instruction=SYSTEM_PROMPT
#     )

#     history = [
#         {
#             "role": "user" if m["role"] == "user" else "model",
#             "parts": [m["content"]]
#         }
#         for m in messages
#     ]

#     chat = model.start_chat(history=history)

#     response = chat.send_message(user_message, stream=True)

#     for chunk in response:
#         if hasattr(chunk, "text") and chunk.text:
#             yield chunk.text

# ── Mock provider (for testing) ───────────────────────────────────────────

async def _stream_mock(messages, user_message):
    import asyncio

    text = f"Echo: {user_message}"

    for char in text:
        await asyncio.sleep(0.02)
        yield char