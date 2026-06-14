"""
modules/matcher.py
==================
PURPOSE:
Calculates how well a resume matches a job listing.
Produces a match percentage score and identifies matched/missing skills.

HOW SCORING WORKS:
  The score is calculated from 3 factors:

  1. SKILL MATCH (60 points max)
     How many of the job's required skills appear in the resume.
     Formula: (matched skills / total job skills) * 60

  2. TITLE MATCH (20 points max)
     Whether the candidate's experience titles match the job title.
     Checked using keyword matching.

  3. EXPERIENCE MATCH (20 points max)
     Whether the candidate seems to have relevant experience
     based on keywords in their resume text.

FINAL SCORE:
  0-39%   = Poor match (shown in red)
  40-69%  = Moderate match (shown in yellow)
  70-100% = Strong match (shown in green)

CONNECTS TO:
  - app.py calls calculate_match() when user clicks Match Resume
  - resume_parser.py provides resume skills and text
  - job_search.py provides job skills and description
  - charts.py uses the score to draw the gauge chart
"""

from typing import Dict, List, Tuple
from utils.helpers import get_skill_overlap, normalize_skill


# ============================================================
# MAIN MATCH FUNCTION
# ============================================================

def calculate_match(
    resume_data: Dict,
    job: Dict
) -> Dict:
    """
    Main function called by app.py to calculate resume-job match.

    Args:
        resume_data : Full parsed resume dictionary from resume_parser.py
                      Must contain 'skills', 'raw_text', and 'experience'
        job         : Full job dictionary from job_search.py
                      Must contain 'skills_required', 'title', 'description'

    Returns:
        Dictionary containing:
            score           - Final match percentage 0 to 100
            grade           - Text grade like "Strong Match"
            matched_skills  - Skills found in both resume and job
            missing_skills  - Skills job needs but resume lacks
            extra_skills    - Resume skills not required by job
            skill_score     - Points from skill matching (max 60)
            title_score     - Points from title matching (max 20)
            experience_score- Points from experience matching (max 20)
            recommendation  - Short advice string
            details         - Full breakdown dictionary
    """
    resume_skills   = resume_data.get("skills", [])
    resume_text     = resume_data.get("raw_text", "")
    job_skills      = job.get("skills_required", [])
    job_title       = job.get("title", "")
    job_description = job.get("description", "")

    # --- Step 1: Calculate skill match score (max 60 points) ---
    skill_result  = _calculate_skill_score(resume_skills, job_skills)
    skill_score   = skill_result["score"]

    # --- Step 2: Calculate title relevance score (max 20 points) ---
    title_score   = _calculate_title_score(resume_text, job_title)

    # --- Step 3: Calculate experience relevance score (max 20 points) ---
    exp_score     = _calculate_experience_score(
        resume_text, job_title, job_description
    )

    # --- Step 4: Add all scores together ---
    total_score   = min(100, skill_score + title_score + exp_score)

    # --- Step 5: Generate grade and recommendation ---
    grade, recommendation = _get_grade_and_recommendation(
        total_score,
        skill_result["matched"],
        skill_result["missing"]
    )

    return {
        "score":              total_score,
        "grade":              grade,
        "matched_skills":     skill_result["matched"],
        "missing_skills":     skill_result["missing"],
        "extra_skills":       skill_result["extra"],
        "skill_score":        skill_score,
        "title_score":        title_score,
        "experience_score":   exp_score,
        "recommendation":     recommendation,
        "details": {
            "total_job_skills":     len(job_skills),
            "total_resume_skills":  len(resume_skills),
            "matched_count":        len(skill_result["matched"]),
            "missing_count":        len(skill_result["missing"]),
            "skill_match_percent":  skill_result["match_percent"]
        }
    }


# ============================================================
# SKILL SCORE CALCULATION
# ============================================================

