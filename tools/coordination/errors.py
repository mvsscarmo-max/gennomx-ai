"""Canonical coordination failures."""
from __future__ import annotations


class CoordinationError(Exception):
    def __init__(self, code: str, message: str, *, reference: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.reference = reference

    def as_dict(self) -> dict[str, str]:
        result = {"error": self.code, "message": str(self)}
        if self.reference:
            result["reference"] = self.reference
        return result
