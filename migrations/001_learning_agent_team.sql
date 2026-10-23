-- SDIS learning agent team: additive PostgreSQL migration.
-- Apply once to the configured SDIS database before deploying this version.
ALTER TABLE students ADD COLUMN IF NOT EXISTS demo_session_hash VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS ix_students_demo_session_hash ON students (demo_session_hash);

CREATE TABLE IF NOT EXISTS learning_agent_runs (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    attempt_id INTEGER NOT NULL REFERENCES assessment_attempts(id),
    agent_results JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_learning_agent_runs_student_id ON learning_agent_runs (student_id);
CREATE INDEX IF NOT EXISTS ix_learning_agent_runs_attempt_id ON learning_agent_runs (attempt_id);
