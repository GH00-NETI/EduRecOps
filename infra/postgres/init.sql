CREATE TABLE IF NOT EXISTS learning_events (
  event_id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  user_id TEXT NOT NULL,
  course_id TEXT NOT NULL,
  session_id UUID NOT NULL,
  event_time TIMESTAMPTZ NOT NULL,
  device TEXT,
  payload JSONB NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_time ON learning_events(user_id, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_course_time ON learning_events(course_id, event_time DESC);

CREATE TABLE IF NOT EXISTS recommendation_impressions (
  impression_id UUID PRIMARY KEY,
  request_id UUID NOT NULL,
  user_id TEXT NOT NULL,
  course_id TEXT NOT NULL,
  rank INTEGER NOT NULL CHECK (rank > 0),
  score DOUBLE PRECISION NOT NULL,
  candidate_source TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  propensity DOUBLE PRECISION,
  served_at TIMESTAMPTZ NOT NULL,
  context JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_impressions_user_time ON recommendation_impressions(user_id, served_at DESC);

CREATE TABLE IF NOT EXISTS learning_outcomes (
  outcome_id UUID PRIMARY KEY,
  impression_id UUID REFERENCES recommendation_impressions(impression_id),
  outcome_type TEXT NOT NULL,
  outcome_value DOUBLE PRECISION,
  outcome_time TIMESTAMPTZ NOT NULL,
  attribution_window TEXT NOT NULL
);
