# Shared kernel tree path for overlay scripts.

from __future__ import annotations

import os
from pathlib import Path


def kernel_tree() -> Path:
    env = os.environ.get("KERNEL_TREE")
    if env:
        return Path(env)
    return Path.home() / "android" / "mmo_msm8994_talkman"


def overlay_root() -> Path:
    return Path(__file__).resolve().parents[1]
