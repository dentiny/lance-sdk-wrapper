from __future__ import annotations

from typing import Any, Final

KiB = 1024
MiB = 1024 * KiB
GiB = 1024 * MiB
DATA_STORAGE_VERSION: Final = "2.3"


class WriterConfig:
    """Mutable configuration for Lance writes."""

    __slots__ = (
        "_blob_dedicated_threshold_bytes",
        "_blob_inline_threshold_bytes",
        "_blob_pack_file_size_bytes",
        "_target_file_size_bytes",
    )

    def __init__(
        self,
        *,
        target_file_size_bytes: int = 512 * MiB,
        blob_inline_threshold_bytes: int = 2 * MiB,
        blob_dedicated_threshold_bytes: int = 32 * MiB,
        blob_pack_file_size_bytes: int = 1 * GiB,
    ) -> None:
        self._target_file_size_bytes = target_file_size_bytes
        self._blob_inline_threshold_bytes = blob_inline_threshold_bytes
        self._blob_dedicated_threshold_bytes = blob_dedicated_threshold_bytes
        self._blob_pack_file_size_bytes = blob_pack_file_size_bytes

    @property
    def target_file_size_bytes(self) -> int:
        return self._target_file_size_bytes

    @target_file_size_bytes.setter
    def target_file_size_bytes(self, value: int) -> None:
        self._target_file_size_bytes = value

    @property
    def blob_inline_threshold_bytes(self) -> int:
        return self._blob_inline_threshold_bytes

    @blob_inline_threshold_bytes.setter
    def blob_inline_threshold_bytes(self, value: int) -> None:
        self._blob_inline_threshold_bytes = value

    @property
    def blob_dedicated_threshold_bytes(self) -> int:
        return self._blob_dedicated_threshold_bytes

    @blob_dedicated_threshold_bytes.setter
    def blob_dedicated_threshold_bytes(self, value: int) -> None:
        self._blob_dedicated_threshold_bytes = value

    @property
    def blob_pack_file_size_bytes(self) -> int:
        return self._blob_pack_file_size_bytes

    @blob_pack_file_size_bytes.setter
    def blob_pack_file_size_bytes(self, value: int) -> None:
        self._blob_pack_file_size_bytes = value

    def lance_write_options(self) -> dict[str, Any]:
        """Translate this configuration to Lance ``write_dataset`` options."""

        return {
            "data_storage_version": DATA_STORAGE_VERSION,
            "max_bytes_per_file": self.target_file_size_bytes,
            "blob_pack_file_size_threshold": self.blob_pack_file_size_bytes,
        }

    def lance_blob_options(self) -> dict[str, int]:
        """Translate this configuration to Lance ``blob_field`` options."""

        return {
            "inline_size_threshold": self.blob_inline_threshold_bytes,
            "dedicated_size_threshold": self.blob_dedicated_threshold_bytes,
        }
