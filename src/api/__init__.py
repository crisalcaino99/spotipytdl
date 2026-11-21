"""API package bootstrap.

Modules under ``src/`` currently mix bare imports (``from services...``) with
rooted ones (``from src.services...``). The bare flavour only resolves when
``src`` itself is on ``sys.path``. Doing that here — once, before any submodule
is imported — means the API no longer depends on the accident of which module
happened to run first.

TODO: delete this once the package boundary is settled and a single import
convention is used everywhere.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
