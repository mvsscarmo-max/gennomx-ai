"""Celery tasks for data source ingestion."""

from celery import shared_task

from app.config import get_settings
from app.database_security import assert_database_role
from workers.base.async_runner import run_coroutine
from workers.base.connector import ConnectorResult
from workers.base.job_tracker import JobTracker
from workers.persistence.assets import (  # noqa: F401
    PHASE_RANK,
    THERAPEUTIC_INTERVENTION_TYPES,
    _clean_asset_name,
    _extract_asset_candidates,
    _insert_asset_evidence_snippet,
    _merge_unique,
    _select_development_stage,
    _upsert_drug_assets_from_trial,
)
from workers.persistence.common import (  # noqa: F401
    DECISION_ENGINE,
    FATAL_CONNECTOR_ERRORS,
    _get_async_session,
    _get_data_source_id,
    _get_last_successful_run,
    _has_fatal_connector_error,
    _record_data_conflict,
)
from workers.persistence.evidence import (  # noqa: F401
    _insert_evidence_snippet,
    _insert_publication_evidence_snippet,
    _insert_trial_field_evidence,
)
from workers.persistence.publications import (  # noqa: F401
    PUBLICATION_JSONB_FIELDS,
    _insert_publication,
    _persist_publications,
    _resolve_nct_links,
    _stage_publication_payloads,
    _update_publication,
    _upsert_publication_source_document,
)
from workers.persistence.regulatory import (  # noqa: F401
    REGULATORY_JSONB_FIELDS,
    _insert_regulatory_approval,
    _persist_regulatory_approvals,
    _resolve_drug_asset_id,
    _stage_regulatory_payloads,
    _update_regulatory_approval,
    _upsert_regulatory_source_document,
)
from workers.persistence.targets import (  # noqa: F401
    TARGET_JSONB_FIELDS,
    _insert_target,
    _persist_targets,
    _update_target,
    _upsert_target_source_document,
)
from workers.persistence.trials import (  # noqa: F401
    TRIAL_JSONB_FIELDS,
    _insert_trial,
    _insert_trial_assertions,
    _persist_trials,
    _stage_trial_payloads,
    _sync_trial_asset_links,
    _trial_assertion_expiry,
    _update_trial,
    _upsert_source_document,
    link_existing_trials_to_assets,
)

settings = get_settings()


@shared_task(
    bind=True, name="workers.tasks.ingest.run_pubmed_ingest", queue="ingest", max_retries=3
)
def run_pubmed_ingest(
    self,
    job_type: str = "incremental",
    query: str | None = None,
    max_records: int | None = None,
):
    """Ingest publications from PubMed E-utilities API."""
    from workers.connectors.pubmed.connector import PubMedConnector
    from workers.connectors.pubmed.normalizer import PubMedNormalizer

    connector = PubMedConnector()
    normalizer = PubMedNormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job("pubmed", job_type, celery_task_id=self.request.id)
            await tracker.start_job(job_id)

            try:
                updated_since = await _get_last_successful_run(db, "pubmed")
                persisted_counts = {"inserted": 0, "updated": 0, "rejected": 0, "skipped": 0}

                async def persist_page(payloads: list[dict]) -> None:
                    page_result = ConnectorResult("pubmed")
                    page_result.raw_payloads = payloads
                    await _persist_publications(db, page_result, normalizer)
                    persisted_counts["inserted"] += page_result.records_inserted
                    persisted_counts["updated"] += page_result.records_updated
                    persisted_counts["rejected"] += page_result.records_rejected
                    persisted_counts["skipped"] += page_result.records_skipped

                result = await connector.run(
                    job_type=job_type,
                    query=query,
                    max_records=max_records,
                    updated_since=updated_since,
                    page_handler=persist_page,
                )
                result.records_inserted += persisted_counts["inserted"]
                result.records_updated += persisted_counts["updated"]
                result.records_rejected += persisted_counts["rejected"]
                result.records_skipped += persisted_counts["skipped"]
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])
                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("pubmed")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc


