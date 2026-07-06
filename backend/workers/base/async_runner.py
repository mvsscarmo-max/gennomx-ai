"""Single sync-to-async boundary for Celery worker tasks."""

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def run_coroutine(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine from a synchronous Celery task.

    Celery tasks are synchronous entrypoints and must not borrow or reuse ambient event loops.
    """
    return asyncio.run(coro)
