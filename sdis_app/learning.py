from .curriculum import OBJECTIVES


def make_learning_plan(student_id: int, latest_attempt):
    if not latest_attempt:
        return {
            "student_id": student_id,
            "based_on_attempt_id": None,
            "activities": [{
                "objective_id": "BASELINE",
                "objective_title": "Baseline check",
                "suggested_activity": "Complete a short teacher-reviewed baseline assessment.",
                "reason": "There is not enough evidence yet to personalize a plan.",
            }],
            "teacher_review_required": True,
        }

    by_id = {objective["objective_id"]: objective for objective in OBJECTIVES}
    activities = []
    for objective_id, result in latest_attempt.objective_results.items():
        if result["percent"] < 70:
            objective = by_id.get(objective_id, {})
            activities.append({
                "objective_id": objective_id,
                "objective_title": objective.get("title", objective_id),
                "suggested_activity": (
                    "Review one worked example, then complete 3 similar practice "
                    "items and explain the steps."
                ),
                "reason": (
                    f"Current demonstration result: {result['percent']}%. "
                    "Recheck after practice."
                ),
            })

    if not activities:
        activities.append({
            "objective_id": "EXTENSION",
            "objective_title": "Extension and transfer",
            "suggested_activity": "Try a slightly more challenging problem and explain the reasoning.",
            "reason": "The latest demonstration assessment showed no objective below the prototype threshold.",
        })

    return {
        "student_id": student_id,
        "based_on_attempt_id": latest_attempt.id,
        "activities": activities,
        "teacher_review_required": True,
    }