@shared_task(
    bind=True, name="workers.tasks.ingest.run_clinicaltrials_ingest", queue="ingest", max_retries=3
)
def run_clinicaltrials_ingest(
    self,
    job_type: str = "incremental",
    query: str | None = None,
    conditions: list | None = None,
    interventions: list | None = None,
    max_records: int | None = None,
):
    """Ingest clinical trials from ClinicalTrials.gov API v2."""
    from workers.connectors.clinicaltrials.connector import ClinicalTrialsConnector
    from workers.connectors.clinicaltrials.normalizer import ClinicalTrialsNormalizer

    connector = ClinicalTrialsConnector()
    normalizer = ClinicalTrialsNormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job(
                "clinicaltrials_gov", job_type, celery_task_id=self.request.id
            )
            await tracker.start_job(job_id)

            try:
                updated_since = await _get_last_successful_run(db, "clinicaltrials_gov")
                persisted_counts = {"inserted": 0, "updated": 0, "rejected": 0, "skipped": 0}

                async def persist_page(payloads: list[dict]) -> None:
                    page_result = ConnectorResult("clinicaltrials_gov")
                    page_result.raw_payloads = payloads
                    await _persist_trials(db, page_result, normalizer)
                    persisted_counts["inserted"] += page_result.records_inserted
                    persisted_counts["updated"] += page_result.records_updated
                    persisted_counts["rejected"] += page_result.records_rejected
                    persisted_counts["skipped"] += page_result.records_skipped

                result = await connector.run(
                    job_type=job_type,
                    query=query,
                    conditions=conditions,
                    interventions=interventions,
                    max_records=max_records,
                    updated_since=updated_since,
                    page_handler=persist_page,
                )
                result.records_inserted += persisted_counts["inserted"]
                result.records_updated += persisted_counts["updated"]
                result.records_rejected += persisted_counts["rejected"]
                result.records_skipped += persisted_counts["skipped"]
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])
                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("clinicaltrials_gov")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc


@shared_task(
    bind=True, name="workers.tasks.ingest.run_openfda_ingest", queue="ingest", max_retries=3
)
def run_openfda_ingest(self, job_type: str = "incremental", max_records: int | None = None):
    """Ingest drug approvals from the openFDA Drugs@FDA (drugsfda) API."""
    from workers.connectors.openfda.connector import OpenFDAConnector
    from workers.connectors.openfda.normalizer import OpenFDANormalizer

    connector = OpenFDAConnector()
    normalizer = OpenFDANormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job("openfda", job_type, celery_task_id=self.request.id)
            await tracker.start_job(job_id)

            try:
                persisted_counts = {"inserted": 0, "updated": 0, "rejected": 0, "skipped": 0}

                async def persist_page(payloads: list[dict]) -> None:
                    page_result = ConnectorResult("openfda")
                    page_result.raw_payloads = payloads
                    await _persist_regulatory_approvals(db, page_result, normalizer, "openfda")
                    persisted_counts["inserted"] += page_result.records_inserted
                    persisted_counts["updated"] += page_result.records_updated
                    persisted_counts["rejected"] += page_result.records_rejected
                    persisted_counts["skipped"] += page_result.records_skipped

                result = await connector.run(
                    job_type=job_type,
                    max_records=max_records,
                    page_handler=persist_page,
                )
                result.records_inserted += persisted_counts["inserted"]
                result.records_updated += persisted_counts["updated"]
                result.records_rejected += persisted_counts["rejected"]
                result.records_skipped += persisted_counts["skipped"]
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])
                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("openfda")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc


