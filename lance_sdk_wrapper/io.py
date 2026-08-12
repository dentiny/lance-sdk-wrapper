from __future__ import annotations

from enum import Enum
from os import PathLike
from typing import TYPE_CHECKING, Any

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
_BLOCKED_WRITE_OPTIONS = frozenset(
    {
        "external_blob_mode",
        "allow_external_blob_outside_bases",
    }
)


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
    options = config.lance_write_options()
    options.update(lance_options)
    return lance.write_dataset(
        data,
        uri,
        schema=schema,
        mode=mode.value,
        **options,
    )
