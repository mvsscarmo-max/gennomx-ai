"""Pydantic v2 schemas for DrugAsset API responses."""

from pydantic import BaseModel, ConfigDict, Field


class DrugAssetList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    primary_name: str
    aliases: list[str] = Field(default_factory=list)
    inn: str | None = None
    modality: str | None = None
    development_stage: str | None = None
    indication_names: list[str] = Field(default_factory=list)
    target_symbols: list[str] = Field(default_factory=list)
    sponsor_names: list[str] = Field(default_factory=list)
    source_confidence: float | None = None
    updated_at: str | None = None


class DrugAssetDetail(DrugAssetList):
    mechanism_of_action: str | None = None
    external_ids: dict | None = None
    regulatory_status_summary: dict | None = None
    data_completeness_score: float | None = None
    created_at: str | None = None
