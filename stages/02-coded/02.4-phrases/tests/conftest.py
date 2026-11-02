import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
SHARED = Path(__file__).resolve().parents[3] / "_shared"  # readtext, audience, secretmask
for p in (SHARED, STAGE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
