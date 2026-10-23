# API examples

Use synthetic/demo data only. The current prototype is not production-ready.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the interactive API docs at `http://127.0.0.1:8000/docs`.

## Create a synthetic demo student

```bash
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Demo Student","grade_level":"Grade 6","preferred_language":"bn"}'
```

## Get the demo assessment

```bash
curl http://127.0.0.1:8000/assessments/demo-math
```

## Submit an attempt (replace student_id)

```bash
curl -X POST http://127.0.0.1:8000/assessments/demo-math/attempts \
  -H "Content-Type: application/json" \
  -d '{"student_id":1,"answers":[{"question_id":"q1","answer":"12"},{"question_id":"q2","answer":"15"},{"question_id":"q3","answer":"2"}]}'
```

## Get the progress report

```bash
curl http://127.0.0.1:8000/students/1/report
```
