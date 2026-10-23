# Demonstration-only content. Replace with verified, current, licensed curriculum mapping.
OBJECTIVES = [
    {
        "objective_id": "MATH6-FRAC-01",
        "grade_level": "Grade 6",
        "subject": "Mathematics",
        "title": "Understand fractions",
        "description": "Represent a fraction as part of a whole.",
        "status": "DEMO_NOT_OFFICIAL",
    },
    {
        "objective_id": "MATH6-ADD-01",
        "grade_level": "Grade 6",
        "subject": "Mathematics",
        "title": "Add whole numbers",
        "description": "Add whole numbers using place value.",
        "status": "DEMO_NOT_OFFICIAL",
    },
    {
        "objective_id": "MATH6-MULT-01",
        "grade_level": "Grade 6",
        "subject": "Mathematics",
        "title": "Multiply whole numbers",
        "description": "Solve simple whole-number multiplication problems.",
        "status": "DEMO_NOT_OFFICIAL",
    },
]

ASSESSMENTS = {
    "demo-math": {
        "assessment_id": "demo-math",
        "title": "Demonstration Mathematics Check",
        "grade_level": "Grade 6",
        "subject": "Mathematics",
        "status": "DEMO_NOT_OFFICIAL",
        "questions": [
            {"question_id": "q1", "objective_id": "MATH6-ADD-01", "prompt": "What is 7 + 5?", "answer": "12", "points": 1},
            {"question_id": "q2", "objective_id": "MATH6-MULT-01", "prompt": "What is 3 × 5?", "answer": "15", "points": 1},
            {"question_id": "q3", "objective_id": "MATH6-FRAC-01", "prompt": "A whole is split into 4 equal parts. 2 parts are shaded. How many parts are shaded? (answer with a number)", "answer": "2", "points": 1},
        ],
    }
}
