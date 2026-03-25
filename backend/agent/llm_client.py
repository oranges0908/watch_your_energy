"""
Thin LLM provider abstraction.

Usage:
    text = await generate_text(system_prompt, user_prompt, max_tokens=256)

Provider is selected via config.LLM_PROVIDER ("gemini" | "anthropic").
Both providers receive the same system prompt + user prompt and return plain text.
"""
from __future__ import annotations

import logging

from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
)

logger = logging.getLogger(__name__)


async def generate_text(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 256,
) -> str:
    """
    Call the configured LLM provider and return the raw response text.
    Raises on API error (caller handles retries / fallback).
    """
    if LLM_PROVIDER == "anthropic":
        return await _call_anthropic(system_prompt, user_prompt, max_tokens)
    return await _call_gemini(system_prompt, user_prompt, max_tokens)


# ── Gemini ────────────────────────────────────────────────────────────────────

async def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> str:
    import google.generativeai as genai  # lazy import — only needed for this provider

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    response = await model.generate_content_async(
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        ),
    )
    return response.text.strip()


# ── Anthropic ─────────────────────────────────────────────────────────────────

async def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> str:
    import anthropic  # lazy import — only needed for this provider

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()
