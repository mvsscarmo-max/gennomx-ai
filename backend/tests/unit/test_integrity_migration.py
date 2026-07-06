"""Contract tests for the integrity/RLS migration."""

import importlib
from unittest.mock import Mock

import pytest


@pytest.mark.unit
def test_integrity_migration_adds_uuid_fks_checks_and_rls(monkeypatch):
    migration = importlib.import_module("migrations.versions.0002_integrity_rls")
    alter_column = Mock()
    create_foreign_key = Mock()
    create_check_constraint = Mock()
    create_table = Mock()
    create_index = Mock()
    execute = Mock()
    monkeypatch.setattr(migration.op, "alter_column", alter_column)
    monkeypatch.setattr(migration.op, "create_foreign_key", create_foreign_key)
    monkeypatch.setattr(migration.op, "create_check_constraint", create_check_constraint)
    monkeypatch.setattr(migration.op, "create_table", create_table)
    monkeypatch.setattr(migration.op, "create_index", create_index)
    monkeypatch.setattr(migration.op, "execute", execute)

    migration.upgrade()

    assert alter_column.call_count == len(migration.UUID_COLUMNS)
    assert create_foreign_key.call_count == len(migration.FOREIGN_KEYS)
    assert create_check_constraint.call_count == 4
    create_table.assert_called_once()
    statements = [call.args[0] for call in execute.call_args_list]
    assert sum("ENABLE ROW LEVEL SECURITY" in sql for sql in statements) == len(
        migration.RLS_TABLES
    )
    assert any("backend_read_clinical_trials" in sql for sql in statements)
    assert any("worker_write_source_documents" in sql for sql in statements)


@pytest.mark.unit
def test_integrity_migration_has_reversible_downgrade(monkeypatch):
    migration = importlib.import_module("migrations.versions.0002_integrity_rls")
    drop_constraint = Mock()
    alter_column = Mock()
    execute = Mock()
    drop_table = Mock()
    monkeypatch.setattr(migration.op, "drop_constraint", drop_constraint)
    monkeypatch.setattr(migration.op, "alter_column", alter_column)
    monkeypatch.setattr(migration.op, "execute", execute)
    monkeypatch.setattr(migration.op, "drop_table", drop_table)

    migration.downgrade()

    assert drop_constraint.call_count == len(migration.FOREIGN_KEYS) + 4
    assert alter_column.call_count == len(migration.UUID_COLUMNS)
    drop_table.assert_called_once_with("clinical_trial_assets")
    statements = [call.args[0] for call in execute.call_args_list]
    assert sum("DISABLE ROW LEVEL SECURITY" in sql for sql in statements) == len(
        migration.RLS_TABLES
    )
