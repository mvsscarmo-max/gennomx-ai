from unittest.mock import AsyncMock

import pytest

from app.database_security import assert_database_role
from tests.conftest import FakeResult, FakeRow


@pytest.mark.unit
async def test_expected_non_privileged_role_is_accepted():
    db = AsyncMock()
    db.execute.return_value = FakeResult([FakeRow("gennomx_app", "gennomx_app", False, False)])
    await assert_database_role(db, "gennomx_app")


@pytest.mark.unit
@pytest.mark.parametrize(
    "row",
    [
        FakeRow("postgres", "postgres", True, True),
        FakeRow("gennomx_app", "gennomx_app", True, False),
        FakeRow("gennomx_app", "gennomx_app", False, True),
        FakeRow("gennomx_worker", "gennomx_worker", False, False),
    ],
)
async def test_unexpected_or_rls_bypassing_role_is_rejected(row):
    db = AsyncMock()
    db.execute.return_value = FakeResult([row])
    with pytest.raises(RuntimeError):
        await assert_database_role(db, "gennomx_app")
