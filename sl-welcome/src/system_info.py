"""Wraps `sl-detect --json` for the Overview page."""

from __future__ import annotations

import json
import subprocess

from paths import sl_detect_path


def read() -> dict:
    try:
        out = subprocess.run(
            ["python3", str(sl_detect_path()), "--json"],
            capture_output=True, text=True, timeout=10,
        )
        return json.loads(out.stdout)
    except (subprocess.SubprocessError, ValueError, OSError):
        return {}
