"""Parameter unwrapping utilities for MCP tool arguments."""

from typing import Any


_MISSING = object()


def unwrap(value: Any, *keys: str, default: Any = _MISSING) -> Any:  # type: ignore[assignment]
    """Unwrap a value from a dict by trying multiple keys.

    Some MCP clients wrap parameters in nested dicts with varying keys.
    This helper tries each key in order and returns the first match.

    Args:
        value: The value to unwrap. If not a dict, returns as-is.
        *keys: Keys to try in order.
        default: Default value if no key matches. If not provided,
            returns the string representation of the dict.

    Returns:
        The unwrapped value or default.
    """
    if not isinstance(value, dict):
        return value
    for key in keys:
        if key in value:
            return value[key]
    if default is _MISSING:
        return str(value)
    return default
