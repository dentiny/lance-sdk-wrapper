from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from os import PathLike
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from .config import WriterConfig

if TYPE_CHECKING:
    from lance import LanceDataset


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
_BLOCKED_WRITE_OPTIONS = frozenset({"external_blob_mode"})


def _validate_lance_options(lance_options: Mapping[str, Any]) -> None:
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


class LanceWriter:
    """Public writer facade for Lance datasets."""

    __slots__ = (
        "_closed",
        "_mode",
        "_schema",
        "_uri",
        "_write_options",
    )

    def __init__(
        self,
        uri: str | PathLike[str],
        *,
        schema: Any,
        mode: WriteMode = WriteMode.CREATE,
        config: WriterConfig | None = None,
        **lance_options: Any,
    ) -> None:
        import pyarrow as pa

        if not isinstance(schema, pa.Schema):
            raise TypeError("schema must be a pyarrow.Schema")
        if not isinstance(mode, WriteMode):
            raise TypeError("mode must be a WriteMode")
        _validate_lance_options(lance_options)

        self._uri = uri
        config = config or WriterConfig()
        config.validate()
        self._schema = schema
        self._mode = mode
        self._write_options = config.lance_write_options()
        self._write_options.update(lance_options)
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

        return lance.write_dataset(
            data,
            self._uri,
            schema=self._schema,
            mode=self._mode.value,
            **self._write_options,
        )
