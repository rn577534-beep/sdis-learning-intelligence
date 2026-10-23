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
