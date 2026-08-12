from __future__ import annotations

from typing import Any, Final

KiB = 1024
MiB = 1024 * KiB
GiB = 1024 * MiB
DATA_STORAGE_VERSION: Final = "2.3"


class WriterConfig:
    """Mutable configuration for Lance writes."""

    def __init__(
        self,
        *,
        target_file_size_bytes: int = 512 * MiB,
        blob_inline_threshold_bytes: int = 2 * MiB,
        blob_dedicated_threshold_bytes: int = 32 * MiB,
        blob_pack_file_size_bytes: int = 1 * GiB,
        connect_timeout_seconds: int = 5,
        request_timeout_seconds: int = 30,
        client_max_retries: int = 3,
        client_retry_timeout_seconds: int = 180,
    ) -> None:
        self._target_file_size_bytes = target_file_size_bytes
        self._blob_inline_threshold_bytes = blob_inline_threshold_bytes
        self._blob_dedicated_threshold_bytes = blob_dedicated_threshold_bytes
        self._blob_pack_file_size_bytes = blob_pack_file_size_bytes
        self._connect_timeout_seconds = connect_timeout_seconds
        self._request_timeout_seconds = request_timeout_seconds
        self._client_max_retries = client_max_retries
        self._client_retry_timeout_seconds = client_retry_timeout_seconds

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

    @property
    def connect_timeout_seconds(self) -> int:
        return self._connect_timeout_seconds

    @connect_timeout_seconds.setter
    def connect_timeout_seconds(self, value: int) -> None:
        self._connect_timeout_seconds = value

    @property
    def request_timeout_seconds(self) -> int:
        return self._request_timeout_seconds

    @request_timeout_seconds.setter
    def request_timeout_seconds(self, value: int) -> None:
        self._request_timeout_seconds = value

    @property
    def client_max_retries(self) -> int:
        return self._client_max_retries

    @client_max_retries.setter
    def client_max_retries(self, value: int) -> None:
        self._client_max_retries = value

    @property
    def client_retry_timeout_seconds(self) -> int:
        return self._client_retry_timeout_seconds

    @client_retry_timeout_seconds.setter
    def client_retry_timeout_seconds(self, value: int) -> None:
        self._client_retry_timeout_seconds = value

    def validate(self) -> None:
        """Validate this configuration before creating a writer."""

        positive_integer_fields = {
            "target_file_size_bytes": self.target_file_size_bytes,
            "blob_inline_threshold_bytes": self.blob_inline_threshold_bytes,
            "blob_dedicated_threshold_bytes": self.blob_dedicated_threshold_bytes,
            "blob_pack_file_size_bytes": self.blob_pack_file_size_bytes,
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "request_timeout_seconds": self.request_timeout_seconds,
            "client_retry_timeout_seconds": self.client_retry_timeout_seconds,
        }
        for name, value in positive_integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

        if self.blob_inline_threshold_bytes >= self.blob_dedicated_threshold_bytes:
            raise ValueError(
                "blob_inline_threshold_bytes must be smaller than "
                "blob_dedicated_threshold_bytes"
            )

        if (
            isinstance(self.client_max_retries, bool)
            or not isinstance(self.client_max_retries, int)
            or self.client_max_retries < 0
        ):
            raise ValueError("client_max_retries must be a non-negative integer")

    def lance_write_options(self) -> dict[str, Any]:
        """Translate this configuration to Lance ``write_dataset`` options."""

        return {
            "data_storage_version": DATA_STORAGE_VERSION,
            "max_bytes_per_file": self.target_file_size_bytes,
            "blob_pack_file_size_threshold": self.blob_pack_file_size_bytes,
            "storage_options": {
                "connect_timeout": f"{self.connect_timeout_seconds}s",
                "request_timeout": f"{self.request_timeout_seconds}s",
                "client_max_retries": str(self.client_max_retries),
                "client_retry_timeout": str(self.client_retry_timeout_seconds),
            },
        }

    def lance_blob_options(self) -> dict[str, int]:
        """Translate this configuration to Lance ``blob_field`` options."""

        return {
            "inline_size_threshold": self.blob_inline_threshold_bytes,
            "dedicated_size_threshold": self.blob_dedicated_threshold_bytes,
        }
