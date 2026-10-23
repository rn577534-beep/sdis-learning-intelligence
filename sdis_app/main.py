import os
import secrets

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from .database import Base, DATABASE_URL, engine, get_db
from .models import Student, AssessmentAttempt
from .schemas import StudentCreate, StudentOut, AttemptCreate
from .curriculum import OBJECTIVES, ASSESSMENTS
from .learning import make_learning_plan

if DATABASE_URL.startswith("sqlite"):
    # Local development convenience. Production schema is managed in PostgreSQL.
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SDIS MVP",
    version="0.1.0",
    description=(
        "Evidence-led student learning support prototype. "
        "Demonstration curriculum and heuristic scoring only."
    ),
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)):
    expected_key = os.getenv("SDIS_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=503, detail="API access is not configured")
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(status_code=401, detail="Valid X-API-Key header required")


@app.get("/")
def root():
    return {
        "name": "SDIS Learning Intelligence API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "note": "Prototype API; not production-ready for real student data.",
    }


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0", "mode": "prototype"}


@app.get("/health/ready")
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/curriculum/objectives")
def list_objectives(grade_level: str | None = None, subject: str | None = None):
    rows = OBJECTIVES
    if grade_level:
        rows = [item for item in rows if item["grade_level"].lower() == grade_level.lower()]
    if subject:
        rows = [item for item in rows if item["subject"].lower() == subject.lower()]
    return {
        "count": len(rows),
        "objectives": rows,
        "warning": "Demonstration data; not official NCTB content.",
    }


@app.post("/students", response_model=StudentOut, status_code=201, dependencies=[Depends(require_api_key)])
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(
        display_name=payload.display_name,
        grade_level=payload.grade_level,
        preferred_language=payload.preferred_language,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/students/{student_id}", response_model=StudentOut, dependencies=[Depends(require_api_key)])
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.get("/assessments/{assessment_id}")
def get_assessment(assessment_id: str):
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    # Never return answer keys to the client.
    return {
        key: value for key, value in assessment.items() if key != "questions"
    } | {
        "questions": [
            {key: value for key, value in question.items() if key != "answer"}
            for question in assessment["questions"]
        ],
        "warning": "Demonstration assessment; not validated.",
    }


@app.post("/assessments/{assessment_id}/attempts", status_code=201, dependencies=[Depends(require_api_key)])
def submit_attempt(assessment_id: str, payload: AttemptCreate, db: Session = Depends(get_db)):
    assessment = ASSESSMENTS.get(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    valid_question_ids = {question["question_id"] for question in assessment["questions"]}
    submitted_ids = {answer.question_id for answer in payload.answers}
    unknown_ids = submitted_ids - valid_question_ids
    if unknown_ids:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Submission contains question IDs not in this assessment",
                "unknown_question_ids": sorted(unknown_ids),
            },
        )

    submitted = {answer.question_id: answer.answer.strip() for answer in payload.answers}
    objective_points = {}
    total_score = 0.0
    max_score = 0.0

    for question in assessment["questions"]:
        points = float(question["points"])
        max_score += points
        objective_id = question["objective_id"]
        objective_points.setdefault(objective_id, {"score": 0.0, "max_score": 0.0})
        objective_points[objective_id]["max_score"] += points
        user_answer = submitted.get(question["question_id"], "")
        # Exact matching is a placeholder, not a validated assessment method.
        if user_answer.casefold() == question["answer"].casefold():
            total_score += points
            objective_points[objective_id]["score"] += points

    objective_results = {}
    for objective_id, values in objective_points.items():
        max_objective_score = values["max_score"]
        percent = round(100 * values["score"] / max_objective_score, 1) if max_objective_score else 0
        objective_results[objective_id] = {
            "score": values["score"],
            "max_score": max_objective_score,
            "percent": percent,
        }

    attempt = AssessmentAttempt(
        student_id=student.id,
        assessment_id=assessment_id,
        answers=[answer.model_dump() for answer in payload.answers],
        score=total_score,
        max_score=max_score,
        objective_results=objective_results,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    percent = round(100 * total_score / max_score, 1) if max_score else 0
    return {
        "attempt_id": attempt.id,
        "student_id": student.id,
        "assessment_id": assessment_id,
        "score": total_score,
        "max_score": max_score,
        "percent": percent,
        "objective_results": objective_results,
        "note": (
            "Prototype rule-based result only. Review with a teacher; "
            "not a diagnosis or permanent label."
        ),
    }


@app.get("/students/{student_id}/learning-plan", dependencies=[Depends(require_api_key)])
def get_learning_plan(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    latest = db.scalar(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.student_id == student_id)
        .order_by(AssessmentAttempt.created_at.desc(), AssessmentAttempt.id.desc())
        .limit(1)
    )
    return make_learning_plan(student_id, latest)


@app.get("/students/{student_id}/report", dependencies=[Depends(require_api_key)])
def get_student_report(student_id: int, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    attempts = list(db.scalars(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.student_id == student_id)
        .order_by(AssessmentAttempt.created_at.asc(), AssessmentAttempt.id.asc())
    ))
    history = [
        {
            "attempt_id": attempt.id,
            "assessment_id": attempt.assessment_id,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "percent": round(100 * attempt.score / attempt.max_score, 1) if attempt.max_score else 0,
            "created_at": attempt.created_at.isoformat(),
        }
        for attempt in attempts
    ]

    return {
        "student": {
            "id": student.id,
            "display_name": student.display_name,
            "grade_level": student.grade_level,
            "preferred_language": student.preferred_language,
        },
        "attempt_count": len(history),
        "assessment_history": history,
        "latest_objective_results": attempts[-1].objective_results if attempts else {},
        "limitations": [
            "Demo curriculum and assessment are not official or validated.",
            "Scores are limited evidence and must not be used for high-stakes decisions.",
            "Teacher review is required before acting on the suggested learning plan.",
        ],
    }
