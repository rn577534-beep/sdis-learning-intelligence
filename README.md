# SDIS — Student Development & Learning Intelligence System

SDIS is an early-stage project exploring how schools can use evidence-informed learning data to support student progress. This repository is an MVP starting point, not a validated educational product.

## Principles

- Start with a narrow, measurable pilot: one grade and one subject.
- Validate learning objectives against the current official curriculum before use.
- Keep teachers in the loop; AI suggestions must be reviewed by educators.
- Track progress over time rather than assigning permanent labels to students.
- Minimize student data and protect privacy, consent, and child safety.
- Distinguish verified evidence from hypotheses and recommendations.
- Do not claim impact until evaluated in a real pilot.

## MVP status

The initial prototype is intended for local development and demonstration only. Sample curriculum data or heuristic scoring must not be treated as official curriculum mapping or validated assessment. This is not production-ready.

Before any school deployment, add authentication and authorization, secure data handling, appropriate consent and retention policies, educator review, accessibility testing, curriculum validation, and a documented evaluation plan.

## Suggested next steps

1. Define the pilot grade, subject, and learning outcomes.
2. Verify curriculum mappings against current NCTB materials.
3. Agree on a small set of transparent assessment indicators.
4. Test with synthetic data first.
5. Conduct a supervised pilot and evaluate outcomes before making efficacy claims.

## Contributions

Document assumptions, data sources, and limitations. Never commit identifiable student information, credentials, API keys, or other secrets.

## Deployment and security notes

- Vercel entrypoint: `app.py` (FastAPI ASGI app).
- PostgreSQL: set `SDIS_DATABASE_URL` to a Neon connection string in Vercel project environment variables.
- API protection: set a strong `SDIS_API_KEY` in Vercel. Student-data endpoints require the `X-API-Key` header; health and demo curriculum endpoints are public.
- `/health/ready` checks the database connection without exposing credentials.
- Production PostgreSQL schema is managed separately; local SQLite tables are created automatically for development/tests.
- This shared API key is a temporary prototype safeguard, not production-grade authentication or role-based access control. Do not store real student data yet.


## Teacher overview and attempt history (incremental MVP)

- `GET /teacher/dashboard` returns aggregate counts and up to 10 recent attempts. It requires `X-API-Key`.
- Set `SDIS_TEACHER_API_KEY` in Vercel to use a separate teacher key; when set, it overrides `SDIS_API_KEY` for the teacher dashboard. If unset, the legacy `SDIS_API_KEY` is used for compatibility.
- `GET /students/{student_id}/attempts` returns chronological scores and objective-level results without exposing raw submitted answers. It requires `X-API-Key`.
- This is not a user login system. Shared API keys are temporary prototype access control; before real school/student use, implement individual accounts, role-based authorization, consent, retention controls, and audit logging.
