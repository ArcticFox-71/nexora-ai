"""
modules/resume_parser.py
========================
PURPOSE:
Reads uploaded PDF resumes and extracts useful information from them.

WHAT IT EXTRACTS:
  - Raw text from PDF pages
  - Skills (using our KNOWN_SKILLS list from helpers.py)
  - Education details (degree, college, year)
  - Work experience (company names, years)
  - Contact info (email, phone, LinkedIn)
  - Overall resume score estimate

HOW PDF READING WORKS:
  1. First tries pdfplumber (best results for most PDFs)
  2. Falls back to PyPDF2 if pdfplumber fails
  3. Returns error message if both fail

CONNECTS TO:
  - app.py uploads the PDF file here
  - ai_analyzer.py receives the extracted text for Gemini analysis
  - matcher.py receives the skills list for job matching
"""

import re
import io
from typing import Dict, List, Tuple, Optional

import pdfplumber
import PyPDF2

from utils.helpers import (
    clean_text,
    extract_skills_from_text,
    KNOWN_SKILLS
)


# ============================================================
# MAIN PARSE FUNCTION
# ============================================================

def parse_resume(uploaded_file) -> Dict:
    """
    Main function called by app.py when user uploads a PDF.
    Coordinates all extraction steps and returns a complete result.

    Args:
        uploaded_file: The file object from st.file_uploader()

    Returns:
        Dictionary containing:
            success       - True if parsing worked, False if it failed
            filename      - Original file name
            raw_text      - Full extracted text from PDF
            skills        - List of tech skills found
            education     - List of education entries found
            experience    - List of work experience entries found
            contact_info  - Dictionary with email, phone, linkedin
            word_count    - Total words in resume
            page_count    - Number of pages in PDF
            error         - Error message if something failed
    """
    if uploaded_file is None:
        return _error_result("No file provided")

    try:
        # Read file bytes — we need this for both pdfplumber and PyPDF2
        file_bytes = uploaded_file.read()

        # Reset file pointer so it can be read again if needed
        uploaded_file.seek(0)

        # Step 1: Extract raw text from PDF
        raw_text, page_count = _extract_text(file_bytes)

        if not raw_text or len(raw_text.strip()) < 50:
            return _error_result(
                "Could not extract text from this PDF. "
                "Please make sure it is not a scanned image PDF."
            )

        # Step 2: Clean the extracted text
        cleaned_text = clean_text(raw_text)

        # Step 3: Extract all information from the cleaned text
        skills      = extract_skills_from_text(cleaned_text)
        education   = _extract_education(cleaned_text)
        experience  = _extract_experience(cleaned_text)
        contact     = _extract_contact_info(cleaned_text)
        word_count  = len(cleaned_text.split())

        return {
            "success":      True,
            "filename":     uploaded_file.name,
            "raw_text":     cleaned_text,
            "skills":       skills,
            "education":    education,
            "experience":   experience,
            "contact_info": contact,
            "word_count":   word_count,
            "page_count":   page_count,
            "error":        None
        }

    except Exception as e:
        return _error_result(f"Unexpected error while parsing: {str(e)}")


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def _extract_text(file_bytes: bytes) -> Tuple[str, int]:
    """
    Extracts all text from a PDF file.
    Tries pdfplumber first, then falls back to PyPDF2.

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Tuple of (extracted_text, page_count)
    """
    # --- Method 1: pdfplumber (preferred — better at complex layouts) ---
    try:
        text       = ""
        page_count = 0

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if text.strip():
            return text, page_count

    except Exception as e:
        print(f"pdfplumber failed: {e} — trying PyPDF2")

    # --- Method 2: PyPDF2 (fallback) ---
    try:
        text       = ""
        page_count = 0

        reader     = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        page_count = len(reader.pages)

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text, page_count

    except Exception as e:
        print(f"PyPDF2 also failed: {e}")
        return "", 0


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def _extract_education(text: str) -> List[Dict]:
    """
    Finds education information in resume text.
    Looks for degree names, college names, and graduation years.

    Returns list of education entries like:
        [{"degree": "B.Tech", "field": "CSE", "year": "2024"}]
    """
    education = []
    text_lower = text.lower()

    # Common degree keywords to look for
    degree_patterns = [
        r'\b(b\.?tech|bachelor of technology)\b',
        r'\b(b\.?e\.?|bachelor of engineering)\b',
        r'\b(b\.?sc\.?|bachelor of science)\b',
        r'\b(b\.?ca|bachelor of computer applications)\b',
        r'\b(m\.?tech|master of technology)\b',
        r'\b(m\.?sc\.?|master of science)\b',
        r'\b(mba|master of business administration)\b',
        r'\b(ph\.?d|doctor of philosophy)\b',
        r'\b(diploma)\b',
        r'\b(12th|hsc|higher secondary)\b',
        r'\b(10th|sslc|secondary)\b'
    ]

    for pattern in degree_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Get surrounding context (100 chars around the match)
            start   = max(0, match.start() - 20)
            end     = min(len(text), match.end() + 100)
            context = text[start:end].strip()

            # Look for a year near this match
            year_match = re.search(r'\b(19|20)\d{2}\b', context)
            year       = year_match.group() if year_match else ""

            education.append({
                "degree":  match.group().upper(),
                "context": context[:100],
                "year":    year
            })

    # Remove duplicates based on degree name
    seen    = set()
    unique  = []
    for edu in education:
        key = edu["degree"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(edu)

    return unique[:5]  # Return max 5 education entries


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def _extract_experience(text: str) -> List[Dict]:
    """
    Finds work experience information in resume text.
    Looks for company names, job titles, and date ranges.

    Returns list of experience entries like:
        [{"title": "Developer", "company": "TCS", "duration": "2022-2024"}]
    """
    experience = []
    text_lower  = text.lower()

    # Look for year ranges that indicate job durations
    # Pattern matches things like "2022 - 2024" or "Jan 2022 - Dec 2024"
    duration_pattern = r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\s*\d{4})\s*[-–to]+\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\s*(?:\d{4}|present|current))'

    matches = re.finditer(duration_pattern, text_lower)

    for match in matches:
        start    = max(0, match.start() - 100)
        end      = min(len(text), match.end() + 50)
        context  = text[start:end].strip()

        experience.append({
            "duration": match.group().strip(),
            "context":  context[:150]
        })

    # Also look for common experience section keywords
    exp_keywords = [
        "software engineer", "developer", "analyst", "intern",
        "manager", "lead", "architect", "consultant", "associate"
    ]

    for keyword in exp_keywords:
        if keyword in text_lower:
            # Find the position and get context
            idx     = text_lower.find(keyword)
            start   = max(0, idx - 20)
            end     = min(len(text), idx + 120)
            context = text[start:end].strip()

            # Only add if not already captured
            if not any(context[:50] in e.get("context", "") for e in experience):
                experience.append({
                    "duration": "",
                    "context":  context[:150]
                })

    return experience[:6]  # Return max 6 experience entries


