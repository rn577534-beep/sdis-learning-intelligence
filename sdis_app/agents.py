"""Transparent evidence-limited learning agent team; deterministic, not LLM agents."""
from statistics import mean

AGENT_ROLES = [
 {"id":"footprint_observer","name":"Learning Footprint Agent","purpose":"Observe answer correctness, time, hints and revisions."},
 {"id":"misconception_detector","name":"Error Pattern Agent","purpose":"Map incorrect answers to objectives without diagnosing the learner."},
 {"id":"mastery_tracker","name":"Mastery Progress Agent","purpose":"Summarize recent objective-level performance and evidence count."},
 {"id":"adaptive_coach","name":"Adaptive Practice Agent","purpose":"Suggest targeted next practice."},
 {"id":"learning_scientist","name":"Evidence Quality Agent","purpose":"Flag limited evidence and uncertainty."},
 {"id":"safety_reviewer","name":"Student Safety & Quality Agent","purpose":"Prevent permanent labels and high-stakes use."},
]

def run_learning_agent_team(student_id, attempt, assessment, submitted_answers, recent_attempts):
    """Run the team on structured evidence; do not infer hidden student traits."""
    questions = assessment.get("questions", [])
    submitted = {item.get("question_id"): item for item in submitted_answers}
    signals, errors = [], []
    for question in questions:
        answer = submitted.get(question["question_id"], {})
        correct = str(answer.get("answer", "")).strip().casefold() == str(question["answer"]).casefold()
        signals.append({"question_id": question["question_id"], "objective_id": question["objective_id"], "correct": correct, "time_spent_seconds": answer.get("time_spent_seconds"), "hint_count": answer.get("hint_count", 0), "revision_count": answer.get("revision_count", 0)})
        if not correct:
            errors.append({"question_id": question["question_id"], "objective_id": question["objective_id"], "signal": "incorrect_response", "diagnosis_made": False})
    history = {}
    for old in recent_attempts:
        for oid, item in (old.objective_results or {}).items():
            history.setdefault(oid, []).append(float(item.get("percent", 0)))
    mastery = []
    for oid, item in (attempt.objective_results or {}).items():
        values = (history.get(oid, [])[-4:] + [float(item.get("percent", 0))])[-5:]
        avg = mean(values) if values else 0
        mastery.append({"objective_id": oid, "latest_percent": float(item.get("percent", 0)), "recent_mean_percent": round(avg, 1), "evidence_attempts": len(values), "status": "needs_more_evidence" if len(values) < 3 else ("practice_recommended" if avg < 70 else "progressing")})
    recommendations = [{"objective_id": x["objective_id"], "action": "একটি সমাধান করা উদাহরণ দেখুন, একই ধরনের ৩টি অনুশীলন করুন, তারপর আবার যাচাই করুন।", "reason": "সর্বশেষ ডেমো প্রচেষ্টায় এই উদ্দেশ্যে ৭০%-এর কম ফল।"} for x in mastery if x["latest_percent"] < 70]
    if not recommendations:
        recommendations = [{"objective_id":"EXTENSION","action":"একটু কঠিন সমস্যা সমাধান করে প্রতিটি ধাপ নিজের ভাষায় ব্যাখ্যা করুন।","reason":"এই প্রচেষ্টায় কোনো উদ্দেশ্যে ৭০%-এর কম ফল দেখা যায়নি।"}]
    count = len(recent_attempts) + 1
    agents = [
      {"agent_id":"footprint_observer","status":"complete","result":{"questions_observed":len(signals),"correct":sum(x["correct"] for x in signals),"signals":signals}},
      {"agent_id":"misconception_detector","status":"complete","result":{"observed_error_signals":errors,"diagnosis_made":False}},
      {"agent_id":"mastery_tracker","status":"complete","result":{"objectives":mastery,"attempts_considered":count}},
      {"agent_id":"adaptive_coach","status":"complete","result":{"recommendations":recommendations}},
      {"agent_id":"learning_scientist","status":"complete","result":{"evidence_level":"very_limited" if count < 3 or len(signals) < 10 else "limited","attempts_considered":count,"warning":"ডেমো প্রশ্ন থেকে সামগ্রিক দক্ষতা নির্ধারণ করা যায় না।"}},
      {"agent_id":"safety_reviewer","status":"complete","result":{"teacher_review_required":True,"permanent_labels_allowed":False,"high_stakes_use_allowed":False}},
    ]
    return {"team_version":"0.1.0","mode":"deterministic_evidence_pipeline","student_id":student_id,"attempt_id":attempt.id,"agents_run":len(agents),"agents":agents,"learner_profile":{"latest_percent":round(100*attempt.score/attempt.max_score,1) if attempt.max_score else 0,"objective_progress":mastery,"evidence_attempts":count},"recommendations":recommendations,"guardrails":{"teacher_review_required":True,"not_a_diagnosis":True,"not_validated_for_high_stakes_use":True}}
