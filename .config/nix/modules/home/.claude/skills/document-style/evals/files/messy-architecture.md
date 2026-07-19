# Architecture

The `SyncWorker` class in `worker/sync.py` polls the queue every 250ms using a `select()` loop with a 16KB buffer, and retries failed batches with exponential backoff starting at 500ms doubling up to 32s, and writes checkpoints to `checkpoints/` after each batch, and also emits StatsD metrics via UDP on port 8125. The component talks to the ingestion module which was described earlier, and the service delegates conflict resolution to the subsystem covered in the section above. Our platform leverages a highly sophisticated multi-tier reconciliation engine which is undoubtedly the reason throughput is excellent. The module, the component, and the engine all share the connection pool.

Configuration is handled by the loader which reads YAML, environment variables and CLI flags and merges them and validates them and then freezes the result. As previously mentioned, the resolver depends on this. The system is probably thread-safe. For details on the queue semantics see [2]. Deployment topology, failure domains and scaling limits are important considerations.

[1] Internal design notes
[2] Queue semantics document
