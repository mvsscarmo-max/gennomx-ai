from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.services.correction_service import CorrectionService

router = APIRouter()


class CorrectionProposal(BaseModel):
    entity_type: str = Field(min_length=1, max_length=100, pattern=r"^[a-z_]+$")
    entity_id: UUID
    field_path: str = Field(min_length=1, max_length=300, pattern=r"^[a-z0-9_.]+$")
    granularity_key: str = Field(min_length=1, max_length=500)
    proposed_value: Any
    reason: str = Field(min_length=10, max_length=4000)
    evidence_snippet_id: UUID


class CorrectionReview(BaseModel):
    approve: bool
    decision_reason: str = Field(min_length=10, max_length=4000)


@router.post("", status_code=201, summary="Propose a non-destructive factual correction")
async def propose_correction(
    payload: CorrectionProposal,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    return await CorrectionService(db).propose(
        entity_type=payload.entity_type,
        entity_id=str(payload.entity_id),
        field_path=payload.field_path,
        granularity_key=payload.granularity_key,
        proposed_value=payload.proposed_value,
        reason=payload.reason,
        requested_by=user.user_id,
        evidence_snippet_id=str(payload.evidence_snippet_id),
    )


@router.post("/{correction_id}/review", summary="Approve or reject a pending correction")
async def review_correction(
    correction_id: UUID,
    payload: CorrectionReview,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> dict:
    return await CorrectionService(db).review(
        correction_id=str(correction_id),
        approve=payload.approve,
        reviewer=user.user_id,
        decision_reason=payload.decision_reason,
    )
