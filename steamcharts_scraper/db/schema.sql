PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS apps (
  app_id             INTEGER PRIMARY KEY,
  name               TEXT,
  short_description  TEXT,
  release_date       TEXT,
  developers         TEXT,   -- JSON array as text
  publishers         TEXT,   -- JSON array as text
  genres             TEXT,   -- JSON array as text
  categories         TEXT,   -- JSON array as text
  store_app_url      TEXT,
  last_refreshed     TEXT    -- ISO8601 UTC
);

CREATE TABLE IF NOT EXISTS snapshots (
  ts            TEXT NOT NULL,   -- ISO8601 UTC from spider
  app_id        INTEGER NOT NULL,
  rank          INTEGER,
  avg_players   INTEGER,
  peak_players  INTEGER,
  detail_url    TEXT,
  PRIMARY KEY (ts, app_id),
  FOREIGN KEY (app_id) REFERENCES apps(app_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_app_id ON snapshots(app_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_rank   ON snapshots(rank);
CREATE INDEX IF NOT EXISTS idx_snapshots_ts     ON snapshots(ts);
