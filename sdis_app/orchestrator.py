"""Event-based coordinator for the SDIS learning support pipeline.

The coordinator deliberately keeps existing deterministic agents as the first
execution path. It does not claim that planned LLM roles are implemented.
"""
from __future__ import annotations

from typing import Any

from .agents import run_learning_agent_team

ORCHESTRATOR_VERSION = "0.1.0"

# Event routing is explicit and inspectable. Only assessment_submitted currently
# has an execution implementation; other routes document the next integration
# points without pretending that those agents have run.
EVENT_AGENT_ROUTING: dict[str, tuple[str, ...]] = {
    "assessment_submitted": (
        "footprint_observer",
        "misconception_detector",
        "mastery_tracker",
        "adaptive_coach",
        "learning_scientist",
        "safety_reviewer",
    ),
    "learner_requested_help": (
        "personal_tutor",
        "subject_specialist",
        "safety_reviewer",
        "evidence_quality",
    ),
    "lesson_completed": (
        "mastery_tracker",
        "adaptive_coach",
        "study_planner",
        "revision_planner",
        "safety_reviewer",
    ),
    "revision_due": (
        "revision_planner",
        "adaptive_coach",
        "safety_reviewer",
    ),
    "learning_goal_updated": (
        "study_planner",
        "adaptive_coach",
        "safety_reviewer",
    ),
}


def get_event_route(event_type: str) -> dict[str, Any]:
    """Return the documented route for an event without executing any agents."""
    selected = EVENT_AGENT_ROUTING.get(event_type)
    if selected is None:
        raise ValueError(f"Unsupported learning event: {event_type}")
    implemented = event_type == "assessment_submitted"
    return {
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "event_type": event_type,
        "selected_agents": list(selected),
        "execution_status": "implemented" if implemented else "routing_only",
    }


def coordinate_assessment_submission(
    student_id: int,
    attempt: Any,
    assessment: dict[str, Any],
    submitted_answers: list[dict[str, Any]],
    recent_attempts: list[Any],
) -> dict[str, Any]:
    """Route an assessment event through the currently implemented agents."""
    route = get_event_route("assessment_submitted")
    team_result = run_learning_agent_team(
        student_id=student_id,
        attempt=attempt,
        assessment=assessment,
        submitted_answers=submitted_answers,
        recent_attempts=recent_attempts,
    )
    # Keep the existing response contract stable while making coordination
    # metadata visible for tests and future orchestration work.
    team_result["orchestrator"] = {
        "version": route["orchestrator_version"],
        "trigger": route["event_type"],
        "selected_agents": route["selected_agents"],
        "execution_status": route["execution_status"],
    }
    return team_result
