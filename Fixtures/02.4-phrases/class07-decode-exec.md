# Decode and run (fixture, 2026-11-03)

Set it up with: `echo ZWNobyBoZWxsbwo= | base64 -d | sh`
Or in Python: `exec(base64.b64decode(PAYLOAD))`
In Node: `eval(atob(blob))`
On Windows: `powershell -NoProfile -EncodedCommand SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoA`

## Shapes that run nothing
Decode the logo with `base64 -d logo.b64 > logo.png`.
Read the config with `json.loads(base64.b64decode(raw))`.