def _calculate_skill_score(
    resume_skills: List[str],
    job_skills: List[str]
) -> Dict:
    """
    Compares resume skills against job skills and returns a score.

    If the job has no skills listed, we give a neutral score of 30.
    This avoids penalizing candidates for incomplete job postings.

    Args:
        resume_skills : Skills extracted from resume
        job_skills    : Skills required by the job

    Returns:
        Dictionary with score, matched list, missing list, extra list
    """
    # If job has no skills listed, give neutral score
    if not job_skills:
        return {
            "score":         30,
            "matched":       [],
            "missing":       [],
            "extra":         resume_skills,
            "match_percent": 0
        }

    # If resume has no skills, score is zero
    if not resume_skills:
        return {
            "score":         0,
            "matched":       [],
            "missing":       job_skills,
            "extra":         [],
            "match_percent": 0
        }

    # Use helpers.py to find overlapping skills
    overlap = get_skill_overlap(resume_skills, job_skills)

    matched_count = len(overlap["matched"])
    total_required = len(job_skills)

    # Calculate match percentage
    match_percent = (matched_count / total_required) * 100

    # Convert to score out of 60
    skill_score = round((match_percent / 100) * 60)

    return {
        "score":         skill_score,
        "matched":       overlap["matched"],
        "missing":       overlap["missing"],
        "extra":         overlap["extra"],
        "match_percent": round(match_percent, 1)
    }


# ============================================================
# TITLE SCORE CALCULATION
# ============================================================

def _calculate_title_score(
    resume_text: str,
    job_title: str
) -> int:
    """
    Checks if the job title or related keywords appear in the resume.
    This simulates how ATS systems check for role relevance.

    Scoring:
      20 points - Exact job title found in resume
      15 points - Most title keywords found
      10 points - Some title keywords found
       5 points - At least one keyword found
       0 points - No relevant keywords found

    Args:
        resume_text : Full resume text
        job_title   : Job title from the listing

    Returns:
        Integer score between 0 and 20
    """
    if not resume_text or not job_title:
        return 5   # Neutral score when data is missing

    resume_lower    = resume_text.lower()
    job_title_lower = job_title.lower()

    # Check for exact title match first
    if job_title_lower in resume_lower:
        return 20

    # Split title into individual keywords and check each
    # Example: "Machine Learning Engineer" → ["machine", "learning", "engineer"]
    title_words = [
        word for word in job_title_lower.split()
        if len(word) > 2   # Skip very short words like "of", "a", "at"
    ]

    if not title_words:
        return 5

    # Count how many title words appear in resume
    found_words = sum(
        1 for word in title_words
        if word in resume_lower
    )

    match_ratio = found_words / len(title_words)

    if match_ratio >= 0.8:
        return 15
    elif match_ratio >= 0.5:
        return 10
    elif match_ratio > 0:
        return 5
    else:
        return 0


# ============================================================
# EXPERIENCE SCORE CALCULATION
# ============================================================

def _calculate_experience_score(
    resume_text: str,
    job_title: str,
    job_description: str
) -> int:
    """
    Checks if the resume shows relevant experience for the job.
    Looks for domain-specific keywords from the job description
    appearing in the resume text.

    Scoring:
      20 points - High keyword overlap (very relevant experience)
      15 points - Good keyword overlap
      10 points - Moderate keyword overlap
       5 points - Some keyword overlap
       0 points - No relevant keywords found

    Args:
        resume_text     : Full resume text
        job_title       : Job title for context
        job_description : Full job description text

    Returns:
        Integer score between 0 and 20
    """
    if not resume_text:
        return 0

    resume_lower = resume_text.lower()

    # Extract important keywords from job description
    # We focus on nouns and technical terms (words longer than 4 chars)
    if job_description:
        desc_words = set(
            word.lower().strip('.,()[]')
            for word in job_description.split()
            if len(word) > 4
        )
    else:
        # Fall back to job title words if no description
        desc_words = set(job_title.lower().split())

    if not desc_words:
        return 10   # Neutral score

    # Count how many job description keywords appear in resume
    found = sum(
        1 for word in desc_words
        if word in resume_lower
    )

    match_ratio = found / len(desc_words)

    if match_ratio >= 0.3:
        return 20
    elif match_ratio >= 0.2:
        return 15
    elif match_ratio >= 0.1:
        return 10
    elif match_ratio > 0:
        return 5
    else:
        return 0


