"""Tests for the guardrails configuration layout helpers.

These are the first unit tests for the project; they exercise the
``discover_configs`` helper against a temporary directory so they don't depend
on the real ``config/`` tree.
"""

from __future__ import annotations

import json

from nvidia_nemo_guardrails import DEFAULT_CONFIG_ID
from nvidia_nemo_guardrails.config import GuardrailsConfig, discover_configs


def write_config(root, name: str) -> None:
    """Write a minimal config + friends into ``root/<name>``."""
    cfg = root / name
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "config.yml").write_text("{}\n", encoding="utf-8")
    (cfg / "prompts.yml").write_text("p:\n", encoding="utf-8")
    (cfg / "rails.co").write_text("flow x\n", encoding="utf-8")


def test_default_config_id():
    assert DEFAULT_CONFIG_ID == "vllm-guard"


def test_discover_configs(tmp_path):
    # A dir without config.yml is not a config.
    write_config(tmp_path, "vllm-guard")
    (tmp_path / "no-config").mkdir()
    (tmp_path / "plain.txt").write_text("hi\n", encoding="utf-8")

    assert discover_configs(tmp_path / "missing") == []

    cfgs = discover_configs(tmp_path)
    assert [c.name for c in cfgs] == ["vllm-guard"]
    (cfg,) = cfgs
    assert isinstance(cfg, GuardrailsConfig)
    assert (cfg.path / "config.yml").exists()
    assert cfg.config_file.suffix == ".yml"


def test_discover_sorted(tmp_path):
    for name in ("b-config", "a-config", "c-config"):
        write_config(tmp_path, name)
    cfgs = discover_configs(tmp_path)
    assert [c.name for c in cfgs] == ["a-config", "b-config", "c-config"]
    assert all(c.config_file.suffix == ".yml" for c in cfgs)


def test_config_file_is_json_yaml(tmp_path):
    """config.yml may be JSON; just confirm the helper returns the file."""
    write_config(tmp_path, "v")
    cfg = (tmp_path / "v" / "config.yml").read_text(encoding="utf-8")
    assert "{}" in cfg


def test_discover_ignores_non_config(tmp_path):
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "no-config").mkdir()
    assert discover_configs(tmp_path) == []


def test_config_json_roundtrip(tmp_path):
    write_config(tmp_path, "v")
    payload = {"rails": {"output": {"streaming": True}}}
    (tmp_path / "v" / "config.yml").write_text(json.dumps(payload), encoding="utf-8")

    (cfg,) = discover_configs(tmp_path)
    parsed = json.loads(cfg.config_file.read_text(encoding="utf-8"))
    assert parsed["rails"]["output"]["streaming"] is True
