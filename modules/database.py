"""
modules/database.py
===================
PURPOSE:
Handles all database operations using SQLite.
Saves and loads jobs, resumes, search history, and applications.

WHY SQLite?
- No server needed — it is just one file called database.db
- Works perfectly on Streamlit Cloud with zero setup
- Python has sqlite3 built in — no extra installation needed
- Perfect for single user apps like this one

TABLES WE CREATE:
1. saved_jobs       - Jobs the user bookmarks
2. search_history   - Past search queries
3. resume_history   - Uploaded resume analyses
4. job_applications - Jobs the user has applied to

CONNECTS TO: app.py calls these functions directly
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# This is the path to the database file
# It will be automatically created when the app runs for the first time
DB_PATH = "database.db"


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.

    WHY check_same_thread=False?
    Streamlit uses multiple threads internally.
    Without this setting SQLite throws a threading error.
    This makes it safe to use across threads.

    WHY row_factory = sqlite3.Row?
    This makes database rows behave like dictionaries.
    So we can write row['title'] instead of row[0].
    Much easier to work with.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """
    Creates all database tables if they do not already exist.
    This function is called ONCE when the app starts.

    The phrase IF NOT EXISTS means this is completely safe to call
    multiple times — it will never delete existing data.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # ----------------------------------------------------------
    # TABLE 1: saved_jobs
    # Stores jobs the user clicks Save on
    # ----------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT UNIQUE,
            title       TEXT NOT NULL,
            company     TEXT NOT NULL,
            location    TEXT,
            salary      TEXT,
            country     TEXT DEFAULT 'India',
            skills      TEXT,
            apply_link  TEXT,
            description TEXT,
            job_data    TEXT,
            saved_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ----------------------------------------------------------
    # TABLE 2: search_history
    # Logs every search the user performs
    # ----------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            query         TEXT NOT NULL,
            location      TEXT,
            country       TEXT,
            results_count INTEGER DEFAULT 0,
            searched_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ----------------------------------------------------------
    # TABLE 3: resume_history
    # Stores every resume that gets analyzed
    # ----------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            filename       TEXT NOT NULL,
            extracted_text TEXT,
            skills_found   TEXT,
            ai_analysis    TEXT,
            ats_score      INTEGER DEFAULT 0,
            analyzed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ----------------------------------------------------------
    # TABLE 4: job_applications
    # Tracks jobs the user has applied to
    # ----------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT,
            job_title   TEXT NOT NULL,
            company     TEXT NOT NULL,
            status      TEXT DEFAULT 'Applied',
            match_score INTEGER DEFAULT 0,
            notes       TEXT,
            applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# SAVED JOBS FUNCTIONS
# ============================================================

def save_job(job: Dict) -> tuple:
    """
    Saves a job to the database when user clicks the Save button.

    Args:
        job: Job dictionary from job_search.py

    Returns:
        (True, "success message") or (False, "error message")
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Convert skills list to JSON string for storage in database
        skills_json = json.dumps(job.get("skills_required", []))

        # Store the entire job dictionary as JSON so we can restore it fully
        job_json = json.dumps(job)

        cursor.execute("""
            INSERT OR IGNORE INTO saved_jobs
            (job_id, title, company, location, salary, country,
             skills, apply_link, description, job_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("id", f"job_{datetime.now().timestamp()}"),
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("salary", ""),
            job.get("country", "India"),
            skills_json,
            job.get("apply_link", ""),
            job.get("description", ""),
            job_json
        ))

        # rowcount 0 means the job_id already existed — duplicate
        if cursor.rowcount == 0:
            conn.close()
            return False, "Job already saved!"

        conn.commit()
        conn.close()
        return True, f"✅ Saved: {job.get('title')} at {job.get('company')}"

    except Exception as e:
        return False, f"Database error: {str(e)}"


def get_saved_jobs(country_filter: Optional[str] = None) -> List[Dict]:
    """
    Gets all saved jobs from the database.
    Optionally filters by country (India or Global).

    Returns:
        List of job dictionaries
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        if country_filter and country_filter != "All":
            cursor.execute("""
                SELECT * FROM saved_jobs
                WHERE country = ?
                ORDER BY saved_at DESC
            """, (country_filter,))
        else:
            cursor.execute("""
                SELECT * FROM saved_jobs
                ORDER BY saved_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        jobs = []
        for row in rows:
            job = dict(row)
            # Parse skills back from JSON string to Python list
            try:
                job["skills_required"] = json.loads(job.get("skills", "[]"))
            except:
                job["skills_required"] = []
            # Restore full job data
            try:
                full_data = json.loads(job.get("job_data", "{}"))
                job.update(full_data)
            except:
                pass
            jobs.append(job)

        return jobs

    except Exception as e:
        print(f"Error fetching saved jobs: {e}")
        return []


