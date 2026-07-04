import asyncio
from concurrent.futures import Future
from contextlib import suppress
from typing import Any, Literal, Protocol

LogLevel = Literal["debug", "info", "warning", "error"]


class LogSink(Protocol):
    """Subset of the FastMCP context logging API used throughout the package."""

    async def debug(self, message: str) -> None:
        ...

    async def info(self, message: str) -> None:
        ...

    async def warning(self, message: str) -> None:
        ...

    async def error(self, message: str) -> None:
        ...


async def log_message(logger: LogSink | None, level: LogLevel, message: str) -> None:
    """Log only when a context/logger was provided by the caller."""
    if logger is None:
        return
    await getattr(logger, level)(message)


class ThreadLogBridge:
    """Forward synchronous Selenium thread logs onto the async MCP event loop."""

    def __init__(
        self,
        logger: LogSink | None,
        loop: asyncio.AbstractEventLoop | None,
    ) -> None:
        self._logger = logger
        self._loop = loop

    def debug(self, message: str) -> None:
        self._submit("debug", message)

    def info(self, message: str) -> None:
        self._submit("info", message)

    def warning(self, message: str) -> None:
        self._submit("warning", message)

    def error(self, message: str) -> None:
        self._submit("error", message)

    def _submit(self, level: LogLevel, message: str) -> None:
        if self._logger is None or self._loop is None or self._loop.is_closed():
            return

        coroutine = getattr(self._logger, level)(message)
        try:
            future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        except RuntimeError:
            coroutine.close()
            return
        future.add_done_callback(ignore_logging_error)


def ignore_logging_error(future: Future[Any]) -> None:
    """Keep best-effort logging failures from breaking a browser fetch."""
    with suppress(Exception):
        future.result()
