"""Small JSON Schema subset used to validate coordination runtime records."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import CoordinationError


class SchemaValidator:
    def __init__(self, schema_root: Path) -> None:
        self.schema_root = schema_root
        self._documents: dict[str, dict[str, Any]] = {}

    def validate(self, schema_name: str, value: Any) -> None:
        document = self._load(f"{schema_name}.schema.json")
        try:
            self._validate(document, value, document, f"{schema_name}")
        except ValueError as exc:
            raise CoordinationError("invalid-envelope", str(exc)) from exc

    def _load(self, name: str) -> dict[str, Any]:
        if name not in self._documents:
            self._documents[name] = json.loads((self.schema_root / name).read_text(encoding="utf-8"))
        return self._documents[name]

    def _resolve(self, reference: str, current: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        file_name, _, fragment = reference.partition("#")
        document = self._load(file_name) if file_name else current
        schema: Any = document
        if fragment:
            for part in fragment.lstrip("/").split("/"):
                schema = schema[part.replace("~1", "/").replace("~0", "~")]
        return schema, document

    def _validate(self, schema: dict[str, Any], value: Any, current: dict[str, Any], path: str) -> None:
        if "$ref" in schema:
            target, document = self._resolve(schema["$ref"], current)
            self._validate(target, value, document, path)
            return
        if "anyOf" in schema:
            for candidate in schema["anyOf"]:
                try:
                    self._validate(candidate, value, current, path)
                    return
                except ValueError:
                    pass
            raise ValueError(f"{path}: value does not match any allowed shape")
        if "const" in schema and value != schema["const"]:
            raise ValueError(f"{path}: expected {schema['const']!r}")
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(f"{path}: unsupported value {value!r}")

        expected = schema.get("type")
        if expected:
            expected_types = expected if isinstance(expected, list) else [expected]
            if not any(self._matches_type(name, value) for name in expected_types):
                raise ValueError(f"{path}: expected {' or '.join(expected_types)}")

        if isinstance(value, dict):
            required = schema.get("required", [])
            missing = [key for key in required if key not in value]
            if missing:
                raise ValueError(f"{path}: missing fields {', '.join(missing)}")
            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is False:
                extra = sorted(set(value) - set(properties))
                if extra:
                    raise ValueError(f"{path}: unexpected fields {', '.join(extra)}")
            for key, item in value.items():
                if key in properties:
                    self._validate(properties[key], item, current, f"{path}.{key}")
        elif isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                raise ValueError(f"{path}: too few items")
            if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
                raise ValueError(f"{path}: duplicate items")
            if "items" in schema:
                for index, item in enumerate(value):
                    self._validate(schema["items"], item, current, f"{path}[{index}]")
        elif isinstance(value, str):
            if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", len(value)):
                raise ValueError(f"{path}: invalid string length")
            if "pattern" in schema and not re.search(schema["pattern"], value):
                raise ValueError(f"{path}: invalid string format")
            if schema.get("format") == "date-time":
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise ValueError(f"{path}: invalid date-time") from exc
                if not value.endswith("Z") or parsed.utcoffset().total_seconds() != 0:
                    raise ValueError(f"{path}: date-time must be UTC with Z suffix")
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            if value < schema.get("minimum", value) or value > schema.get("maximum", value):
                raise ValueError(f"{path}: number outside allowed range")

    @staticmethod
    def _matches_type(name: str, value: Any) -> bool:
        return {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": isinstance(value, bool),
            "null": value is None,
        }.get(name, False)
