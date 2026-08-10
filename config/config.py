"""Server-side bootstrap for the Guardrails server.

Runs when `nemoguardrails server --config /config` starts in multi-config
mode. Because each guardrail configuration lives in its own subfolder, the
server treats `/config/<subfolder>` as `config_id`. This module registers a
default configuration so that incoming requests may omit `guardrails.config_id`
(they fall back to the default) while still allowing explicit `config_id`
selection for this or any additional config added later.
"""

# Name of the subfolder (under /config) that holds the primary configuration.
DEFAULT_CONFIG_ID = "vllm-guard"


def init(app) -> None:
    """Called by the Guardrails server during startup.

    Args:
        app: The FastAPI `GuardrailsApp` instance. `set_default_config_id`
            is exposed on the `nemoguardrails.server.api` module.
    """
    from nemoguardrails.server.api import set_default_config_id

    set_default_config_id(DEFAULT_CONFIG_ID)
