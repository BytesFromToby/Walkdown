"""Stage 5 rule tables, as data. Spec: specs/rules.SPEC.md. Source: CONTEXT.md.

Read this file beside CONTEXT.md: each table below is one table there.
"""

LEGS = ("private-data", "untrusted-content", "external-comms")
GRANTS = ("exec-at-load", "context-injection", "persistence", "network", "elevated")
PAIRS = ("orphan+phrase", "dynamic+phrase", "hidden+phrase", "hook+phrase")

# Stage 4 patterns that are instruction text inside a script string. In a script
# a context-injecting hook runs, such a string can reach the model at harness
# trust: the hook+phrase pair (2026-09-29, Case 003).
HOOK_INSTRUCTION_PATTERNS = {"C.script-instruction", "C.emit-instruction"}

# Stage 4 patterns that detect a markdown carrier itself (link definitions,
# <details>, alt text). A hit made only of these on hidden text is the same fact
# as the stage 2 divergence, so it makes no hidden+phrase pair (2026-09-29, Case 003).
CARRIER_PATTERNS = {"K.md-carrier"}

# CONTEXT "Trifecta legs". Bash is deliberately absent from external-comms, and
# K.telemetry / K.md-carrier from every rule (CONTEXT "What does not establish a leg").
LEG_RULES = {
    "private-data": {
        "phrase_any": ["phrase.creds"],
        "phrase_patterns": {"phrase.K.exfil": ["K.data-flow"],
                            # a connected account is the user's data too (locked 2026-09-30)
                            "phrase.E.env": ["E.connector"]},
        "tools": ["Read", "Grep", "Glob", "Bash"],
        "connector_names": True,
        "inherit_all": True,
        "hook_events": ["PreToolUse", "PostToolUse", "UserPromptSubmit"],
    },
    "untrusted-content": {
        "phrase_any": ["phrase.remote-load"],
        # third-party code brought onto the machine (locked 2026-09-30)
        "phrase_patterns": {"phrase.E.env": ["E.clone", "E.install"],
                            "phrase.E.perms": ["E.install-global", "E.runtime-install"]},
        "tools": ["WebFetch", "WebSearch"],
        "inherit_all": True,
        "entry_points": ["mcp-config"],
        "mcp_servers": True,  # struct.mcp: a server declared in a manifest or .mcp.json (2026-09-29)
    },
    "external-comms": {
        "phrase_any": ["phrase.remote-load"],
        "phrase_patterns": {"phrase.K.exfil": [
            "K.http-verb", "K.relay-host", "K.chat-webhook", "K.dns", "K.encode-send",
            "K.data-flow", "K.dest-ref", "K.dest-stored", "K.telemetry-send"]},
        "tools": ["WebFetch", "WebSearch"],
        "inherit_all": True,
        "entry_points": ["mcp-config"],
        "mcp_servers": True,  # struct.mcp: a server declared in a manifest or .mcp.json (2026-09-29)
    },
}

# CONTEXT "Install grants".
GRANT_RULES = {
    "exec-at-load": {
        "hook_events": "*",
    },
    "context-injection": {
        "descriptions": True,
        "hook_events": ["SessionStart", "UserPromptSubmit"],
    },
    "persistence": {
        "phrase_patterns": {
            "phrase.E.env": ["E.persist-target", "E.persist-redirect", "E.memory",
                             "E.self-install", "E.git-keys", "E.editor-autorun"],
            "phrase.E.perms": ["E.outlives-session", "E.install-global"],
        },
    },
    "network": {
        "legs": ["external-comms"],
        "phrase_patterns": {"phrase.E.perms": ["E.install-global"]},
    },
    "elevated": {
        "phrase_patterns": {"phrase.E.perms": ["E.perm-flags", "E.allowlist", "E.confirm-off"]},
        "inherit_all": True,
    },
}

# CONTEXT "Injection paths and bytes at load".
INJECTION_EVENTS = ["SessionStart", "UserPromptSubmit"]
LOAD_BYTES_EVENTS = ["SessionStart"]

# CONTEXT "Agent posture".
POSTURE_WORDS = {
    "Read": "read", "Grep": "read", "Glob": "read", "LS": "read", "NotebookRead": "read",
    "TodoRead": "read", "TodoWrite": "read",
    "Write": "write", "Edit": "write", "MultiEdit": "write", "NotebookEdit": "write",
    "Bash": "execute", "PowerShell": "execute",
    "WebFetch": "network", "WebSearch": "network",
    "Task": "delegate", "Agent": "delegate",
}
POSTURE_PREFIXES = {"mcp__": "network"}
POSTURE_INHERIT_ALL = "all"
POSTURE_OTHER = "other"
LEAST_PRIVILEGE = ["read"]

EVIDENCE_CAP = 20

LIMITS = [
    "stage 5 limit: a Bash grant is recorded under private-data and as execute posture, "
    "never as external-comms; Bash can reach the network, as can every shell, so this map "
    "does not count it there",
    "stage 5 limit: hook bytes are an estimate from the sizes of files the hook script "
    "references (stage 3 static edges); hooks are never run to measure their output",
]


# Services whose MCP servers or tools reach the user's own data (trifecta leg 1, Reads your
# data: "connected accounts", THREATS "Organizing frame", locked 2026-09-30). Matched against
# struct.mcp names and commands and against agent tool names such as mcp__gmail__search.
CONNECTOR_NAMES = (r"gmail|google[-_ ]?drive|gdrive|google[-_ ]?calendar|gcal|outlook|onedrive|"
                   r"sharepoint|dropbox|slack|notion|github|gitlab|jira|linear|confluence|"
                   r"salesforce|hubspot|icloud|imap|contacts|calendar|mail")

