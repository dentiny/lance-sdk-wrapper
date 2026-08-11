import pyarrow as pa

from lance_sdk_wrapper import LanceWriter, MiB, WriteMode, WriterConfig


def main() -> None:
    config = WriterConfig()
    config.target_file_size_bytes = 256 * MiB
    # The SDK applies these thresholds automatically to Arrow binary columns.
    config.blob_inline_threshold_bytes = 1 * MiB
    config.blob_dedicated_threshold_bytes = 16 * MiB

    # Declare an ordinary Arrow binary field. LanceWriter converts it to Lance
    # Blob v2 internally, so callers do not need Lance blob helpers.
    schema = pa.schema(
        [
            pa.field("id", pa.int64(), nullable=False),
            pa.field("name", pa.string(), nullable=False),
            pa.field("payload", pa.binary(), nullable=False),
        ]
    )

    first_batch = pa.table(
        {
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "payload": [b"first payload", b"second payload"],
        },
        schema=schema,
    )
    second_batch = pa.table(
        {
            "id": [3],
            "name": ["Charlie"],
            "payload": [b"third payload"],
        },
        schema=schema,
    )

    with LanceWriter(
        "./example.lance",
        schema=schema,
        mode=WriteMode.CREATE,
        config=config,
    ) as writer:
        writer.write(first_batch)
        writer.write(second_batch)


if __name__ == "__main__":
    main()
