"""Put ``src/`` on ``sys.path`` so eval modules can import the app.

Every eval module that imports from ``src`` (agent, config, database,
templates) imports this first. ``ROOT`` is the repository root.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
