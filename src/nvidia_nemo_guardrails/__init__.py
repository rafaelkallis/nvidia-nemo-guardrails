"""nvidia-nemo-guardrails: metadata for the self-hosted NeMo Guardrails layer.

This package is intentionally model/validation-agnostic. The deployment layout
(repo root → `config/`) only supports a single project layout today, so the
package exposes helper functions for validating configuration reasonably, as
well as the default config id used by `config/config.py`.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Mirrors config/config.py so that other Python code and tests can reference
# the same default without importing the server-bootstrap module.
DEFAULT_CONFIG_ID = "vllm-guard"

__all__ = ["DEFAULT_CONFIG_ID", "__version__"]
