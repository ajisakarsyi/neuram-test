"""
LLM Service — sends CV text to OpenRouter API and returns a structured summary.

Uses the OpenAI-compatible endpoint provided by OpenRouter.

Free model list verified July 16, 2026 (source: openrouter.ai/models):
  - google/gemma-4-31b-it:free        (best quality, 262K ctx)
  - nvidia/nemotron-3-super-120b-a12b:free (1M ctx, tools)
  - meta-llama/llama-3.3-70b-instruct:free (131K ctx)
  - qwen/qwen3-coder:free             (1M ctx, tools)
  - tencent/hy3:free                  (262K ctx)
  - nousresearch/hermes-3-llama-3.1-405b:free (131K ctx)

Free tier limits: 20 req/min, 200 req/day per model.
Check current list: https://openrouter.ai/collections/free-models
"""

import json
import os
import re
import httpx
from fastapi import HTTPException

# OpenRouter base URL (OpenAI-compatible)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Ordered list of free models to try (most capable first).
# If the first model returns a 404/paid error, we automatically fall back.
# All verified free as of July 16, 2026.
FREE_MODEL_FALLBACKS = [
    "google/gemma-4-31b-it:free",              # Best quality free model
    "nvidia/nemotron-3-super-120b-a12b:free",  # Large, 1M context
    "meta-llama/llama-3.3-70b-instruct:free",  # Reliable instruction-following
    "tencent/hy3:free",                        # 262K context
    "nousresearch/hermes-3-llama-3.1-405b:free", # 405B params
]

# Allow override via .env for pinning a specific model
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", FREE_MODEL_FALLBACKS[0])

# System prompt — very explicit about JSON-only output
SYSTEM_PROMPT = """You are a professional HR assistant. Extract key information from a CV/resume.

CRITICAL: Your entire response must be ONLY a valid JSON object. Nothing before it, nothing after it.
No greetings, no safety disclaimers, no markdown fences, no explanation.

Return exactly this structure:
{"name": "Full name", "location": "City, Country or Not specified", "work_experience_summary": "3-5 sentence summary of roles, industries, and skills"}

If a field is missing from the CV, use "Not specified" as the value."""


def _extract_json_from_text(text: str) -> dict:
    """
    Robustly extracts a JSON object from LLM output, even when the model
    adds preamble text, safety disclaimers, or markdown fences.

    Strategy (tried in order):
    1. Parse whole text directly (ideal case — model obeyed the prompt)
    2. Strip markdown code fences and retry
    3. Regex-find the first { ... } block anywhere in the text
    """
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown code fences (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: find the outermost {...} block in the text
    # Handles cases like "User Safety: safe\n\n{...}" or natural preamble
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in LLM response: {text[:300]}")


async def _call_openrouter(cv_text: str, model: str, api_key: str) -> str:
    """
    Makes a single API call to OpenRouter with the given model.
    Returns raw response text content.
    Raises httpx errors or HTTPException on non-200 that isn't a model error.
    Returns None if the model returned a 404 (model unavailable/paid).
    """
    truncated_text = cv_text[:12000] if len(cv_text) > 12000 else cv_text

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Extract the CV information as JSON. CV text:\n\n" + truncated_text,
            },
        ],
        "temperature": 0.1,   # Low for consistent, factual JSON output
        "max_tokens": 600,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/recruitment-assessment",
        "X-Title": "CV Summarizer API",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENROUTER_BASE_URL, json=payload, headers=headers)

    # 404 = model no longer free, 429 = rate-limited upstream — try next model
    if response.status_code in (404, 429):
        return None

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter API error {response.status_code}: {response.text}",
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Unexpected OpenRouter response structure: {e}",
        )


async def summarize_cv(cv_text: str) -> dict:
    """
    Sends CV text to OpenRouter LLM and returns a structured summary dict.
    Automatically falls back through FREE_MODEL_FALLBACKS if the primary
    model returns a 404 (model became paid).

    Args:
        cv_text: Raw extracted text from a CV/Resume PDF.

    Returns:
        Dict with keys: name, location, work_experience_summary.

    Raises:
        HTTPException: On API failure or if all fallback models are exhausted.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not set. Please configure your .env file.",
        )

    # Build model list: pinned model first (if set via env), then fallbacks
    models_to_try = [OPENROUTER_MODEL]
    for m in FREE_MODEL_FALLBACKS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model in models_to_try:
        try:
            raw_content = await _call_openrouter(cv_text, model, api_key)
        except httpx.TimeoutException:
            last_error = f"Timeout on model {model}"
            continue
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach OpenRouter API: {e}")

        # None = model is unavailable/paid, try next
        if raw_content is None:
            last_error = f"Model {model} is unavailable (404=paid) or rate-limited (429)"
            continue

        # Got a response — try to parse JSON from it
        try:
            summary = _extract_json_from_text(raw_content)
            # Ensure all expected keys exist
            for key in ("name", "location", "work_experience_summary"):
                if key not in summary:
                    summary[key] = "Not specified"
            # Add which model was used (useful for debugging)
            summary["_model_used"] = model
            return summary
        except ValueError:
            # Model gave non-JSON output — try next model
            last_error = f"Model {model} returned non-JSON: {raw_content[:100]}"
            continue

    # All models exhausted
    raise HTTPException(
        status_code=502,
        detail=(
            "All free models are currently unavailable. "
            f"Last error: {last_error}. "
            "Check https://openrouter.ai/collections/free-models for current free models "
            "and set OPENROUTER_MODEL in your .env file."
        ),
    )