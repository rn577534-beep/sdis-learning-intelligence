from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class StudentCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    grade_level: str = Field(min_length=1, max_length=30)
    preferred_language: str = Field(default="bn", pattern="^(bn|en)$")

    @field_validator("display_name", "grade_level")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank")
        return value


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    display_name: str
    grade_level: str
    preferred_language: str


class AnswerIn(BaseModel):
    question_id: str = Field(min_length=1, max_length=80)
    answer: str = Field(max_length=500)

    @field_validator("question_id")
    @classmethod
    def strip_question_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question ID must not be blank")
        return value


class AttemptCreate(BaseModel):
    student_id: int = Field(gt=0)
    answers: List[AnswerIn] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def reject_duplicate_question_ids(self):
        ids = [answer.question_id for answer in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Each question_id may appear only once")
        return self


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
