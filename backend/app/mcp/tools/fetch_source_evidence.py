"""MCP Tool: fetch_source_evidence — return evidence snippets."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_source_evidence(arguments: dict, db: AsyncSession | None = None) -> dict:
    evidence_id = str(arguments.get("evidence_id", ""))[:50]
    source_document_id = str(arguments.get("source_document_id", ""))[:50]
    entity_id = str(arguments.get("entity_id", ""))[:50]
    entity_type = str(arguments.get("entity_type", ""))[:100]

    if not db:
        return {"data": [], "count": 0, "limitations": ["Database unavailable"]}

    filters = []
    params: dict = {}

    if evidence_id:
        filters.append("es.id::text = :eid")
        params["eid"] = evidence_id

    if source_document_id:
        filters.append("es.source_document_id = :sdid")
        params["sdid"] = source_document_id

    if entity_id:
        filters.append("es.entity_id = :entity_id")
        params["entity_id"] = entity_id

    if entity_type:
        filters.append("es.entity_type = :entity_type")
        params["entity_type"] = entity_type

    if not filters:
        return {
            "data": [],
            "count": 0,
            "limitations": [
                "Provide at least one filter: evidence_id, source_document_id, or entity_id"
            ],
        }

    where = " AND ".join(filters)

    rows = (
        await db.execute(
            text(f"""
            SELECT
                es.id::text,
                es.entity_type,
                es.entity_id,
                es.entity_field,
                es.text_excerpt,
                es.page_number,
                es.section,
                es.extraction_method,
                es.confidence_score,
                es.created_at,
                sd.url,
                sd.title AS doc_title,
                sd.license_status,
                sd.retrieved_at
            FROM evidence_snippets es
            LEFT JOIN source_documents sd ON sd.id::text = es.source_document_id
            WHERE {where}
            LIMIT 20
        """),
            params,
        )
    ).fetchall()

    results = [
        {
            "id": r[0],
            "entity_type": r[1],
            "entity_id": r[2],
            "entity_field": r[3],
            "text_excerpt": r[4],
            "page_number": r[5],
            "section": r[6],
            "extraction_method": r[7],
            "confidence_score": r[8],
            "collected_at": r[9].isoformat() if r[9] else None,
            "source": {
                "url": r[10],
                "title": r[11],
                "license_status": r[12],
                "retrieved_at": r[13].isoformat() if r[13] else None,
            },
        }
        for r in rows
    ]

    return {
        "data": results,
        "count": len(results),
        "limitations": [
            "Evidence reflects text at time of ingestion. Source content may have been updated."
        ],
        "gaps": [],
    }
