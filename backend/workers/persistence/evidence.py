"""Evidence-snippet persistence shared by trial and publication ingestion."""

import json
import uuid

from sqlalchemy import text


async def _insert_trial_field_evidence(
    *, db, source_document_id: str, trial_id: str, protocol: dict
) -> None:
    fragments = {
        "status_normalized": protocol.get("statusModule", {}).get("overallStatus"),
        "last_update_date": protocol.get("statusModule", {}).get("lastUpdatePostDateStruct"),
        "phase_normalized": protocol.get("designModule", {}).get("phases"),
        "enrollment": protocol.get("designModule", {}).get("enrollmentInfo"),
        "sponsor_name": protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor"),
    }
    for field_name, field_value in fragments.items():
        if field_value is None:
            continue
        await db.execute(
            text("""
                INSERT INTO evidence_snippets (
                    id, source_document_id, entity_type, entity_id, entity_field,
                    text_excerpt, section, extraction_method, confidence_score,
                    created_at, updated_at
                ) SELECT
                    :id, :source_document_id, 'clinical_trial', :trial_id, :entity_field,
                    :text_excerpt, :section, 'api_source_fragment', 0.99, now(), now()
                WHERE NOT EXISTS (
                    SELECT 1 FROM evidence_snippets
                    WHERE source_document_id = :source_document_id
                      AND entity_type = 'clinical_trial' AND entity_id = :trial_id
                      AND entity_field = :entity_field
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "source_document_id": source_document_id,
                "trial_id": trial_id,
                "entity_field": field_name,
                "text_excerpt": json.dumps(field_value, ensure_ascii=False, sort_keys=True),
                "section": f"protocolSection.{field_name}",
            },
        )


async def _insert_evidence_snippet(
    *,
    db,
    source_document_id: str,
    trial_id: str,
    raw: dict,
) -> None:
    protocol = raw.get("protocolSection", {})
    fragment = {
        key: protocol[key]
        for key in ("identificationModule", "statusModule", "sponsorCollaboratorsModule")
        if key in protocol
    }
    evidence_text = json.dumps(fragment, ensure_ascii=False, sort_keys=True)
    await db.execute(
        text("""
            INSERT INTO evidence_snippets (
                id, source_document_id, entity_type, entity_id, entity_field,
                text_excerpt, section, extraction_method, confidence_score,
                created_at, updated_at
            )
            SELECT
                :id, :source_document_id, 'clinical_trial', :trial_id, 'summary',
                :text_excerpt, 'protocolSection', 'api_source_fragment', 0.95,
                now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'clinical_trial' AND entity_id = :trial_id
                  AND entity_field = 'summary'
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "source_document_id": source_document_id,
            "trial_id": trial_id,
            "text_excerpt": evidence_text,
        },
    )
    await _insert_trial_field_evidence(
        db=db,
        source_document_id=source_document_id,
        trial_id=trial_id,
        protocol=protocol,
    )


async def _insert_publication_evidence_snippet(
    *,
    db,
    source_document_id: str,
    pub_id: str,
    parsed,
    raw: dict | None,
) -> None:
    fragment_text = json.dumps(
        {
            "title": parsed.title,
            "abstract": (parsed.abstract or "")[:500],
            "journal": parsed.journal,
            "pmid": parsed.pmid,
            "doi": parsed.doi,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    await db.execute(
        text("""
            INSERT INTO evidence_snippets (
                id, source_document_id, entity_type, entity_id, entity_field,
                text_excerpt, section, extraction_method, confidence_score,
                created_at, updated_at
            )
            SELECT
                :id, :source_document_id, 'publication', :pub_id, 'summary',
                :text_excerpt, 'pubmed_efetch', 'api_source_fragment', 0.95,
                now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'publication' AND entity_id = :pub_id
                  AND entity_field = 'summary'
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "source_document_id": source_document_id,
            "pub_id": pub_id,
            "text_excerpt": fragment_text,
        },
    )


async def _insert_regulatory_evidence_snippet(
    *,
    db,
    source_document_id: str,
    approval_id: str,
    fragment: dict,
) -> None:
    evidence_text = json.dumps(fragment, ensure_ascii=False, sort_keys=True, default=str)
    await db.execute(
        text("""
            INSERT INTO evidence_snippets (
                id, source_document_id, entity_type, entity_id, entity_field,
                text_excerpt, section, extraction_method, confidence_score,
                created_at, updated_at
            )
            SELECT
                :id, :source_document_id, 'regulatory_approval', :approval_id, 'summary',
                :text_excerpt, 'api_source_record', 'api_source_fragment', 0.9,
                now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'regulatory_approval' AND entity_id = :approval_id
                  AND entity_field = 'summary'
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "source_document_id": source_document_id,
            "approval_id": approval_id,
            "text_excerpt": evidence_text,
        },
    )


async def _insert_target_evidence_snippet(
    *,
    db,
    source_document_id: str,
    target_id: str,
    fragment: dict,
) -> None:
    evidence_text = json.dumps(fragment, ensure_ascii=False, sort_keys=True, default=str)
    await db.execute(
        text("""
            INSERT INTO evidence_snippets (
                id, source_document_id, entity_type, entity_id, entity_field,
                text_excerpt, section, extraction_method, confidence_score,
                created_at, updated_at
            )
            SELECT
                :id, :source_document_id, 'target', :target_id, 'summary',
                :text_excerpt, 'graphql_source_record', 'api_source_fragment', 0.9,
                now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'target' AND entity_id = :target_id
                  AND entity_field = 'summary'
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "source_document_id": source_document_id,
            "target_id": target_id,
            "text_excerpt": evidence_text,
        },
    )


async def _insert_asset_evidence_snippet(
    *,
    db,
    source_document_id: str,
    asset_id: str,
    parsed,
    primary_name: str,
    raw: dict | None,
) -> None:
    if not raw:
        return
    module = raw.get("protocolSection", {}).get("armsInterventionsModule", {})
    interventions = module.get("interventions", [])
    fragment = next(
        (
            item
            for item in interventions
            if item.get("name", "").casefold() == primary_name.casefold()
        ),
        None,
    )
    if not fragment:
        return
    evidence_text = json.dumps(fragment, ensure_ascii=False, sort_keys=True)
    await db.execute(
        text("""
            INSERT INTO evidence_snippets (
                id, source_document_id, entity_type, entity_id, entity_field,
                text_excerpt, section, extraction_method, confidence_score,
                created_at, updated_at
            )
            SELECT
                :id, :source_document_id, 'drug_asset', :asset_id, 'trial_intervention',
                :text_excerpt, 'armsInterventionsModule.interventions',
                'api_source_fragment', 0.86,
                now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM evidence_snippets
                WHERE source_document_id = :source_document_id
                  AND entity_type = 'drug_asset' AND entity_id = :asset_id
                  AND entity_field = 'trial_intervention'
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "source_document_id": source_document_id,
            "asset_id": asset_id,
            "text_excerpt": evidence_text,
        },
    )