# ============================================================
# CONTACT INFO EXTRACTION
# ============================================================

def _extract_contact_info(text: str) -> Dict:
    """
    Extracts contact information from resume text.
    Looks for email address, phone number, and LinkedIn URL.

    Returns dictionary like:
        {
            "email":   "arjun@example.com",
            "phone":   "+91 9876543210",
            "linkedin": "linkedin.com/in/arjun"
        }
    """
    contact = {
        "email":    "",
        "phone":    "",
        "linkedin": "",
        "github":   ""
    }

    # Email pattern
    email_match = re.search(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        text
    )
    if email_match:
        contact["email"] = email_match.group()

    # Indian phone number pattern
    # Matches formats: +91 9876543210, 9876543210, 098-765-43210
    phone_match = re.search(
        r'(\+91[-\s]?)?[6-9]\d{9}',
        text
    )
    if phone_match:
        contact["phone"] = phone_match.group()

    # LinkedIn URL pattern
    linkedin_match = re.search(
        r'linkedin\.com/in/[\w\-]+',
        text.lower()
    )
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group()

    # GitHub URL pattern
    github_match = re.search(
        r'github\.com/[\w\-]+',
        text.lower()
    )
    if github_match:
        contact["github"] = github_match.group()

    return contact


# ============================================================
# RESUME QUALITY SCORING
# ============================================================

