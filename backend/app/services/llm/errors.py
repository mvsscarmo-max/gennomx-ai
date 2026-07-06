class LLMConfigurationError(Exception):
    """LLM provider is misconfigured (missing key, URL, or unsupported provider)."""


class LLMProviderError(Exception):
    """The LLM provider returned an error response (4xx/5xx)."""


class LLMTimeoutError(Exception):
    """The LLM provider did not respond within the configured timeout."""


class LLMSchemaValidationError(Exception):
    """The LLM response failed Pydantic schema validation."""
