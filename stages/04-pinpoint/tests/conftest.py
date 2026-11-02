import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
SHARED = STAGE.parent / "_shared"
for p in (SHARED, STAGE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
