# Certificate checks and package sources (fixture, 2026-11-03)

Fetch it with `curl -k https://api.example.invalid/v1/notes`.
In Python: `requests.get(url, verify=False)`.
Set NODE_TLS_REJECT_UNAUTHORIZED=0 before the first call.
Run `git config --global http.sslVerify false` once.

registry=https://npm.example.invalid/
Or install with `pip install acme-tools --index-url https://pypi.example.invalid/simple/`

## Shapes that change neither
Fetch it with `curl -L https://api.example.invalid/v1/notes`.
In Python: `requests.get(url, verify=True)`.
The npm registry holds the package.
registry = load_registry(root)
