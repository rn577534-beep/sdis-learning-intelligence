import os

os.environ.setdefault("SDIS_API_KEY", "test-api-key")

from fastapi.testclient import TestClient
from sdis_app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-api-key"}


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
    create = client.post("/students", headers=AUTH_HEADERS, json={
        "display_name": "Synthetic Learner",
        "grade_level": "Grade 6",
        "preferred_language": "bn",
    })
    assert create.status_code == 201
    student_id = create.json()["id"]

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

    report = client.get(f"/students/{student_id}/report", headers=AUTH_HEADERS)
    assert report.status_code == 200
    assert report.json()["attempt_count"] == 1


def test_answer_key_not_exposed():
    response = client.get("/assessments/demo-math")
    assert response.status_code == 200
    body = response.json()
    assert all("answer" not in question for question in body["questions"])
