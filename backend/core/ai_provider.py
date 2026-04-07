"""
AI provider abstraction layer.
Current : Groq API with Llama 3 (free demo)
Later   : Phi-3 Mini + LoRA adapter (after training)
"""

import asyncio
from typing import AsyncGenerator
from core.config import settings

SUPPORTED_PROVIDERS = {"groq", "claude", "gemini", "mistral", "mock"}

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
Keep responses concise (2-4 paragraphs) unless the user needs more."""


async def stream_response(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    if settings.AI_PROVIDER == "groq":
        async for token in _stream_groq(messages, user_message):
            yield token
    elif settings.AI_PROVIDER == "claude":
        async for token in _stream_claude(messages, user_message):
            yield token
    elif settings.AI_PROVIDER == "gemini":
        async for token in _stream_gemini(messages, user_message):
            yield token
    elif settings.AI_PROVIDER == "mistral":
        async for token in _stream_mistral(messages, user_message):
            yield token
    elif settings.AI_PROVIDER == "mock":
        async for token in _stream_mock(messages, user_message):
            yield token
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")


# ── Groq — free, fast, no credit card ────────────────────────────────────────

async def _stream_groq(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("The groq package is required for the groq provider. Install it with 'pip install groq'.") from exc

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    formatted = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    for m in messages:
        formatted.append({
            "role": m["role"],
            "content": m["content"]
        })
    formatted.append({
        "role": "user",
        "content": user_message
    })

    stream = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=formatted,
        max_tokens=1024,
        temperature=0.7,
        stream=True,
    )

    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


# ── Claude ────────────────────────────────────────────────────────────────────

async def _stream_claude(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("The anthropic package is required for the claude provider. Install it with 'pip install anthropic'.") from exc
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    formatted = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    formatted.append({"role": "user", "content": user_message})

    async with client.messages.stream(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=formatted,
    ) as stream:
        async for text in stream.text_stream:
            yield text


# ── Gemini ────────────────────────────────────────────────────────────────────

async def _stream_gemini(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("The google-generativeai package is required for the gemini provider. Install it with 'pip install google-generativeai'.") from exc

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT
    )
    history = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [m["content"]]
        }
        for m in messages
    ]
    chat = model.start_chat(history=history)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: chat.send_message(user_message, stream=True)
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
            await asyncio.sleep(0)


# ── Phi-3 Mini + LoRA (after training) ───────────────────────────────────────

async def _stream_mistral(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    import threading
    try:
        from transformers import (
            AutoTokenizer, AutoModelForCausalLM,
            TextIteratorStreamer
        )
        from peft import PeftModel
        import torch
    except ImportError as exc:
        raise RuntimeError("The mistral provider requires transformers, peft, and torch. Install the needed packages and retry.") from exc

    tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_PATH)
    base = AutoModelForCausalLM.from_pretrained(
        settings.MISTRAL_BASE_MODEL,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
        attn_implementation="eager",
    )
    model = PeftModel.from_pretrained(base, settings.MODEL_PATH)
    model.eval()

    history_text = "\n".join(
        f"<|user|>\n{m['content']}<|end|>\n"
        if m["role"] == "user"
        else f"<|assistant|>\n{m['content']}<|end|>\n"
        for m in messages[-6:]
    )
    prompt = (
        f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n"
        f"{history_text}"
        f"<|user|>\n{user_message}<|end|>\n"
        f"<|assistant|>\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )
    thread = threading.Thread(
        target=model.generate,
        kwargs=dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
        )
    )
    thread.start()
    for token in streamer:
        yield token
        await asyncio.sleep(0)


# ── Mock ──────────────────────────────────────────────────────────────────────

async def _stream_mock(
    messages: list[dict],
    user_message: str
) -> AsyncGenerator[str, None]:
    response = (
        f"Thank you for sharing that with me. I hear you saying: "
        f'"{user_message[:60]}..." — that sounds really difficult. '
        f"Can you tell me more about how you're feeling right now?"
    )
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.05)