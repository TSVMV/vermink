"""Exception types shared across the vermink package."""

__all__ = ["ConfigError", "UsageError", "VerminkError"]


class VerminkError(Exception):
    """Base error for all vermink failures."""


class ConfigError(VerminkError):
    """A theme file cannot be parsed or a reference inside it is invalid."""

    def __init__(self, message: str, path: str = "", line: int | None = None):
        self.path = path
        self.line = line
        where = f"{path}:{line}" if path and line is not None else path
        super().__init__(f"{where}: {message}" if where else message)


class UsageError(VerminkError):
    """The user passed invalid command line input."""
