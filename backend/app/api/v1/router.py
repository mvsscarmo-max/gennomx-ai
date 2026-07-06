from fastapi import APIRouter

from app.api.v1 import (
    assets,
    audit,
    companies,
    corrections,
    governance,
    indications,
    jobs,
    overview,
    sources,
    targets,
    trials,
)

api_router = APIRouter()

api_router.include_router(overview.router, prefix="/overview", tags=["overview"])
api_router.include_router(assets.router, prefix="/assets", tags=["drug-assets"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(trials.router, prefix="/trials", tags=["clinical-trials"])
api_router.include_router(indications.router, prefix="/indications", tags=["indications"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(sources.router, prefix="/sources", tags=["data-sources"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["ingestion-jobs"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(corrections.router, prefix="/corrections", tags=["data-governance"])
api_router.include_router(governance.router, prefix="/governance", tags=["data-governance"])
