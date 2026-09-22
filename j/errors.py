"""Exception types shared across the j package."""

__all__ = ["ConfigError", "JError", "UsageError"]


class JError(Exception):
    """Base error for all j failures."""


class ConfigError(JError):
    """A theme file cannot be parsed or a reference inside it is invalid."""

    def __init__(self, message: str, path: str = "", line: int | None = None):
        self.path = path
        self.line = line
        where = f"{path}:{line}" if path and line is not None else path
        super().__init__(f"{where}: {message}" if where else message)


class UsageError(JError):
    """The user passed invalid command line input."""
