"""Explicit control plane for the ingestible source allowlist."""

from typing import Any

RUNNABLE_SOURCE_SLUGS = frozenset(
    {
        "clinicaltrials_gov",
        "pubmed",
        "openfda",
        "dailymed",
        "open_targets",
        "ema",
    }
)


def schedule_ingestion(source_slug: str, **kwargs: Any):
    """Queue a supported ingestion task without dynamic imports or task names."""
    if source_slug == "clinicaltrials_gov":
        from workers.tasks.ingest import run_clinicaltrials_ingest

        return run_clinicaltrials_ingest.delay(**kwargs)
    if source_slug == "pubmed":
        from workers.tasks.ingest import run_pubmed_ingest

        return run_pubmed_ingest.delay(**kwargs)
    if source_slug == "openfda":
        from workers.tasks.ingest import run_openfda_ingest

        return run_openfda_ingest.delay(**kwargs)
    if source_slug == "dailymed":
        from workers.tasks.ingest import run_dailymed_ingest

        return run_dailymed_ingest.delay(**kwargs)
    if source_slug == "open_targets":
        from workers.tasks.ingest import run_opentargets_ingest

        return run_opentargets_ingest.delay(**kwargs)
    if source_slug == "ema":
        from workers.tasks.ingest import run_ema_ingest

        return run_ema_ingest.delay(**kwargs)
    raise ValueError(f"Unsupported ingestion source: {source_slug}")
