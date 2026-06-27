import hashlib
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors

DATABASE_URL = os.getenv("DATABASE_URL")


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS waitlist (
                    id             SERIAL PRIMARY KEY,
                    email          TEXT   UNIQUE NOT NULL,
                    name           TEXT   NOT NULL,
                    source         TEXT   NOT NULL DEFAULT 'hero',
                    freelance_type TEXT,
                    pain_point     TEXT,
                    current_tool   TEXT,
                    signed_up_at   TEXT   NOT NULL,
                    ip_hash        TEXT,
                    user_agent     TEXT
                )
            """)


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


def insert_signup(
    email: str,
    name: str,
    source: str,
    freelance_type: str,
    pain_point: str,
    current_tool: str,
    ip: str,
    user_agent: str,
) -> int | None:
    """Returns the new row id (signup position), or None if email already exists."""
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO waitlist
                        (email, name, source, freelance_type, pain_point, current_tool,
                         signed_up_at, ip_hash, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        email.lower().strip(),
                        name.strip(),
                        source,
                        freelance_type or None,
                        pain_point or None,
                        current_tool or None,
                        datetime.now(timezone.utc).isoformat(),
                        _hash_ip(ip),
                        (user_agent or "")[:500],
                    ),
                )
                return cur.fetchone()[0]
            except pg_errors.UniqueViolation:
                return None


def get_count() -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM waitlist")
            return cur.fetchone()[0]


def get_all(page: int = 1, per_page: int = 50) -> tuple[list[dict], int]:
    offset = (page - 1) * per_page
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) FROM waitlist")
            total = cur.fetchone()["count"]
            cur.execute(
                "SELECT * FROM waitlist ORDER BY id ASC LIMIT %s OFFSET %s",
                (per_page, offset),
            )
            return [dict(r) for r in cur.fetchall()], total


def get_all_for_export() -> list[dict]:
    with get_db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM waitlist ORDER BY id ASC")
            return [dict(r) for r in cur.fetchall()]


def get_stats() -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM waitlist")
            total = cur.fetchone()[0]

            today = datetime.now(timezone.utc).date().isoformat()
            cur.execute(
                "SELECT COUNT(*) FROM waitlist WHERE signed_up_at LIKE %s",
                (f"{today}%",),
            )
            today_count = cur.fetchone()[0]

            from datetime import timedelta
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            cur.execute(
                "SELECT COUNT(*) FROM waitlist WHERE signed_up_at >= %s",
                (week_ago,),
            )
            week_count = cur.fetchone()[0]

            cur.execute(
                "SELECT source, COUNT(*) as cnt FROM waitlist GROUP BY source"
            )
            src = {r[0]: r[1] for r in cur.fetchall()}

            return {
                "total": total,
                "today": today_count,
                "this_week": week_count,
                "hero_count": src.get("hero", 0),
                "cta_count": src.get("cta", 0),
            }