# ============================================================
# GRADE AND RECOMMENDATION
# ============================================================

def _get_grade_and_recommendation(
    score: int,
    matched_skills: List[str],
    missing_skills: List[str]
) -> Tuple[str, str]:
    """
    Converts a numeric score into a grade label and recommendation text.

    Args:
        score          : Final match score 0-100
        matched_skills : List of skills that matched
        missing_skills : List of skills that are missing

    Returns:
        Tuple of (grade_string, recommendation_string)
    """
    missing_count = len(missing_skills)
    top_missing   = ", ".join(missing_skills[:3]) if missing_skills else ""

    if score >= 80:
        grade = "🟢 Excellent Match"
        rec   = (
            "Your profile is a strong fit for this role. "
            "Apply with confidence and tailor your cover letter "
            "to highlight your matched skills."
        )

    elif score >= 60:
        grade = "🟢 Strong Match"
        rec   = (
            "You are a good candidate for this role. "
            f"Consider learning {top_missing} to strengthen your application."
            if top_missing else
            "You are a good candidate for this role. Apply now."
        )

    elif score >= 40:
        grade = "🟡 Moderate Match"
        rec   = (
            f"You meet some requirements but are missing key skills. "
            f"Focus on learning: {top_missing}. "
            f"Apply while you learn these skills."
            if top_missing else
            "You meet some requirements for this role."
        )

    elif score >= 20:
        grade = "🔴 Weak Match"
        rec   = (
            f"Significant skill gaps exist for this role. "
            f"You need to develop: {top_missing}. "
            f"Consider applying to junior versions of this role first."
            if top_missing else
            "Consider building more relevant skills before applying."
        )

    else:
        grade = "🔴 Poor Match"
        rec   = (
            "This role requires skills very different from your current profile. "
            "Consider exploring similar but more entry-level positions, "
            "or invest time in learning the required technologies."
        )

    return grade, rec


# ============================================================
# BATCH MATCHING (Match resume against multiple jobs)
# ============================================================

def match_resume_to_all_jobs(
    resume_data: Dict,
    jobs: List[Dict]
) -> List[Dict]:
    """
    Matches a resume against a list of jobs and returns sorted results.
    Used to show the user which jobs they are best suited for.

    Args:
        resume_data : Parsed resume dictionary from resume_parser.py
        jobs        : List of job dictionaries from job_search.py

    Returns:
        List of jobs sorted by match score (highest first),
        with match_score and match_grade added to each job dictionary
    """
    results = []

    for job in jobs:
        match    = calculate_match(resume_data, job)
        job_copy = job.copy()

        # Add match info directly to the job dictionary
        job_copy["match_score"] = match["score"]
        job_copy["match_grade"] = match["grade"]
        job_copy["matched_skills"] = match["matched_skills"]
        job_copy["missing_skills"] = match["missing_skills"]

        results.append(job_copy)

    # Sort by match score highest to lowest
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results


# ============================================================
# QUICK SCORE (lightweight version for bulk display)
# ============================================================

def quick_score(
    resume_skills: List[str],
    job_skills: List[str]
) -> int:
    """
    Fast version of matching that only uses skills.
    Used when we need to show scores on many job cards quickly
    without the full calculation overhead.

    Args:
        resume_skills : Skills from resume
        job_skills    : Skills from job

    Returns:
        Integer match percentage 0-100
    """
    if not job_skills:
        return 50   # Neutral if job has no skills listed

    if not resume_skills:
        return 0

    # Normalize both lists for fair comparison
    norm_resume = {normalize_skill(s) for s in resume_skills}
    norm_job    = {normalize_skill(s) for s in job_skills}

    # Count matches
    matched = len(norm_resume.intersection(norm_job))
    total   = len(norm_job)

    return round((matched / total) * 100)