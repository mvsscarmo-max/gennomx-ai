"""Privacy-preserving operational audit queries for administrators."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_mcp_logs(
        self, *, status: str | None, tool_name: str | None, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        filters: list[str] = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}
        if status:
            filters.append("status = :status")
            params["status"] = status
        if tool_name:
            filters.append("tool_name = :tool_name")
            params["tool_name"] = tool_name
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        total = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM mcp_query_logs {where}"), params)
        ).scalar() or 0
        rows = (
            await self.db.execute(
                text(f"""
            SELECT id::text, timestamp, tool_name, requesting_client, result_count,
                   latency_ms, status, error_type, entity_types_accessed, safety_flags
            FROM mcp_query_logs {where}
            ORDER BY timestamp DESC NULLS LAST LIMIT :limit OFFSET :offset
        """),
                params,
            )
        ).fetchall()
        return [
            {
                "id": r[0],
                "timestamp": r[1].isoformat() if r[1] else None,
                "tool_name": r[2],
                "requesting_client": r[3],
                "result_count": r[4],
                "latency_ms": r[5],
                "status": r[6],
                "error_type": r[7],
                "entity_types_accessed": r[8] or [],
                "safety_flags": r[9] or [],
            }
            for r in rows
        ], total

    async def list_security_events(
        self, *, severity: str | None, status: str | None, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        filters: list[str] = []
        params: dict = {"offset": (page - 1) * page_size, "limit": page_size}
        if severity:
            filters.append("severity = :severity")
            params["severity"] = severity
        if status:
            filters.append("status = :status")
            params["status"] = status
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        total = (
            await self.db.execute(text(f"SELECT COUNT(*) FROM security_events {where}"), params)
        ).scalar() or 0
        rows = (
            await self.db.execute(
                text(f"""
            SELECT id::text, timestamp, event_type, severity, actor_type,
                   endpoint_or_tool, description, action_taken, status
            FROM security_events {where}
            ORDER BY timestamp DESC NULLS LAST LIMIT :limit OFFSET :offset
        """),
                params,
            )
        ).fetchall()
        return [
            {
                "id": r[0],
                "timestamp": r[1].isoformat() if r[1] else None,
                "event_type": r[2],
                "severity": r[3],
                "actor_type": r[4],
                "endpoint_or_tool": r[5],
                "description": r[6],
                "action_taken": r[7],
                "status": r[8],
            }
            for r in rows
        ], total
