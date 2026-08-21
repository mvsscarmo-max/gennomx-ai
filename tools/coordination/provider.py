"""Provider-neutral executable coordination contract."""
from __future__ import annotations

import inspect
from typing import Any, Protocol

from .errors import CoordinationError


class CoordinationProvider(Protocol):
    SUPPORTED_OPERATIONS: dict[str, str]

    def invoke(self, operation: str, payload: dict[str, Any]) -> Any: ...

    def discover_capabilities(self) -> dict[str, list[str]]: ...


def invoke_operation(provider: CoordinationProvider, operation: str, payload: dict[str, Any]) -> Any:
    method_name = provider.SUPPORTED_OPERATIONS.get(operation)
    if method_name is None:
        raise CoordinationError(
            "capability-not-supported-by-provider",
            f"operation is not supported by this provider: {operation}",
        )
    method = getattr(provider, method_name)
    try:
        inspect.signature(method).bind(**payload)
    except TypeError as exc:
        raise CoordinationError("invalid-envelope", f"invalid payload for {operation}: {exc}") from exc
    return method(**payload)
