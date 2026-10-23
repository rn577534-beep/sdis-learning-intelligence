from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(80), nullable=False)
    grade_level = Column(String(30), nullable=False)
    preferred_language = Column(String(8), nullable=False, default="bn")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    attempts = relationship(
        "AssessmentAttempt",
        back_populates="student",
        cascade="all, delete-orphan",
    )


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    assessment_id = Column(String(80), nullable=False)
    answers = Column(JSON, nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False)
    objective_results = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    student = relationship("Student", back_populates="attempts")
