from __future__ import annotations

from os import PathLike
from typing import Any

from typing_extensions import Self

from .config import WriterConfig
from .io import WriteMode, write_dataset


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
        if not isinstance(mode, WriteMode):
            raise TypeError("mode must be a WriteMode")

        self._uri = uri
        self._config = config or WriterConfig()
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