def delete_saved_job(job_id: str) -> bool:
    """
    Removes a job from saved jobs by its ID.
    Called when user clicks the Remove button.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def is_job_saved(job_id: str) -> bool:
    """
    Checks if a specific job is already saved.
    Used to show Save or Already Saved button correctly.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM saved_jobs WHERE job_id = ?", (job_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except:
        return False


# ============================================================
# SEARCH HISTORY FUNCTIONS
# ============================================================

def log_search(query: str, location: str = "",
               country: str = "India", results_count: int = 0) -> None:
    """
    Saves a search query to history automatically after every search.
    This powers the Recent Searches section in the sidebar.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_history (query, location, country, results_count)
            VALUES (?, ?, ?, ?)
        """, (query, location, country, results_count))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging search: {e}")


def get_search_history(limit: int = 10) -> List[Dict]:
    """
    Returns the most recent search queries.
    Shown in the sidebar as Recent Searches.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM search_history
            ORDER BY searched_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return []


# ============================================================
# RESUME HISTORY FUNCTIONS
# ============================================================

def save_resume_analysis(filename: str, extracted_text: str,
                          skills: List[str], ai_analysis: str,
                          ats_score: int = 0) -> int:
    """
    Saves a resume analysis result to the database.
    Called after Gemini finishes analyzing an uploaded resume.

    Returns:
        The new record ID as integer, or -1 if saving failed
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO resume_history
            (filename, extracted_text, skills_found, ai_analysis, ats_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            filename,
            extracted_text[:10000],    # Limit stored text to 10000 chars
            json.dumps(skills),
            ai_analysis,
            ats_score
        ))

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    except Exception as e:
        print(f"Error saving resume: {e}")
        return -1


def get_resume_history(limit: int = 5) -> List[Dict]:
    """
    Returns the most recent resume analyses.
    Shown in the Resume tab as Past Analyses.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, ats_score, analyzed_at, skills_found
            FROM resume_history
            ORDER BY analyzed_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            r = dict(row)
            try:
                r["skills"] = json.loads(r.get("skills_found", "[]"))
            except:
                r["skills"] = []
            results.append(r)
        return results
    except:
        return []


# ============================================================
# JOB APPLICATIONS TRACKING FUNCTIONS
# ============================================================

def track_application(job_id: str, job_title: str,
                       company: str, match_score: int = 0,
                       notes: str = "") -> bool:
    """
    Saves a job application to the tracker.
    Called when user clicks Apply and Track button.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO job_applications
            (job_id, job_title, company, match_score, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, job_title, company, match_score, notes))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def get_applications() -> List[Dict]:
    """
    Returns all tracked job applications.
    Shown in the Applications Tracker tab.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM job_applications
            ORDER BY applied_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return []


def update_application_status(app_id: int, status: str) -> bool:
    """
    Updates the status of a job application.
    Status options: Applied, Interview, Offer, Rejected, Withdrawn
    """
    valid_statuses = ["Applied", "Interview", "Offer", "Rejected", "Withdrawn"]
    if status not in valid_statuses:
        return False

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE job_applications SET status = ? WHERE id = ?",
            (status, app_id)
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

def get_dashboard_stats() -> Dict:
    """
    Returns summary numbers for the dashboard overview section.
    Called by app.py to display the metric cards at the top.

    Returns a dictionary with counts of all major activities.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM saved_jobs")
        saved_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM search_history")
        search_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM resume_history")
        resume_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM job_applications")
        apps_count = cursor.fetchone()["count"]

        cursor.execute("""
            SELECT AVG(ats_score) as avg_score
            FROM resume_history
            WHERE ats_score > 0
        """)
        avg_row   = cursor.fetchone()
        avg_ats   = avg_row["avg_score"] if avg_row["avg_score"] else 0

        conn.close()

        return {
            "saved_jobs":      saved_count,
            "total_searches":  search_count,
            "resumes_analyzed": resume_count,
            "applications":    apps_count,
            "avg_ats_score":   round(avg_ats, 1)
        }

    except Exception as e:
        print(f"Stats error: {e}")
        return {
            "saved_jobs":      0,
            "total_searches":  0,
            "resumes_analyzed": 0,
            "applications":    0,
            "avg_ats_score":   0
        }