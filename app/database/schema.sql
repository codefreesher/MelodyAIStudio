PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT, email TEXT);
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, title TEXT NOT NULL, type TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS history(
 id INTEGER PRIMARY KEY, uuid TEXT UNIQUE NOT NULL, type TEXT NOT NULL, title TEXT NOT NULL,
 provider TEXT NOT NULL, model TEXT NOT NULL DEFAULT '', prompt TEXT NOT NULL,
 result_path TEXT NOT NULL, thumbnail_path TEXT NOT NULL DEFAULT '', metadata_json TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'completed');
CREATE INDEX IF NOT EXISTS history_type_date ON history(type, created_at);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS generations(uuid TEXT PRIMARY KEY, type TEXT, status TEXT, created_at TEXT);
PRAGMA user_version=1;
