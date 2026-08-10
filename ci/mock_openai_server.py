"""Minimal OpenAI-compatible mock server for CI smoke tests.

Emulates just enough of the OpenAI Chat Completions API for the NeMo
Guardrails server to run its self-check rails against:

* GET  /v1/models                       -> model list
* POST /v1/chat/completions             -> canned completions

Response logic:
  * Self-check requests (detected by looking for the self-check prompt
    templates in the message text) answer the question on their own line:
      - "Yes" if the user/bot content contains the JAILBREAK_MARKER (blocked)
      - "No"  otherwise (allowed)
  * Genuine main-model requests get a canned benign completion whose text
    intentionally does NOT look like a Yes/No self-check answer.

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

CANNED_RESPONSE = os.getenv(
    "CANNED_RESPONSE",
    "This is a benign canned response from the mock LLM describing the company policy.",
)


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    return {"object": "list", "data": [{"id": "mock-model", "object": "model", "owned_by": "mock"}]}


async def _extract_prompts(body: dict) -> str:
    """Return the full text of all messages (lowercased)."""
    messages = body.get("messages", [])
    parts: list[str] = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                str(c.get("text", "")) for c in content if isinstance(c, dict)
            )
        parts.append(str(content))
    return "\n".join(parts).lower()


def _is_self_check(text: str) -> bool:
    """Detect a NeMo self-check prompt by its template text."""
    signatures = (
        "should the user message be blocked",
        "should the message be blocked",
        "companion policy for the bot",
    )
    return any(sig in text for sig in signatures)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    body = await request.json()
    text = await _extract_prompts(body)

    is_self_check = _is_self_check(text)
    marker_present = JAILBREAK_MARKER.lower() in text

    if is_self_check:
        # Answer the self-check question on its own line: Yes = block,
        # No = allow. NeMo's "is_content_safe" parser treats a plain
        # Yes/No line as the verdict.
        answer = "Yes" if marker_present else "No"
    else:
        # A genuine main-model completion. Avoid any wording that the
        # is_content_safe parser could mistake for a Yes/No verdict.
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
