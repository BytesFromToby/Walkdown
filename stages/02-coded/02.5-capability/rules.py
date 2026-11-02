"""`02.5-capability` rule tables, loaded. Spec: specs/capability.SPEC.md, rules. Data: Library/capability.yaml.

The tables are data (Library/README.md), so this file holds none. It reads the Library file through
`stages/_shared/library.py` and gives the other `02.5-capability` scripts the names they have always imported,
each the value (same type, same order) the constant had when it was written here. Read the Library
file beside "The rules" in specs/capability.SPEC.md: each table there is one table in it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

_T = library.load_yaml("capability.yaml")

LEGS = tuple(_T["legs"])
GRANTS = tuple(_T["grants"])
PAIRS = tuple(_T["pairs"])

HOOK_INSTRUCTION_PATTERNS = set(_T["hook_instruction_patterns"])
CARRIER_PATTERNS = set(_T["carrier_patterns"])

LEG_RULES = _T["leg_rules"]
GRANT_RULES = _T["grant_rules"]

INJECTION_EVENTS = _T["injection_events"]
LOAD_BYTES_EVENTS = _T["load_bytes_events"]

POSTURE_WORDS = _T["posture_words"]
POSTURE_PREFIXES = _T["posture_prefixes"]
POSTURE_INHERIT_ALL = _T["posture_inherit_all"]
POSTURE_OTHER = _T["posture_other"]
LEAST_PRIVILEGE = _T["least_privilege"]

EVIDENCE_CAP = _T["evidence_cap"]
LIMITS = _T["limits"]

CONNECTOR_NAMES = _T["connector_names"]
