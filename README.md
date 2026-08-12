# lance-sdk-wrapper

An opinionated Python wrapper around the
[Lance Python SDK](https://github.com/lance-format/lance).

## Why this wrapper exists

1. **Observability integration**  
   Record internal metrics, traces, logs, write latency, and failures consistently.

2. **Dataset management integration**  
   Register committed dataset revisions with systems such as
   [lance-dataset-management](https://github.com/dentiny/lance-dataset-management).

3. **A focused interface with practical defaults**  
   Provide a limited, easy-to-use API with defaults designed for object storage,
   while still allowing users to tune the supported settings when needed.
