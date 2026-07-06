from __future__ import annotations

import hashlib
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

# Unbound: LLMResponse wraps either a validated Pydantic model (schema-gated
# calls) or a raw string (complete_raw), so it cannot require T <: BaseModel.
T = TypeVar("T")


class LLMRequest(BaseModel):
    """Internal request envelope for LLM calls."""

    system_prompt: str = Field(..., min_length=1)
    user_content: str = Field(..., min_length=1)
    task_name: str = Field(..., min_length=1)
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    json_schema: dict[str, Any] | None = None

    def prompt_hash(self) -> str:
        payload = json.dumps(
            {"system": self.system_prompt, "user": self.user_content},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def input_payload_hash(self) -> str:
        payload = self.model_dump_json(exclude={"system_prompt", "user_content"})
        return hashlib.sha256(payload.encode()).hexdigest()


class LLMCallMetadata(BaseModel):
    """Operational metadata recorded for every LLM call."""

    provider: str
    model: str
    task_name: str
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    prompt_hash: str = ""
    input_payload_hash: str = ""
    raw_response_hash: str = ""
    schema_name: str | None = None
    schema_valid: bool = True
    status: str = "success"
    error_type: str | None = None
    error_detail_sanitized: str | None = None
    estimated_cost_usd: float | None = None


class LLMResponse(BaseModel, Generic[T]):
    """Generic LLM response wrapping a validated Pydantic model."""

    parsed_output: T
    metadata: LLMCallMetadata

    @model_validator(mode="after")
    def ensure_schema_valid(self) -> LLMResponse[T]:
        if not self.metadata.schema_valid:
            raise ValueError("Cannot create LLMResponse with schema_valid=False")
        return self
