"""
Persistence & Traceability Layer
SQLite-based storage for requirements, test cases, quality reports, and trace links.
"""
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

_DB_PATH = "prototype.db"


def set_db_path(path: str):
    global _DB_PATH
    _DB_PATH = path


def get_db_path() -> str:
    return _DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS requirements (
            req_id          TEXT PRIMARY KEY,
            raw_input       TEXT NOT NULL,
            structured_req  TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            version         INTEGER DEFAULT 1,
            group_name      TEXT DEFAULT 'tool'
        );

        CREATE TABLE IF NOT EXISTS quality_reports (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            req_id              TEXT NOT NULL,
            smell_count         INTEGER DEFAULT 0,
            conformance         INTEGER DEFAULT 0,
            conformance_notes   TEXT,
            smells_json         TEXT,
            created_at          TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (req_id) REFERENCES requirements(req_id)
        );

        CREATE TABLE IF NOT EXISTS test_cases (
            tc_id       TEXT PRIMARY KEY,
            req_id      TEXT NOT NULL,
            raw_output  TEXT,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (req_id) REFERENCES requirements(req_id)
        );
        """)
        # Migration: add group_name to existing databases
        try:
            conn.execute("ALTER TABLE requirements ADD COLUMN group_name TEXT DEFAULT 'tool'")
        except Exception:
            pass  # column already exists
    logger.info("Database initialised at %s", _DB_PATH)


def next_req_id() -> str:
    with _conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
    return f"REQ-{count + 1:03d}"


def next_tc_id(offset: int = 0) -> str:
    """Return next TC-ID. Use offset=1 for the second ID in the same batch."""
    with _conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0]
    return f"TC-{count + 1 + offset:03d}"


def next_ctrl_req_id() -> str:
    with _conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM requirements WHERE group_name = 'control'"
        ).fetchone()[0]
    return f"CTRL-{count + 1:03d}"


def save_requirement(req_id: str, raw_input: str, structured_req: str, group_name: str = "tool"):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO requirements (req_id, raw_input, structured_req, group_name) VALUES (?, ?, ?, ?)",
            (req_id, raw_input, structured_req, group_name),
        )
    logger.info("Saved requirement %s (group: %s)", req_id, group_name)


def save_quality_report(
    req_id: str,
    smells: list,
    smell_count: int,
    conformance: bool,
    conformance_notes: str,
):
    with _conn() as conn:
        conn.execute(
            """INSERT INTO quality_reports
               (req_id, smell_count, conformance, conformance_notes, smells_json)
               VALUES (?, ?, ?, ?, ?)""",
            (req_id, smell_count, int(conformance), conformance_notes, json.dumps(smells)),
        )
    logger.info("Saved quality report for %s — smells: %d, conformance: %s", req_id, smell_count, conformance)


def save_test_cases(tc_ids: list[str], req_id: str, raw_output: str):
    with _conn() as conn:
        for tc_id in tc_ids:
            conn.execute(
                "INSERT OR IGNORE INTO test_cases (tc_id, req_id, raw_output) VALUES (?, ?, ?)",
                (tc_id, req_id, raw_output),
            )
    logger.info("Saved test cases %s for %s", tc_ids, req_id)


def load_all_requirements() -> list:
    with _conn() as conn:
        return conn.execute(
            "SELECT req_id, raw_input, structured_req, created_at, version "
            "FROM requirements ORDER BY created_at DESC"
        ).fetchall()


def load_quality_for_req(req_id: str) -> tuple | None:
    with _conn() as conn:
        return conn.execute(
            "SELECT smell_count, conformance, conformance_notes, smells_json "
            "FROM quality_reports WHERE req_id = ? ORDER BY created_at DESC LIMIT 1",
            (req_id,),
        ).fetchone()


def load_test_cases_for_req(req_id: str) -> list:
    with _conn() as conn:
        return conn.execute(
            "SELECT tc_id, raw_output FROM test_cases WHERE req_id = ? ORDER BY tc_id",
            (req_id,),
        ).fetchall()


def load_all_trace_links() -> list:
    """Return all (req_id, tc_id) pairs for traceability view."""
    with _conn() as conn:
        return conn.execute(
            "SELECT req_id, tc_id FROM test_cases ORDER BY req_id, tc_id"
        ).fetchall()


def load_metrics() -> dict:
    with _conn() as conn:
        total_reqs = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
        total_tcs = conn.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0]
        avg_smells = conn.execute("SELECT AVG(smell_count) FROM quality_reports").fetchone()[0] or 0.0
        conformance_rate = conn.execute("SELECT AVG(conformance) FROM quality_reports").fetchone()[0] or 0.0
        traced_reqs = conn.execute("SELECT COUNT(DISTINCT req_id) FROM test_cases").fetchone()[0]
    return {
        "total_reqs": total_reqs,
        "total_tcs": total_tcs,
        "avg_smells": round(avg_smells, 2),
        "conformance_rate": round(conformance_rate * 100, 1),
        "traceability_coverage": round((traced_reqs / total_reqs * 100) if total_reqs else 0.0, 1),
    }


def load_metrics_by_group() -> dict:
    """Return metrics split by group_name ('tool' vs 'control') for comparison."""
    result = {}
    with _conn() as conn:
        for group in ("tool", "control"):
            req_ids = [
                r[0] for r in conn.execute(
                    "SELECT req_id FROM requirements WHERE group_name = ?", (group,)
                ).fetchall()
            ]
            total_reqs = len(req_ids)
            if not req_ids:
                result[group] = {
                    "total_reqs": 0, "total_tcs": 0,
                    "avg_smells": 0.0, "conformance_rate": 0.0,
                    "traceability_coverage": 0.0,
                }
                continue

            placeholders = ",".join("?" * len(req_ids))
            avg_smells = conn.execute(
                f"SELECT AVG(smell_count) FROM quality_reports WHERE req_id IN ({placeholders})",
                req_ids,
            ).fetchone()[0] or 0.0
            conformance_rate = conn.execute(
                f"SELECT AVG(conformance) FROM quality_reports WHERE req_id IN ({placeholders})",
                req_ids,
            ).fetchone()[0] or 0.0
            total_tcs = conn.execute(
                f"SELECT COUNT(*) FROM test_cases WHERE req_id IN ({placeholders})",
                req_ids,
            ).fetchone()[0]
            traced_reqs = conn.execute(
                f"SELECT COUNT(DISTINCT req_id) FROM test_cases WHERE req_id IN ({placeholders})",
                req_ids,
            ).fetchone()[0]

            result[group] = {
                "total_reqs": total_reqs,
                "total_tcs": total_tcs,
                "avg_smells": round(avg_smells, 2),
                "conformance_rate": round(conformance_rate * 100, 1),
                "traceability_coverage": round((traced_reqs / total_reqs * 100) if total_reqs else 0.0, 1),
            }
    return result
