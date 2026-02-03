import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            interests TEXT,
            countries TEXT,
            provider TEXT,
            model TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            data TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            created_at TEXT,
            message TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_session(interests, countries, provider, model):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (created_at, interests, countries, provider, model) VALUES (?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), json.dumps(interests), json.dumps(countries), provider, model),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def save_results(session_id: int, results):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO results (session_id, data) VALUES (?, ?)",
        (session_id, json.dumps(results)),
    )
    conn.commit()
    conn.close()


def get_results(session_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT data FROM results WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row["data"]) if row else []


def list_sessions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def save_alert(session_id: int, message: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alerts (session_id, created_at, message) VALUES (?, ?, ?)",
        (session_id, datetime.utcnow().isoformat(), message),
    )
    conn.commit()
    conn.close()
