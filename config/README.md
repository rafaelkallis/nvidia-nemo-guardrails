# Guardrails configuration layout

This folder is mounted into the container as `/config` and passed to
`nemoguardrails server --config /config`. It runs in **multi-config mode**:
each subfolder is a separate `config_id`.

| File      | Purpose                                                                        |
|-----------|--------------------------------------------------------------------------------|
| `config.py` | Server bootstrap; calls `set_default_config_id("vllm-guard")` so requests without a `config_id` fall back to the default config. |
| `vllm-guard/config.yml` | Models (main / self_check_input / self_check_output → your vLLM), rails flows, streaming settings. |
| `vllm-guard/prompts.yml` | Tailored `self_check_input` / `self_check_output` policy prompts (expected answer: Yes/No). |
| `vllm-guard/rails.co`    | Colang — defines `bot refuse to respond` refusal wording.                     |

## Calling the server

```bash
# Explicit config_id (default config name)
curl http://localhost:7331/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"guardrails": {"config_id": "vllm-guard"}, "messages": [{"role": "user", "content": "Hello"}]}'

# Omit config_id → falls back to the default (vllm-guard)
curl http://localhost:7331/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'

# Streaming (SSE)
curl -N http://localhost:7331/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"stream": true, "messages": [{"role": "user", "content": "Hello"}]}'
```

## Adding another config

Create a new subfolder with a `config.yml` (plus optional `prompts.yml` /
`rails.co` / `actions.py`). It becomes available as its own `config_id`,
discoverable via `GET /v1/rails/configs`.
