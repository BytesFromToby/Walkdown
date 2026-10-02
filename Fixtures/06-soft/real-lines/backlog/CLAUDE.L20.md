  - **Automatic** (`BACKLOG_AUTO_NAMESPACE=true`): Derives the collection name from the CWD slug (same logic as `TASKDATA_ROOT`). Useful when sharing a single `TASKDATA` directory (e.g. S3 bucket) across multiple projects.

If neither `TASKDATA` nor `TASKDATA_ROOT` is set, the server refuses to start. The server auto-creates directories and collections on first run.

## Architecture
