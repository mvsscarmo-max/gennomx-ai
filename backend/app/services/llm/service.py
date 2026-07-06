from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.config import get_settings
from app.services.llm.client import LLMClient
from app.services.llm.errors import LLMConfigurationError
from app.services.llm.schemas import LLMRequest, LLMResponse

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Internal LLM service — configuration, safety, and schema-gated calls.

    Responsibilities:
    - Validate that network calls are enabled and configuration is complete.
    - Build LLMClient for the configured provider (currently only opencode).
    - Accept a Pydantic output schema and validate every response.
    - Return LLMResponse[T] with metadata; never persist data directly.
    - Sanitise error information before it leaves the service.

    The service does NOT write to the database. Audit logging is the caller's
    responsibility (typically a Celery worker that bridges llm_call_logs).
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: LLMClient | None = None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> LLMService:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @property
    def enabled(self) -> bool:
        return self._settings.LLM_ENABLE_NETWORK_CALLS

    @property
    def provider(self) -> str:
        return self._settings.LLM_PROVIDER

    def _get_client(self) -> LLMClient:
        if self._client is not None:
            return self._client
        if not self._settings.LLM_ENABLE_NETWORK_CALLS:
            raise LLMConfigurationError(
                "LLM network calls are disabled. Set LLM_ENABLE_NETWORK_CALLS=true."
            )
        self._client = LLMClient(
            base_url=self._settings.OPENCODE_BASE_URL,
            api_key=self._settings.OPENCODE_API_KEY,
            timeout_seconds=self._settings.LLM_TIMEOUT_SECONDS,
        )
        return self._client

    def complete_with_schema(
        self,
        system_prompt: str,
        user_content: str,
        task_name: str,
        schema_class: type[T],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse[T]:
        if not system_prompt or not user_content:
            raise LLMConfigurationError("system_prompt and user_content are required")

        request = LLMRequest(
            system_prompt=system_prompt,
            user_content=user_content,
            task_name=task_name,
            model=model or self._settings.LLM_MODEL_PREMIUM,
            temperature=(
                temperature if temperature is not None else self._settings.LLM_TEMPERATURE
            ),
            max_tokens=max_tokens or self._settings.LLM_MAX_TOKENS,
            json_schema=schema_class.model_json_schema(),
        )

        client = self._get_client()
        parsed, metadata = client.complete(request, schema_class=schema_class)
        return LLMResponse[T](parsed_output=parsed, metadata=metadata)

    def complete_raw(
        self,
        system_prompt: str,
        user_content: str,
        task_name: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse[str]:
        if not system_prompt or not user_content:
            raise LLMConfigurationError("system_prompt and user_content are required")

        request = LLMRequest(
            system_prompt=system_prompt,
            user_content=user_content,
            task_name=task_name,
            model=model or self._settings.LLM_MODEL_PREMIUM,
            temperature=(
                temperature if temperature is not None else self._settings.LLM_TEMPERATURE
            ),
            max_tokens=max_tokens or self._settings.LLM_MAX_TOKENS,
        )

        client = self._get_client()
        raw: str
        raw, metadata = client.complete(request, schema_class=None)
        return LLMResponse[str](parsed_output=raw, metadata=metadata)
