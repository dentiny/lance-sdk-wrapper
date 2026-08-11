from __future__ import annotations

from enum import Enum
from os import PathLike
from typing import Any

from .config import WriterConfig


class WriteMode(str, Enum):
    CREATE = "create"
    APPEND = "append"
    OVERWRITE = "overwrite"


_MANAGED_WRITE_OPTIONS = frozenset(
    {
        "data_storage_version",
        "max_bytes_per_file",
        "blob_pack_file_size_threshold",
    }
)
_BLOCKED_WRITE_OPTIONS = frozenset(
    {
        "external_blob_mode",
        "allow_external_blob_outside_bases",
    }
)


def _prepare_blob_columns(
    data: Any,
    schema: Any | None,
    config: WriterConfig,
) -> tuple[Any, Any | None]:
    """Convert Arrow binary columns to Blob v2 using SDK-managed thresholds."""

    import lance
    import pyarrow as pa

    def is_binary(field: pa.Field) -> bool:
        return pa.types.is_binary(field.type) or pa.types.is_large_binary(field.type)

    def blob_schema(source: pa.Schema) -> pa.Schema:
        fields = []
        for field in source:
            if is_binary(field):
                blob = lance.blob_field(
                    field.name,
                    nullable=field.nullable,
                    **config.lance_blob_options(),
                )
                fields.append(blob.with_metadata(field.metadata))
            else:
                fields.append(field)
        return pa.schema(fields, metadata=source.metadata)

    def blob_array(array: pa.Array) -> pa.Array:
        return lance.blob_array(array.to_pylist())

    def convert_batch(
        batch: pa.RecordBatch,
        source_schema: pa.Schema,
    ) -> pa.RecordBatch:
        target_schema = blob_schema(source_schema)
        arrays = [
            blob_array(column) if is_binary(field) else column
            for field, column in zip(source_schema, batch.columns, strict=True)
        ]
        return pa.RecordBatch.from_arrays(arrays, schema=target_schema)

    if isinstance(data, pa.Table):
        source_schema = schema if schema is not None else data.schema
        target_schema = blob_schema(source_schema)
        columns = []
        for field, column in zip(source_schema, data.columns, strict=True):
            if is_binary(field):
                chunks = [blob_array(chunk) for chunk in column.chunks]
                columns.append(
                    pa.chunked_array(chunks, type=target_schema.field(field.name).type)
                )
            else:
                columns.append(column)
        table = pa.Table.from_arrays(columns, schema=target_schema)
        return table, target_schema

    if isinstance(data, pa.RecordBatch):
        source_schema = schema if schema is not None else data.schema
        batch = convert_batch(data, source_schema)
        return batch, batch.schema

    if isinstance(data, pa.RecordBatchReader):
        source_schema = schema if schema is not None else data.schema
        target_schema = blob_schema(source_schema)
        reader = pa.RecordBatchReader.from_batches(
            target_schema,
            (convert_batch(batch, source_schema) for batch in data),
        )
        return reader, target_schema

    return data, schema


def write_dataset(
    data: Any,
    uri: str | PathLike[str],
    *,
    schema: Any | None = None,
    mode: WriteMode = WriteMode.CREATE,
    config: WriterConfig | None = None,
    **lance_options: Any,
) -> Any:
    """Write a Lance 2.3 dataset using validated defaults.

    Other Lance options remain available as keyword arguments. Options managed
    by :class:`WriterConfig` must be changed on ``config``.
    """

    if not isinstance(mode, WriteMode):
        raise TypeError("mode must be a WriteMode")

    conflicts = _MANAGED_WRITE_OPTIONS.intersection(lance_options)
    if conflicts:
        names = ", ".join(sorted(conflicts))
        raise TypeError(
            f"{names} must be configured through WriterConfig, not passed directly"
        )

    blocked = _BLOCKED_WRITE_OPTIONS.intersection(lance_options)
    if blocked:
        names = ", ".join(sorted(blocked))
        raise TypeError(f"{names} cannot be configured through this wrapper")

    import lance

    config = config or WriterConfig()
    data, schema = _prepare_blob_columns(data, schema, config)
    options = config.lance_write_options()
    options.update(lance_options)
    return lance.write_dataset(
        data,
        uri,
        schema=schema,
        mode=mode.value,
        **options,
    )


def open_dataset(
    uri: str | PathLike[str],
    *,
    version: int | str | None = None,
    **lance_options: Any,
) -> Any:
    """Open a Lance dataset while preserving access to reader options."""

    import lance

    if version is not None:
        lance_options["version"] = version
    return lance.dataset(uri, **lance_options)
