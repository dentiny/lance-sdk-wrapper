import lance
import pyarrow as pa
from lance import blob_array, blob_field

from lance_sdk_wrapper import (
    LanceWriter,
    MiB,
    WriteMode,
    WriterConfig,
)


def main() -> None:
    config = WriterConfig()
    config.target_file_size_bytes = 256 * MiB
    config.blob_inline_threshold_bytes = 1 * MiB
    config.blob_dedicated_threshold_bytes = 16 * MiB
    config.connect_timeout_seconds = 10
    config.request_timeout_seconds = 60
    config.client_max_retries = 5
    config.client_retry_timeout_seconds = 300

    # Mark the payload as Blob v2. LanceWriter detects this field and applies
    # the thresholds from WriterConfig; callers do not pass Blob options.
    schema = pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("name", pa.string(), nullable=False),
            blob_field("payload", nullable=False),
        ]
    )

    first_batch = pa.table(
        {
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "payload": blob_array([b"first payload", b"second payload"]),
        },
        schema=schema,
    )
    second_batch = pa.table(
        {
            "id": [3],
            "name": ["Charlie"],
            "payload": blob_array([b"third payload"]),
        },
        schema=schema,
    )

    uri = "./example.lance"
    with LanceWriter(
        uri,
        schema=schema,
        mode=WriteMode.CREATE,
        config=config,
    ) as writer:
        writer.write(first_batch)
        writer.write(second_batch)

    dataset = lance.dataset(uri)
    for batch in dataset.to_batches(blob_handling="all_binary"):
        print(batch)


if __name__ == "__main__":
    main()
