"""
utils/helpers.py
================
PURPOSE: Shared utility functions used by ALL other modules.
Think of this as a toolbox — small reusable tools everyone can borrow.

CONNECTS TO: job_search.py, resume_parser.py, matcher.py, app.py
"""

import re
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


# ============================================================
# TEXT CLEANING FUNCTIONS
# ============================================================

def clean_text(text: str) -> str:
    """
    Removes extra whitespace and special characters from text.
    Used when cleaning extracted PDF text.
    Example: "  Hello   World\n\n " becomes "Hello World"
    """
    if not text:
        return ""
    # Replace multiple spaces and newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()


def truncate_text(text: str, max_chars: int = 300) -> str:
    """
    Shortens long text for display in job cards.
    Adds ... at the end if text is too long.
    Example: truncate_text("Very long text...", 20) becomes "Very long..."
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(' ', 1)[0] + "..."


# ============================================================
# SKILL PROCESSING
# ============================================================

# Master list of all tech skills the app can recognize
# This covers 95% of skills found in real job postings
KNOWN_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "swift", "kotlin", "scala", "r", "matlab", "php",

    # Web Frameworks
    "django", "flask", "fastapi", "react", "angular", "vue", "node.js",
    "express", "spring", "rails", "laravel", "nextjs", "streamlit",

    # Data and ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "seaborn", "plotly", "opencv", "transformers", "bert",
    "langchain", "llm", "generative ai", "mlflow", "airflow",

    # Databases
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle",
    "cassandra", "elasticsearch", "dynamodb", "firebase",

    # Cloud and DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "github actions", "ci/cd", "linux", "bash", "ansible",

    # Tools and Others
    "git", "rest api", "graphql", "microservices", "kafka", "spark",
    "hadoop", "tableau", "power bi", "excel", "jira", "agile", "scrum"
]


def extract_skills_from_text(text: str) -> List[str]:
    """
    Scans any text and returns all recognized tech skills found in it.
    Uses word boundary matching so "R" does not match inside "React".

    Args:
        text: Any text such as resume content or job description

    Returns:
        List of skill names found, example: ["Python", "Docker", "AWS"]
    """
    if not text:
        return []

    text_lower = text.lower()
    found_skills = []

    for skill in KNOWN_SKILLS:
        # \b means word boundary — prevents partial matches
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            # Capitalize nicely for display
            found_skills.append(skill.title())

    # Remove duplicates while keeping order
    return list(dict.fromkeys(found_skills))


def normalize_skill(skill: str) -> str:
    """
    Normalizes skill name for comparison by removing dots, spaces, dashes.
    Example: "node.js" becomes "nodejs", "React.js" becomes "reactjs"
    """
    return skill.lower().replace(".", "").replace(" ", "").replace("-", "")


def get_skill_overlap(skills_a: List[str], skills_b: List[str]) -> Dict:
    """
    Compares two skill lists and returns matched and missing skills.
    Used by matcher.py to compare resume skills vs job skills.

    Returns a dictionary with:
        matched  - skills found in both lists
        missing  - skills in job but not in resume (candidate lacks these)
        extra    - skills in resume but not in job (bonus skills)
    """
    norm_a = {normalize_skill(s): s for s in skills_a}
    norm_b = {normalize_skill(s): s for s in skills_b}

    matched = [norm_b[k] for k in norm_a if k in norm_b]
    missing = [norm_b[k] for k in norm_b if k not in norm_a]
    extra   = [norm_a[k] for k in norm_a if k not in norm_b]

    return {
        "matched": matched,
        "missing": missing,
        "extra":   extra
    }


# ============================================================
# DATE AND FORMATTING HELPERS
# ============================================================

def format_date(date_str: str) -> str:
    """
    Converts ISO date string to human readable format.
    Example: "2025-06-01" becomes "01 Jun 2025"
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.strftime("%d %b %Y")
    except:
        return date_str


def days_since_posted(date_str: str) -> str:
    """
    Returns how long ago a job was posted in friendly format.
    Example: "2025-06-01" might return "3 days ago"
    """
    try:
        posted = datetime.strptime(date_str, "%Y-%m-%d")
        today  = datetime.now()
        diff   = (today - posted).days

        if diff == 0:
            return "Today"
        elif diff == 1:
            return "Yesterday"
        elif diff < 7:
            return f"{diff} days ago"
        elif diff < 30:
            weeks = diff // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            return format_date(date_str)
    except:
        return "Recently"


# ============================================================
# FILE UTILITIES
# ============================================================

