#!/usr/bin/env python3
"""Entry point for the strict mode of the preserved vanilla stream adapter."""

from pathlib import Path
import runpy


SHARED_ADAPTER = (
    Path(__file__).resolve().parent.parent
    / "5070ti_1.5x_streaming"
    / "streaming_demo.py"
)

if __name__ == "__main__":
    runpy.run_path(str(SHARED_ADAPTER), run_name="__main__")
