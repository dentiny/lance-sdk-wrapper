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

    options = (config or WriterConfig()).lance_write_options()
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


def blob_field(
    name: str,
    *,
    nullable: bool = True,
    config: WriterConfig | None = None,
    **lance_options: Any,
) -> Any:
    """Create a Lance Blob v2 field with the configured storage thresholds."""

    threshold_names = {"inline_size_threshold", "dedicated_size_threshold"}
    conflicts = threshold_names.intersection(lance_options)
    if conflicts:
        names = ", ".join(sorted(conflicts))
        raise TypeError(
            f"{names} must be configured through WriterConfig, not passed directly"
        )

    import lance

    options = (config or WriterConfig()).lance_blob_options()
    options.update(lance_options)
    return lance.blob_field(name, nullable=nullable, **options)
