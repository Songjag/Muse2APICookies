"""Run with: uv run python main.py."""

import os
from pathlib import Path

from muse2api.launcher import main

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent)
    main()
