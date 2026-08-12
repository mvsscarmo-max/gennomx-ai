import pytest

from app.mcp.tools.get_trial_results import get_trial_results
from tests.conftest import FakeResult, FakeRow


class ResultsDB:
    def __init__(self, responses):
        self.responses = iter(responses)

    async def execute(self, _statement, _params=None):
        return next(self.responses)


@pytest.mark.unit
async def test_trial_without_posted_results_returns_gaps_not_error():
    db = ResultsDB(
        [
            FakeResult(
                [
                    FakeRow(
                        "trial-1",
                        "NCT00000008",
                        "Fixture study without posted results",
                        "PHASE2",
                        "RECRUITING",
                        "Fixture Biotech",
                        [],
                    )
                ]
            ),
            FakeResult(
                [
                    FakeRow(
                        "endpoint-1",
                        "Progression-free survival",
                        "primary",
                        None,
                        "Up to 24 months",
                        None,
                        "evidence-1",
                    )
                ]
            ),
            FakeResult([]),
            FakeResult([]),
        ]
    )

    response = await get_trial_results({"nct_id": "NCT00000008"}, db)

    assert response["count"] == 1
    assert response["data"]["results"] == []
    assert response["data"]["adverse_events"] == []
    assert any("No quantitative results" in gap for gap in response["gaps"])
    assert response["data"]["endpoints"][0]["evidence_id"] == "evidence-1"


@pytest.mark.unit
async def test_trial_results_include_literal_values_adverse_events_and_evidence():
    db = ResultsDB(
        [
            FakeResult(
                [
                    FakeRow(
                        "trial-1",
                        "NCT00000007",
                        "Fixture study with posted results",
                        "PHASE2",
                        "COMPLETED",
                        "Fixture Biotech",
                        [],
                    )
                ]
            ),
            FakeResult(
                [
                    FakeRow(
                        "endpoint-1",
                        "Change from baseline score",
                        "primary",
                        None,
                        "Week 12",
                        "points",
                        "evidence-outcome",
                    )
                ]
            ),
            FakeResult(
                [
                    FakeRow(
                        "result-1",
                        "endpoint-1",
                        "Treatment",
                        '[{"value": "-2.4"}]',
                        None,
                        0.004,
                        None,
                        -3.0,
                        -1.2,
                        "Week 12",
                        42,
                        0.99,
                        "automatic",
                        "evidence-outcome",
                    )
                ]
            ),
            FakeResult(
                [
                    FakeRow(
                        "event-1",
                        "Pneumonia",
                        "serious",
                        1,
                        42,
                        "Treatment",
                        "evidence-safety",
                    )
                ]
            ),
        ]
    )

    response = await get_trial_results({"nct_id": "NCT00000007"}, db)

    assert response["count"] == 3
    assert "-2.4" in response["data"]["results"][0]["value"]
    assert response["data"]["adverse_events"][0]["name"] == "Pneumonia"
    assert response["data"]["adverse_events"][0]["evidence_id"] == "evidence-safety"