@shared_task(
    bind=True, name="workers.tasks.ingest.run_dailymed_ingest", queue="ingest", max_retries=3
)
def run_dailymed_ingest(self, job_type: str = "incremental", max_records: int | None = None):
    """Ingest structured product labels (SPL) from DailyMed."""
    from workers.connectors.dailymed.connector import DailyMedConnector
    from workers.connectors.dailymed.normalizer import DailyMedNormalizer

    connector = DailyMedConnector()
    normalizer = DailyMedNormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job("dailymed", job_type, celery_task_id=self.request.id)
            await tracker.start_job(job_id)

            try:
                persisted_counts = {"inserted": 0, "updated": 0, "rejected": 0, "skipped": 0}

                async def persist_page(payloads: list[dict]) -> None:
                    page_result = ConnectorResult("dailymed")
                    page_result.raw_payloads = payloads
                    await _persist_regulatory_approvals(db, page_result, normalizer, "dailymed")
                    persisted_counts["inserted"] += page_result.records_inserted
                    persisted_counts["updated"] += page_result.records_updated
                    persisted_counts["rejected"] += page_result.records_rejected
                    persisted_counts["skipped"] += page_result.records_skipped

                result = await connector.run(
                    job_type=job_type,
                    max_records=max_records,
                    page_handler=persist_page,
                )
                result.records_inserted += persisted_counts["inserted"]
                result.records_updated += persisted_counts["updated"]
                result.records_rejected += persisted_counts["rejected"]
                result.records_skipped += persisted_counts["skipped"]
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])
                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("dailymed")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc


@shared_task(
    bind=True, name="workers.tasks.ingest.run_opentargets_ingest", queue="ingest", max_retries=3
)
def run_opentargets_ingest(self, job_type: str = "incremental", max_records: int | None = None):
    """Ingest biological-target / disease-association records from Open Targets."""
    from workers.connectors.opentargets.connector import OpenTargetsConnector
    from workers.connectors.opentargets.normalizer import OpenTargetsNormalizer

    connector = OpenTargetsConnector()
    normalizer = OpenTargetsNormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job(
                "open_targets", job_type, celery_task_id=self.request.id
            )
            await tracker.start_job(job_id)

            try:
                persisted_counts = {"inserted": 0, "updated": 0, "rejected": 0, "skipped": 0}

                async def persist_page(payloads: list[dict]) -> None:
                    page_result = ConnectorResult("open_targets")
                    page_result.raw_payloads = payloads
                    await _persist_targets(db, page_result, normalizer, "open_targets")
                    persisted_counts["inserted"] += page_result.records_inserted
                    persisted_counts["updated"] += page_result.records_updated
                    persisted_counts["rejected"] += page_result.records_rejected
                    persisted_counts["skipped"] += page_result.records_skipped

                result = await connector.run(
                    job_type=job_type,
                    max_records=max_records,
                    page_handler=persist_page,
                )
                result.records_inserted += persisted_counts["inserted"]
                result.records_updated += persisted_counts["updated"]
                result.records_rejected += persisted_counts["rejected"]
                result.records_skipped += persisted_counts["skipped"]
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])
                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("open_targets")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc


@shared_task(bind=True, name="workers.tasks.ingest.run_ema_ingest", queue="ingest", max_retries=3)
def run_ema_ingest(self, job_type: str = "incremental", max_records: int | None = None):
    """Ingest medicine authorisation records from the EMA official medicines export."""
    from workers.connectors.ema.connector import EMAConnector
    from workers.connectors.ema.normalizer import EMANormalizer

    connector = EMAConnector()
    normalizer = EMANormalizer()

    async def _run():
        async_session = _get_async_session()
        async with async_session() as db:
            if settings.is_production:
                await assert_database_role(db, "gennomx_worker")
            tracker = JobTracker(db)
            job_id = await tracker.create_job("ema", job_type, celery_task_id=self.request.id)
            await tracker.start_job(job_id)

            try:
                result = await connector.run(job_type=job_type, max_records=max_records)
                if _has_fatal_connector_error(result):
                    raise RuntimeError(result.errors[0]["message"])

                await _persist_regulatory_approvals(db, result, normalizer, "ema")

                await tracker.complete_job(job_id, result)
                return {
                    "job_id": job_id,
                    "status": "success" if result.success else "partial",
                    "inserted": result.records_inserted,
                }

            except Exception as e:
                fail_result = ConnectorResult("ema")
                fail_result.add_error("task_error", str(e))
                fail_result.finish()
                await tracker.complete_job(job_id, fail_result)
                raise

    try:
        return run_coroutine(_run())
    except Exception as exc:
        countdown = min(300, 2**self.request.retries * 30)
        raise self.retry(exc=exc, countdown=countdown) from exc
