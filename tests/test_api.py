import os

os.environ.setdefault("SDIS_API_KEY", "test-api-key")

from fastapi.testclient import TestClient
from sdis_app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


def make_synthetic_student():
    response = client.post("/students", headers=AUTH_HEADERS, json={
        "display_name": "Synthetic Learner",
        "grade_level": "Grade 6",
        "preferred_language": "bn",
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_objectives_are_labelled():
    response = client.get("/curriculum/objectives")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert "not official" in data["warning"].lower()


def test_student_endpoints_require_api_key():
    response = client.get("/students/1")
    assert response.status_code == 401


def test_student_assessment_and_report():
    student_id = make_synthetic_student()
    attempt = client.post("/assessments/demo-math/attempts", headers=AUTH_HEADERS, json={
        "student_id": student_id,
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "q2", "answer": "0"},
            {"question_id": "q3", "answer": "2"},
        ],
    })
    assert attempt.status_code == 201
    assert attempt.json()["max_score"] == 3.0

    plan = client.get(f"/students/{student_id}/learning-plan", headers=AUTH_HEADERS)
    assert plan.status_code == 200
    assert plan.json()["teacher_review_required"] is True

    report = client.get(f"/students/{student_id}/report", headers=AUTH_HEADERS)
    assert report.status_code == 200
    assert report.json()["attempt_count"] == 1


def test_answer_key_not_exposed():
    response = client.get("/assessments/demo-math")
    assert response.status_code == 200
    body = response.json()
    assert all("answer" not in question for question in body["questions"])


def test_duplicate_question_ids_are_rejected():
    student_id = make_synthetic_student()
    response = client.post("/assessments/demo-math/attempts", headers=AUTH_HEADERS, json={
        "student_id": student_id,
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "q1", "answer": "999"},
        ],
    })
    assert response.status_code == 422


def test_unknown_question_ids_are_rejected():
    student_id = make_synthetic_student()
    response = client.post("/assessments/demo-math/attempts", headers=AUTH_HEADERS, json={
        "student_id": student_id,
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "not-in-this-assessment", "answer": "999"},
        ],
    })
    assert response.status_code == 422


def test_blank_student_name_is_rejected():
    response = client.post("/students", headers=AUTH_HEADERS, json={
        "display_name": "   ",
        "grade_level": "Grade 6",
        "preferred_language": "bn",
    })
    assert response.status_code == 422


def test_root_serves_student_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SDIS Learning Intelligence" in response.text
    assert "পরীক্ষা শুরু করুন" in response.text


def test_anonymous_demo_attempt_is_saved_and_returns_learning_plan():
    response = client.post("/demo/attempts", json={
        "student_id": 1,
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "q2", "answer": "0"},
            {"question_id": "q3", "answer": "2"},
        ],
    })
    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 2.0
    assert body["max_score"] == 3.0
    assert body["attempt_id"] > 0
    assert body["learning_plan"]["teacher_review_required"] is True


def test_anonymous_demo_attempt_rejects_unknown_question():
    response = client.post("/demo/attempts", json={
        "student_id": 1,
        "answers": [{"question_id": "unknown", "answer": "x"}],
    })
    assert response.status_code == 422


def test_student_attempt_history_returns_scores_without_raw_answers(monkeypatch):
    monkeypatch.delenv("SDIS_TEACHER_API_KEY", raising=False)
    student_id = make_synthetic_student()
    response = client.post("/assessments/demo-math/attempts", headers=AUTH_HEADERS, json={
        "student_id": student_id,
        "answers": [
            {"question_id": "q1", "answer": "12"},
            {"question_id": "q2", "answer": "15"},
            {"question_id": "q3", "answer": "2"},
        ],
    })
    assert response.status_code == 201
    history = client.get(f"/students/{student_id}/attempts", headers=AUTH_HEADERS)
    assert history.status_code == 200
    body = history.json()
    assert body["attempt_count"] == 1
    assert body["history"][0]["percent"] == 100.0
    assert "answers" not in body["history"][0]


def test_teacher_dashboard_requires_key(monkeypatch):
    monkeypatch.delenv("SDIS_TEACHER_API_KEY", raising=False)
    response = client.get("/teacher/dashboard")
    assert response.status_code == 401


def test_teacher_dashboard_summary(monkeypatch):
    monkeypatch.delenv("SDIS_TEACHER_API_KEY", raising=False)
    student_id = make_synthetic_student()
    response = client.get("/teacher/dashboard", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "SDIS Learning Intelligence"
    assert body["summary"]["student_records"] >= 1
    assert isinstance(body["recent_attempts"], list)
    assert "limitations" in body


def test_learning_agent_team_tracks_pseudonymous_progress():
    import secrets
    payload={"student_id":1,"demo_session_id":secrets.token_hex(24),"answers":[{"question_id":"q1","answer":"12","time_spent_seconds":18,"hint_count":1},{"question_id":"q2","answer":"0","time_spent_seconds":22},{"question_id":"q3","answer":"2","time_spent_seconds":10}]}
    first=client.post("/demo/attempts",json=payload)
    assert first.status_code == 201
    body=first.json()
    assert body["agent_team"]["agents_run"] == 6
    assert body["agent_team"]["agents"][0]["result"]["signals"][0]["time_spent_seconds"] == 18
    second=client.post("/demo/attempts",json=payload)
    assert second.status_code == 201
    assert second.json()["student_id"] == body["student_id"]
    assert second.json()["agent_team"]["learner_profile"]["evidence_attempts"] >= 2


def test_student_agent_profile_requires_api_key():
    assert client.get("/students/1/agent-profile").status_code == 401
