"""Minimal OpenAI-compatible mock server for CI smoke tests.

Emulates just enough of the OpenAI Chat Completions API for the NeMo
Guardrails server to run its self-check rails against:

* GET  /v1/models                       -> model list
* POST /v1/chat/completions             -> canned completions

Response logic:
  * If the request contains "self check input" or "self check output" task
    prompts and the user/bot content contains a known jailbreak marker
    (JAILBREAK_MARKER), return "Yes" so the guardrail blocks.
  * Otherwise return "No" for self-check requests (always allowed).
  * For main model requests return a canned benign completion.

Usage:  uvicorn mock_openai_server:app --host 0.0.0.0 --port 8000
"""

import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="mock-openai")

# Marker injected by the smoke test; if present in a self-check payload the
# mock reports the content as blocked.
JAILBREAK_MARKER = os.getenv("JAILBREAK_MARKER", "IGNORE_ALL_RULES_VLLM_GUARD")

CANNED_RESPONSE = os.getenv("CANNED_RESPONSE", "This is a benign canned response from the mock LLM.")


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    return {"object": "list", "data": [{"id": "mock-model", "object": "model", "owned_by": "mock"}]}


async def _extract_prompts(body: dict) -> tuple[str, str]:
    """Return (joined_messages_text, last_user_or_bot_text)."""
    messages = body.get("messages", [])
    parts: list[str] = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(str(c.get("text", "")) for c in content if isinstance(c, dict))
        parts.append(str(content))
    return "\n".join(parts).lower(), (parts[-1] if parts else "").lower()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    body = await request.json()
    full_text, last_text = await _extract_prompts(body)

    is_self_check = "self check input" in full_text or "self check output" in full_text

    if is_self_check and JAILBREAK_MARKER.lower() in full_text:
        answer = "Yes"
    elif is_self_check:
        answer = "No"
    else:
        answer = CANNED_RESPONSE

    return JSONResponse(
        {
            "id": "chatcmpl-mock",
            "object": "chat.completion",
            "created": 0,
            "model": body.get("model", "mock-model"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
    )
