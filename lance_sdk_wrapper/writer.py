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


def write_dataset(
    data: Any,
    uri: str | PathLike[str],
    *,
    schema: Any | None = None,
    mode: WriteMode = WriteMode.CREATE,
    config: WriterConfig | None = None,
    **lance_options: Any,
) -> LanceDataset:
    """Write a Lance 2.3 dataset using SDK-managed defaults.

    Other Lance options remain available as keyword arguments. Options managed
    by :class:`WriterConfig` must be changed on ``config``.

    Returns
    -------
    LanceDataset
        The committed Lance dataset at its new latest version. For create and
        overwrite operations this is the newly written dataset; for append
        operations it includes both the existing and appended rows.
    """

    if not isinstance(mode, WriteMode):
        raise TypeError("mode must be a WriteMode")

    _validate_lance_options(lance_options)

    import lance

    config = config or WriterConfig()
    options = config.lance_write_options()
    options.update(lance_options)
    return lance.write_dataset(
        data,
        uri,
        schema=schema,
        mode=mode.value,
        **options,
    )


class LanceWriter:
    """Public writer facade for Lance datasets."""

    __slots__ = (
        "_closed",
        "_config",
        "_lance_options",
        "_mode",
        "_schema",
        "_uri",
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
        self._config = config or WriterConfig()
        self._config.validate()
        self._schema = schema
        self._mode = mode
        self._lance_options = dict(lance_options)
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def write(self, data: Any) -> Any:
        self._ensure_open()
        result = write_dataset(
            data,
            self._uri,
            schema=self._schema,
            mode=self._mode,
            config=self._config,
            **self._lance_options,
        )
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
