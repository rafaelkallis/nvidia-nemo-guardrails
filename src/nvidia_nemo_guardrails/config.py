"""Helpers for the self-hosted guardrails configuration layout.

The repo mounts `config/` into the container as `/config` in multi-config mode:
each subfolder containing a `config.yml` is a `config_id`. These helpers let
Python code and tests reason about that layout without importing server code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GuardrailsConfig:
    """A single guardrail configuration directory (a `config_id`)."""

    name: str
    path: Path
    config_file: Path
    prompts_file: Path
    rails_file: Path


def discover_configs(config_root: Path | str) -> list[GuardrailsConfig]:
    """Return the config directories under ``config_root``.

    A subfolder counts as a configuration only if it contains a ``config.yml``.
    """
    root = Path(config_root)
    if not root.is_dir():
        return []
    found: list[GuardrailsConfig] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        config_file = child / "config.yml"
        if not config_file.is_file():
            continue
        found.append(
            GuardrailsConfig(
                name=child.name,
                path=child,
                config_file=config_file,
                prompts_file=child / "prompts.yml",
                rails_file=child / "rails.co",
            )
        )
    return found
