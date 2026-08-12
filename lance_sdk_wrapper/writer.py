from __future__ import annotations

from enum import Enum
from os import PathLike
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from .config import WriterConfig

if TYPE_CHECKING:
    import pyarrow as pa
    from lance import LanceDataset


class WriteMode(str, Enum):
    CREATE = "create"
    APPEND = "append"
    OVERWRITE = "overwrite"


def _configure_blob_fields(
    schema: pa.Schema,
    config: WriterConfig,
) -> pa.Schema:
    """Apply SDK Blob thresholds to fields already marked as Lance Blob v2.

    Non-Blob fields are preserved unchanged. Existing field and schema metadata
    are retained, while threshold metadata is replaced with values from
    ``WriterConfig``.

    Returns
    -------
    pyarrow.Schema
        A schema ready to use for all writes performed by ``LanceWriter``.
    """

    import lance
    import pyarrow as pa

    fields = []
    for field in schema:
        is_blob = (
            isinstance(field.type, pa.ExtensionType)
            and field.type.extension_name == "lance.blob.v2"
        )
        if is_blob:
            configured = lance.blob_field(
                field.name,
                nullable=field.nullable,
                **config.lance_blob_options(),
            )
            metadata = dict(field.metadata or {})
            metadata.update(configured.metadata or {})
            fields.append(configured.with_metadata(metadata))
        else:
            fields.append(field)

    return pa.schema(fields, metadata=schema.metadata)


class LanceWriter:
    """Public writer facade for Lance datasets."""

    def __init__(
        self,
        uri: str | PathLike[str],
        *,
        schema: Any,
        mode: WriteMode = WriteMode.CREATE,
        config: WriterConfig | None = None,
    ) -> None:
        import pyarrow as pa

        if not isinstance(schema, pa.Schema):
            raise TypeError("schema must be a pyarrow.Schema")
        if not isinstance(mode, WriteMode):
            raise TypeError("mode must be a WriteMode")

        self._uri = uri
        config = config or WriterConfig()
        config.validate()

        self._schema = _configure_blob_fields(schema, config)
        self._mode = mode
        self._write_options = config.lance_write_options()
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def write(self, data: Any) -> LanceDataset:
        """Write data and return the newly committed Lance dataset version."""

        self._ensure_open()
        result = self._write_dataset(data)
        self._mode = WriteMode.APPEND
        return result

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> Self:
        self._ensure_open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("writer is closed")

    def _write_dataset(self, data: Any) -> LanceDataset:
        import lance
        import pyarrow as pa

        if isinstance(data, (pa.Table, pa.RecordBatch)):
            data = data.cast(self._schema)
        elif isinstance(data, pa.RecordBatchReader):
            data = pa.RecordBatchReader.from_batches(
                self._schema,
                (batch.cast(self._schema) for batch in data),
            )

        return lance.write_dataset(
            data,
            self._uri,
            schema=self._schema,
            mode=self._mode.value,
            **self._write_options,
        )
