from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    grade_level: str = Field(min_length=1, max_length=30)
    preferred_language: str = Field(default="bn", pattern="^(bn|en)$")


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    display_name: str
    grade_level: str
    preferred_language: str


class AnswerIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=80)
    answer: str = Field(max_length=500)


class AttemptCreate(BaseModel):
    student_id: int
    answers: List[AnswerIn]


class AttemptOut(BaseModel):
    attempt_id: int
    student_id: int
    assessment_id: str
    score: float
    max_score: float
    percent: float
    objective_results: dict
    note: str


class LearningActivity(BaseModel):
    objective_id: str
    objective_title: str
    suggested_activity: str
    reason: str


class LearningPlanOut(BaseModel):
    student_id: int
    based_on_attempt_id: Optional[int] = None
    activities: List[LearningActivity]
    teacher_review_required: bool = True
