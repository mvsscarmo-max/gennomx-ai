from __future__ import annotations

import hashlib
import json
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from app.config import get_settings
from app.services.llm.errors import (
    LLMConfigurationError,
    LLMProviderError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from app.services.llm.schemas import LLMCallMetadata, LLMRequest

T = TypeVar("T", bound=BaseModel)


def _hash_raw(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class LLMClient:
    """Thin HTTP adapter for OpenAI-compatible chat completions API.

    Uses httpx. Does NOT persist data — the caller (LLMService) owns
    audit logging and persistence decisions.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: int = 60,
    ) -> None:
        if not base_url:
            raise LLMConfigurationError("OPENCODE_BASE_URL is not configured")
        if not api_key:
            raise LLMConfigurationError("OPENCODE_API_KEY is not configured")
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
        )
        self._settings = get_settings()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LLMClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_content},
        ]
        payload: dict[str, Any] = {
            "model": request.model or self._settings.LLM_MODEL_PREMIUM,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.task_name.replace(" ", "_"),
                    "strict": True,
                    "schema": request.json_schema,
                },
            }
        return payload

    def complete(
        self,
        request: LLMRequest,
        schema_class: type[T] | None = None,
    ) -> tuple[T, LLMCallMetadata]:
        """Send a chat completion request and optionally validate against a Pydantic schema.

        Returns (parsed_output, metadata). Validation errors are raised as
        LLMSchemaValidationError so the pipeline can decide whether to retry or skip.
        """
        if request.system_prompt == request.user_content:
            raise LLMConfigurationError("System prompt and user content must not be identical")

        payload = self._build_payload(request)
        start = time.monotonic()
        raw_response = ""

        try:
            resp = self._client.post("/v1/chat/completions", json=payload)
        except httpx.TimeoutException as exc:
            elapsed = (time.monotonic() - start) * 1000
            raise LLMTimeoutError(f"LLM call timed out after {elapsed:.0f}ms") from exc

        elapsed_ms = (time.monotonic() - start) * 1000

        if resp.status_code >= 400:
            error_body = resp.text[:500]
            raise LLMProviderError(f"Provider returned {resp.status_code}: {error_body}")

        body = resp.json()
        raw_response = json.dumps(body, sort_keys=True)

        choice = body.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        usage = body.get("usage", {})

        metadata = LLMCallMetadata(
            provider=self._settings.LLM_PROVIDER,
            model=request.model or self._settings.LLM_MODEL_PREMIUM,
            task_name=request.task_name,
            latency_ms=elapsed_ms,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            prompt_hash=request.prompt_hash(),
            input_payload_hash=request.input_payload_hash(),
            raw_response_hash=_hash_raw(raw_response),
            schema_name=schema_class.__name__ if schema_class else None,
            schema_valid=True,
            status="success",
        )

        if schema_class is not None:
            try:
                parsed = schema_class.model_validate_json(content)
            except Exception as exc:
                metadata.schema_valid = False
                metadata.status = "schema_invalid"
                metadata.error_type = type(exc).__name__
                metadata.error_detail_sanitized = "LLM output failed Pydantic schema validation"
                raise LLMSchemaValidationError(
                    f"Schema validation failed for {schema_class.__name__}: {exc}"
                ) from exc
            return parsed, metadata

        return content, metadata  # type: ignore[return-value]
