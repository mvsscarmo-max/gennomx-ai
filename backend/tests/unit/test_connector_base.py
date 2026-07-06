"""Unit tests for BaseConnector and ConnectorResult."""

import pytest

from workers.base.connector import ConnectorResult


@pytest.mark.unit
class TestConnectorResult:
    def test_initial_counts_are_zero(self):
        r = ConnectorResult("test_source")
        assert r.records_fetched == 0
        assert r.records_inserted == 0
        assert r.records_updated == 0
        assert r.records_rejected == 0
        assert r.records_skipped == 0

    def test_finish_sets_duration(self):
        import time

        r = ConnectorResult("test_source")
        time.sleep(0.01)
        r.finish()
        assert r.duration_seconds is not None
        assert r.duration_seconds >= 0.0

    def test_errors_list_initially_empty(self):
        r = ConnectorResult("test_source")
        assert r.errors == []

    def test_raw_payloads_list_initially_empty(self):
        r = ConnectorResult("test_source")
        assert r.raw_payloads == []

    def test_compute_hash_deterministic(self):
        from workers.base.connector import BaseConnector

        data = {"nctId": "NCT123", "title": "Test"}
        h1 = BaseConnector.compute_hash(data)
        h2 = BaseConnector.compute_hash(data)
        assert h1 == h2

    def test_compute_hash_differs_for_different_data(self):
        from workers.base.connector import BaseConnector

        h1 = BaseConnector.compute_hash({"a": 1})
        h2 = BaseConnector.compute_hash({"a": 2})
        assert h1 != h2

    def test_compute_hash_is_sha256_hex(self):
        from workers.base.connector import BaseConnector

        h = BaseConnector.compute_hash({"key": "value"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
