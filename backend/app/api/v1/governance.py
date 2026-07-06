import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_admin
from app.database import get_db

router = APIRouter()


class LegalHoldCreate(BaseModel):
    resource_type: str = Field(min_length=1, max_length=100, pattern=r"^[a-z_]+$")
    resource_id: str | None = Field(None, max_length=500)
    reason: str = Field(min_length=10, max_length=4000)
    expires_at: datetime | None = None


class RetentionRun(BaseModel):
    dry_run: bool = True
    batch_size: int = Field(1000, ge=1, le=10_000)


class ScraperDomainPolicy(BaseModel):
    owner: str = Field(min_length=2, max_length=200)
    purpose: str = Field(min_length=10, max_length=2000)
    legal_basis: str = Field(min_length=5, max_length=2000)
    terms_reviewed_at: datetime
    robots_policy: str = Field(pattern=r"^(allowed|not_applicable|blocked)$")
    requests_per_minute: int = Field(10, ge=1, le=600)
    max_concurrency: int = Field(1, ge=1, le=20)
    allowed_hosts: list[str] = Field(default_factory=list, max_length=20)
    active: bool = False
    kill_switch: bool = True

    @field_validator("allowed_hosts")
    @classmethod
    def normalize_hosts(cls, value: list[str]) -> list[str]:
        normalized = []
        for host in value:
            clean = host.casefold().strip().rstrip(".")
            if not clean or "/" in clean or ":" in clean:
                raise ValueError("allowed_hosts must contain hostnames only")
            normalized.append(clean)
        return sorted(set(normalized))

    @model_validator(mode="after")
    def activation_requires_approved_controls(self):
        if self.active and self.robots_policy not in {"allowed", "not_applicable"}:
            raise ValueError("active scraper domains require an approved robots policy")
        if self.active and self.kill_switch:
            raise ValueError("active scraper domains cannot have the kill switch enabled")
        return self


@router.get("/status")
async def governance_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    domains = (
        (
            await db.execute(
                text("""
                SELECT domain, owner, robots_policy, requests_per_minute,
                       max_concurrency, active, kill_switch, updated_at
                FROM scraper_domain_policies ORDER BY domain
            """)
            )
        )
        .mappings()
        .all()
    )
    policies = (
        (
            await db.execute(
                text("""
                SELECT resource_type, hot_days, archive_after_days, delete_after_days,
                       archive_destination, policy_version, active
                FROM retention_policies ORDER BY resource_type
            """)
            )
        )
        .mappings()
        .all()
    )
    holds = (
        (
            await db.execute(
                text("""
                SELECT id::text, resource_type, resource_id, reason, starts_at, expires_at
                FROM legal_holds
                WHERE released_at IS NULL AND (expires_at IS NULL OR expires_at > now())
                ORDER BY starts_at DESC LIMIT 100
            """)
            )
        )
        .mappings()
        .all()
    )
    manifests = (
        (
            await db.execute(
                text("""
                SELECT id::text, resource_type, record_count, status, dry_run,
                       storage_uri, created_at
                FROM archive_manifests ORDER BY created_at DESC LIMIT 20
            """)
            )
        )
        .mappings()
        .all()
    )
    return {
        "scraper_domains": [dict(row) for row in domains],
        "retention_policies": [dict(row) for row in policies],
        "active_legal_holds": [dict(row) for row in holds],
        "archive_manifests": [dict(row) for row in manifests],
    }


@router.post("/legal-holds", status_code=201)
async def create_legal_hold(
    payload: LegalHoldCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    row = (
        await db.execute(
            text("""
                INSERT INTO legal_holds (
                    id, resource_type, resource_id, reason, created_by,
                    starts_at, expires_at, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :resource_type, :resource_id, :reason,
                    :created_by, now(), :expires_at, now(), now()
                ) RETURNING id::text
            """),
            {**payload.model_dump(), "created_by": user.user_id},
        )
    ).first()
    assert row is not None  # INSERT ... RETURNING always yields a row on success
    return {"id": row[0], "status": "active"}


@router.post("/legal-holds/{hold_id}/release")
async def release_legal_hold(
    hold_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    row = (
        await db.execute(
            text("""
                UPDATE legal_holds SET released_at = now(), updated_at = now()
                WHERE id = :id AND released_at IS NULL RETURNING id::text
            """),
            {"id": str(hold_id)},
        )
    ).first()
    if not row:
        return {"id": str(hold_id), "status": "not_active"}
    return {"id": row[0], "status": "released"}


@router.post("/retention/run", status_code=202)
async def trigger_retention(
    payload: RetentionRun,
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    from workers.tasks.retention import run_retention_cycle

    task = run_retention_cycle.apply_async(
        kwargs={"dry_run": payload.dry_run, "batch_size": payload.batch_size},
        queue="process",
    )
    return {"task_id": task.id, "status": "queued", "dry_run": payload.dry_run}


@router.put("/scraper-domains/{domain}")
async def upsert_scraper_domain(
    domain: str,
    payload: ScraperDomainPolicy,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    normalized_domain = domain.casefold().strip().rstrip(".")
    if not normalized_domain or "/" in normalized_domain or ":" in normalized_domain:
        raise HTTPException(status_code=422, detail="domain must be a hostname")
    values = payload.model_dump(exclude={"allowed_hosts"})
    await db.execute(
        text("""
            INSERT INTO scraper_domain_policies (
                id, domain, owner, purpose, legal_basis, terms_reviewed_at,
                robots_policy, requests_per_minute, max_concurrency,
                allowed_schemes, allowed_hosts, kill_switch, active,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :domain, :owner, :purpose, :legal_basis,
                :terms_reviewed_at, :robots_policy, :requests_per_minute,
                :max_concurrency, '["https"]'::jsonb, CAST(:allowed_hosts AS JSONB),
                :kill_switch, :active, now(), now()
            ) ON CONFLICT (domain) DO UPDATE SET
                owner = EXCLUDED.owner, purpose = EXCLUDED.purpose,
                legal_basis = EXCLUDED.legal_basis,
                terms_reviewed_at = EXCLUDED.terms_reviewed_at,
                robots_policy = EXCLUDED.robots_policy,
                requests_per_minute = EXCLUDED.requests_per_minute,
                max_concurrency = EXCLUDED.max_concurrency,
                allowed_hosts = EXCLUDED.allowed_hosts,
                kill_switch = EXCLUDED.kill_switch, active = EXCLUDED.active,
                updated_at = now()
        """),
        {
            "domain": normalized_domain,
            "allowed_hosts": json.dumps(payload.allowed_hosts),
            **values,
        },
    )
    return {
        "domain": normalized_domain,
        "active": payload.active,
        "kill_switch": payload.kill_switch,
    }


@router.post("/scraper-domains/{domain}/pause")
async def pause_scraper_domain(
    domain: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    normalized_domain = domain.casefold().strip().rstrip(".")
    await db.execute(
        text("""
            UPDATE scraper_domain_policies
            SET kill_switch = true, active = false, updated_at = now()
            WHERE domain = :domain
        """),
        {"domain": normalized_domain},
    )
    return {"domain": normalized_domain, "status": "paused"}
