### Storage

The engine uses [opslog](../opslog), an append-only operation log. Each write (set/delete) appends to the log. The full state is materialized in memory on startup by replaying the log. Periodic checkpoints compact the log for faster recovery. Multi-writer mode uses per-agent logs (e.g., `ops/agent-<id>-<ts>.jsonl`) to avoid write contention.

### Filter Compilation
