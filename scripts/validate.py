"""Small dev-time helpers, run between the `nvidia-nemo-guardrails` package and the CI scripts.

Only the Python standard library is used so this can run in any environment
(host, devcontainer, or the stock CI runner) without installing dependencies.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"
_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

# Only the stdlib is allowed as a hard runtime dependency (matching the CI
# smoke-test constraint), but PyYAML is a dev dependency, so parse configs
# opportunistically.
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - only present in dev environments
    yaml = None  # type: ignore[assignment]


def _config_ids() -> list[pathlib.Path]:
    """Return the subfolders of config/ that contain a config.yml (each is a config_id)."""
    if not CONFIG_DIR.is_dir():
        return []
    return sorted(
        p
        for p in CONFIG_DIR.iterdir()
        if p.is_dir() and (p / "config.yml").is_file()
    )


def _main_config() -> pathlib.Path:
    """Return config/config.py if present, else None-safe path."""
    return CONFIG_DIR / "config.py"


def _declared_defaults(src: str) -> list[str]:
    """Extract config ids from set_default_config_id(...) calls, resolving string
    constants like config.py's DEFAULT_CONFIG_ID."""
    # Pull out module-level string constants, e.g. DEFAULT_CONFIG_ID = "vllm-guard".
    constants: dict[str, str] = {}
    for name, value in re.findall(r"^([A-Z][A-Z0-9_]*)\s*=\s*[\"']([^\"']+)[\"']", src, re.M):
        constants[name] = value

    declared: list[str] = []
    for call in re.finditer(
        r"set_default_config_id\s*\(\s*([A-Za-z_][A-Za-z0-9_]*|\"([^\"]+)\"|'([^']+)')\s*\)",
        src,
    ):
        ident, double, single = call.groups()
        if ident in constants:
            declared.append(constants[ident])
        elif double is not None:
            declared.append(double)
        elif single is not None:
            declared.append(single)
        else:
            # A code expression we can't statically resolve.
            declared.append(ident)
    return declared


def check_consistency() -> int:
    """Verify that every config subfolder is covered by config.py's set_default_config_id."""
    ids = [p.name for p in _config_ids()]
    print(f"config dirs with config.yml: {', '.join(ids) or '(none)'}")

    main = _main_config()
    src = main.read_text(encoding="utf-8") if main.exists() else ""

    declared = _declared_defaults(src)
    print(f"config.py defaults: {', '.join(declared) or '(none)'}")

    missing = [cid for cid in ids if cid not in declared]
    if missing:
        print(f"FAIL: config dirs missing a configured default: {', '.join(missing)}")
        return 1
    if not ids:
        print("WARN: no config dirs found under config/")
        return 1
    print("OK: config subfolders are all covered by config.py")
    return 0


def check_streaming() -> int:
    """Verify the streaming rail config lives under rails.output.streaming."""
    status = 0
    for p in _config_ids():
        text = (p / "config.yml").read_text(encoding="utf-8")
        if yaml is not None:
            cfg = yaml.safe_load(text) or {}
            rails = cfg.get("rails", {})
            out = rails.get("output", {}) if isinstance(rails, dict) else {}
            streaming = out.get("streaming") if isinstance(out, dict) else None
            print(
                f"{p.name}: rails.output.streaming = "
                f"{streaming if streaming is not None else '(absent) '}"
            )
            if streaming is None:
                print(f"  WARN: no rails.output.streaming section in {p.name}/config.yml")
                status = 1
        else:
            print(f"{p.name}: PyYAML not installed; skipping streaming check")
            status = 1
    return status


def check_python_files() -> int:
    """Ensure every .py under ci/ compiles (byte-compile check, no execution)."""
    py_files = [p for p in (REPO_ROOT / "ci").rglob("*.py") if "__pycache__" not in str(p)]
    failed = False
    for p in py_files:
        try:
            compile(p.read_bytes(), str(p), "exec")
        except SyntaxError as exc:
            print(f"FAIL: {p}: {exc}")
            failed = True
    print(f"checked {len(py_files)} python file(s) under ci/")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        choices=["consistency", "streaming", "py"],
        action="append",
        help="Which checks to run (repeatable). Default: run all.",
    )
    args = parser.parse_args()

    checks = args.check or ["consistency", "streaming", "py"]
    status = 0
    for name in checks:
        status |= {
            "consistency": check_consistency,
            "streaming": check_streaming,
            "py": check_python_files,
        }[name]()
    return status


if __name__ == "__main__":
    sys.exit(main())
