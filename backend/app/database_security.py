"""Runtime verification that PostgreSQL least-privilege roles are effective."""

from sqlalchemy import text


async def assert_database_role(session, expected_role: str) -> None:
    row = (
        await session.execute(
            text("""
                SELECT current_user, rolname, rolsuper, rolbypassrls
                FROM pg_roles WHERE rolname = current_user
            """)
        )
    ).fetchone()
    if not row:
        raise RuntimeError("Database role metadata unavailable")
    current_user, role_name, is_superuser, bypasses_rls = row
    if current_user != expected_role or role_name != expected_role:
        raise RuntimeError(f"Unexpected database role: {current_user}")
    if is_superuser or bypasses_rls:
        raise RuntimeError(f"Database role {expected_role} bypasses RLS")
