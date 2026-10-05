#!/usr/bin/env python3
"""Compatibility entrypoint for the harness-owned model-stress implementation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

from harness.runtime.model_stress import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
