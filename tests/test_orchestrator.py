from types import SimpleNamespace

import pytest

from sdis_app.orchestrator import (
    EVENT_AGENT_ROUTING,
    coordinate_assessment_submission,
    get_event_route,
)


def test_assessment_event_routes_to_existing_agents():
    route = get_event_route("assessment_submitted")
    assert route["execution_status"] == "implemented"
    assert route["selected_agents"] == list(EVENT_AGENT_ROUTING["assessment_submitted"])


def test_unimplemented_event_is_transparently_routing_only():
    route = get_event_route("learner_requested_help")
    assert route["execution_status"] == "routing_only"
    assert "personal_tutor" in route["selected_agents"]


def test_unknown_event_is_rejected():
    with pytest.raises(ValueError, match="Unsupported learning event"):
        get_event_route("unknown_event")


def test_assessment_submission_runs_existing_pipeline_and_adds_metadata():
    attempt = SimpleNamespace(
        id=7,
        score=1.0,
        max_score=2.0,
        objective_results={
            "MATH6-ADD-01": {"score": 1.0, "max_score": 1.0, "percent": 100.0},
            "MATH6-MULT-01": {"score": 0.0, "max_score": 1.0, "percent": 0.0},
        },
    )
    assessment = {
        "questions": [
            {"question_id": "q1", "objective_id": "MATH6-ADD-01", "answer": "12"},
            {"question_id": "q2", "objective_id": "MATH6-MULT-01", "answer": "15"},
        ]
    }
    answers = [
        {"question_id": "q1", "answer": "12", "time_spent_seconds": 10, "hint_count": 0, "revision_count": 0},
        {"question_id": "q2", "answer": "10", "time_spent_seconds": 15, "hint_count": 1, "revision_count": 1},
    ]

    result = coordinate_assessment_submission(
        student_id=3,
        attempt=attempt,
        assessment=assessment,
        submitted_answers=answers,
        recent_attempts=[],
    )

    assert result["student_id"] == 3
    assert result["attempt_id"] == 7
    assert result["orchestrator"]["trigger"] == "assessment_submitted"
    assert result["orchestrator"]["execution_status"] == "implemented"
    assert {agent["agent_id"] for agent in result["agents"]} == set(
        EVENT_AGENT_ROUTING["assessment_submitted"]
    )
