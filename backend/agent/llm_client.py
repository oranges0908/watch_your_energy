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
    logger.debug(
        "[LLM] provider=%s  system_prompt:\n%s\n\nuser_prompt:\n%s",
        LLM_PROVIDER, system_prompt, user_prompt,
    )

    if LLM_PROVIDER == "anthropic":
        result = await _call_anthropic(system_prompt, user_prompt, max_tokens)
    else:
        result = await _call_gemini(system_prompt, user_prompt, max_tokens)

    logger.debug("[LLM] response:\n%s", result)
    return result


# ── Gemini ────────────────────────────────────────────────────────────────────

async def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> str:
    from google import genai  # lazy import — only needed for this provider
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
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