def calculate_resume_score(parsed_data: Dict) -> Dict:
    """
    Calculates a basic quality score for the resume.
    This is separate from the job match score.
    It measures how complete and well-structured the resume is.

    Scoring breakdown:
        Skills section    : 30 points (has skills listed)
        Experience        : 25 points (has work history)
        Education         : 20 points (has education details)
        Contact info      : 15 points (has email and phone)
        Resume length     : 10 points (appropriate word count)

    Returns dictionary with score and breakdown.
    """
    score    = 0
    breakdown = {}

    # Score 1: Skills (max 30 points)
    skill_count = len(parsed_data.get("skills", []))
    if skill_count >= 10:
        skill_score = 30
    elif skill_count >= 5:
        skill_score = 20
    elif skill_count >= 2:
        skill_score = 10
    else:
        skill_score = 0
    score += skill_score
    breakdown["Skills"] = {
        "score": skill_score,
        "max":   30,
        "note":  f"{skill_count} skills found"
    }

    # Score 2: Experience (max 25 points)
    exp_count = len(parsed_data.get("experience", []))
    if exp_count >= 3:
        exp_score = 25
    elif exp_count >= 1:
        exp_score = 15
    else:
        exp_score = 0
    score += exp_score
    breakdown["Experience"] = {
        "score": exp_score,
        "max":   25,
        "note":  f"{exp_count} experience entries found"
    }

    # Score 3: Education (max 20 points)
    edu_count = len(parsed_data.get("education", []))
    if edu_count >= 2:
        edu_score = 20
    elif edu_count >= 1:
        edu_score = 12
    else:
        edu_score = 0
    score += edu_score
    breakdown["Education"] = {
        "score": edu_score,
        "max":   20,
        "note":  f"{edu_count} education entries found"
    }

    # Score 4: Contact Info (max 15 points)
    contact     = parsed_data.get("contact_info", {})
    contact_score = 0
    if contact.get("email"):
        contact_score += 7
    if contact.get("phone"):
        contact_score += 5
    if contact.get("linkedin"):
        contact_score += 3
    score += contact_score
    breakdown["Contact Info"] = {
        "score": contact_score,
        "max":   15,
        "note":  "email, phone, linkedin"
    }

    # Score 5: Resume Length (max 10 points)
    word_count = parsed_data.get("word_count", 0)
    if 300 <= word_count <= 800:
        length_score = 10   # Ideal length
    elif 200 <= word_count < 300:
        length_score = 6    # A bit short
    elif word_count > 800:
        length_score = 6    # A bit long
    else:
        length_score = 2    # Too short
    score += length_score
    breakdown["Resume Length"] = {
        "score": length_score,
        "max":   10,
        "note":  f"{word_count} words"
    }

    return {
        "total_score": score,
        "max_score":   100,
        "percentage":  score,
        "grade":       _get_grade(score),
        "breakdown":   breakdown
    }


def _get_grade(score: int) -> str:
    """
    Converts a numeric score into a letter grade with label.
    """
    if score >= 85:
        return "A+ — Excellent"
    elif score >= 70:
        return "A — Very Good"
    elif score >= 55:
        return "B — Good"
    elif score >= 40:
        return "C — Average"
    else:
        return "D — Needs Improvement"


# ============================================================
# ERROR HELPER
# ============================================================

def _error_result(message: str) -> Dict:
    """
    Returns a standardized error dictionary.
    Used when parsing fails so app.py always gets the same structure.
    """
    return {
        "success":      False,
        "filename":     "",
        "raw_text":     "",
        "skills":       [],
        "education":    [],
        "experience":   [],
        "contact_info": {},
        "word_count":   0,
        "page_count":   0,
        "error":        message
    }