def load_json_file(filepath: str) -> Any:
    """
    Safely loads a JSON file from disk.
    Returns empty list if file is not found or is broken.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def load_css(filepath: str) -> str:
    """
    Reads the CSS file and returns it as a string.
    Used by app.py to inject custom styling into Streamlit.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_pdf(file) -> tuple:
    """
    Checks that an uploaded file is a valid PDF.

    Returns:
        (True, "OK") if file is valid
        (False, "error message") if file is invalid
    """
    if file is None:
        return False, "No file uploaded"

    if not file.name.lower().endswith('.pdf'):
        return False, "File must be a PDF (.pdf extension)"

    # Max allowed size is 5MB
    if file.size > 5 * 1024 * 1024:
        return False, "File size must be less than 5MB"

    return True, "OK"


def validate_search_query(query: str) -> tuple:
    """
    Validates a job search input before sending to search engine.

    Returns:
        (True, "OK") if query is valid
        (False, "error message") if query is invalid
    """
    if not query or not query.strip():
        return False, "Please enter a job title or skill to search"

    if len(query.strip()) < 2:
        return False, "Search query must be at least 2 characters"

    if len(query) > 100:
        return False, "Search query is too long (max 100 characters)"

    return True, "OK"


# ============================================================
# HTML CARD GENERATORS
# ============================================================

def generate_job_card_html(job: Dict) -> str:
    skills_html = ""
    for skill in job.get("skills_required", [])[:6]:
        skills_html += f'<span class="skill-tag">{skill}</span> '

    remote_badge = ""
    if job.get("remote"):
        remote_badge = '<span style="background:#065f46;color:#6ee7b7;padding:2px 10px;border-radius:20px;font-size:12px;margin-left:8px;">🏠 Remote</span>'

    country_flag = "🇮🇳" if job.get("country") == "India" else "🌍"
    days_ago = days_since_posted(job.get("posted_date", ""))
    description = truncate_text(job.get("description", ""), 200)
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "N/A")
    salary = job.get("salary", "N/A")
    experience = job.get("experience", "N/A")

    return (
        '<div class="job-card">'
        f'<div class="job-title">{title}</div>'
        '<div style="margin:6px 0;">'
        f'<span class="job-company">🏢 {company}</span>'
        f'{remote_badge}'
        '</div>'
        f'<div class="job-location">{country_flag} {location}'
        f' &nbsp;|&nbsp; <span style="color:#fbbf24;">💰 {salary}</span>'
        f' &nbsp;|&nbsp; <span style="color:#9ca3af;">⏱️ {experience}</span>'
        '</div>'
        f'<div style="margin:10px 0;color:#d1d5db;font-size:14px;line-height:1.5;">{description}</div>'
        f'<div style="margin:8px 0;">{skills_html}</div>'
        f'<div style="margin-top:12px;color:#6b7280;font-size:12px;">📅 Posted: {days_ago}</div>'
        '</div>'
    )


def generate_match_result_html(match_data: Dict) -> str:
    """
    Generates HTML to display resume vs job match results.
    Called by app.py after matcher.py calculates the score.

    Args:
        match_data: Dictionary output from matcher.py calculate_match()

    Returns:
        HTML string ready to pass into st.markdown()
    """
    score = match_data.get("score", 0)

    # Pick color based on score
    if score >= 70:
        score_class = "match-score-high"
        emoji        = "🟢"
    elif score >= 40:
        score_class = "match-score-medium"
        emoji        = "🟡"
    else:
        score_class = "match-score-low"
        emoji        = "🔴"

    # Build matched skill tags
    matched_html = " ".join([
        f'<span class="skill-tag-match">{s}</span>'
        for s in match_data.get("matched_skills", [])
    ])

    # Build missing skill tags
    missing_html = " ".join([
        f'<span class="skill-tag-missing">{s}</span>'
        for s in match_data.get("missing_skills", [])
    ])

    html = f"""
    <div style="text-align:center; padding:20px;">
        <div style="font-size:14px;color:#9ca3af;margin-bottom:8px;">
            ATS Match Score {emoji}
        </div>
        <div class="{score_class}">{score}%</div>
    </div>

    <div style="margin:16px 0;">
        <div style="font-size:14px;color:#6ee7b7;font-weight:600;margin-bottom:6px;">
            ✅ Matched Skills ({len(match_data.get('matched_skills', []))})
        </div>
        <div>
            {matched_html if matched_html else
             '<span style="color:#9ca3af">No matching skills found</span>'}
        </div>
    </div>

    <div style="margin:16px 0;">
        <div style="font-size:14px;color:#fca5a5;font-weight:600;margin-bottom:6px;">
            ❌ Missing Skills ({len(match_data.get('missing_skills', []))})
        </div>
        <div>
            {missing_html if missing_html else
             '<span style="color:#9ca3af">No missing skills — great match!</span>'}
        </div>
    </div>
    """
    return html