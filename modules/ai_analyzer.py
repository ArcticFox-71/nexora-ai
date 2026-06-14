"""
modules/ai_analyzer.py
======================
PURPOSE:
All Google Gemini AI interactions happen in this file.
Every prompt sent to Gemini is written here as a function.

WHAT GEMINI DOES IN THIS PROJECT:
  1. Analyzes full resume and gives ATS feedback
  2. Suggests resume improvements
  3. Compares resume against a specific job description
  4. Recommends missing skills to learn
  5. Generates a career roadmap
  6. Answers career questions in a chat interface

MODEL USED:
  gemini-2.5-flash — latest and fastest Gemini model as of 2026

RATE LIMIT HANDLING:
  Free tier allows 15 requests per minute.
  All functions have try/except to handle quota errors gracefully.
  App shows a friendly message instead of crashing.

CONNECTS TO:
  - app.py calls these functions when user requests AI analysis
  - resume_parser.py provides the extracted resume text
  - job_search.py provides the job description for comparison
"""

import os
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

# Get API key from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Model name — always use latest working model
GEMINI_MODEL = "gemini-2.5-flash"

# Configure the Gemini library with our API key
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def _get_model():
    """
    Creates and returns a Gemini model instance.
    Called fresh for each request to avoid stale connections.

    Generation config controls how Gemini responds:
      temperature  - 0.7 means balanced between creative and factual
      max_tokens   - limits response length to avoid huge outputs
    """
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config={
            "temperature":       0.7,
            "max_output_tokens": 1500,
        }
    )


def _safe_generate(prompt: str, retries: int = 2) -> str:
    """
    Safely sends a prompt to Gemini with error handling and retry logic.

    WHY RETRIES?
    Sometimes the API is briefly busy and fails on first try.
    We wait 5 seconds and try again before giving up.

    Args:
        prompt  : The text prompt to send to Gemini
        retries : Number of times to retry on failure

    Returns:
        Gemini response text, or a friendly error message
    """
    if not GEMINI_API_KEY:
        return (
            "⚠️ Gemini API key not found. "
            "Please add your GEMINI_API_KEY to the .env file."
        )

    for attempt in range(retries + 1):
        try:
            model    = _get_model()
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            error_str = str(e).lower()

            # Rate limit error — wait and retry
            if "429" in str(e) or "quota" in error_str:
                if attempt < retries:
                    time.sleep(5)
                    continue
                return (
                    "⚠️ AI rate limit reached. "
                    "Please wait 1 minute and try again. "
                    "Gemini free tier allows 15 requests per minute."
                )

            # API key error
            if "api key" in error_str or "401" in str(e):
                return (
                    "⚠️ Invalid Gemini API key. "
                    "Please check your .env file and make sure "
                    "GEMINI_API_KEY is correct."
                )

            # Model not found
            if "404" in str(e) or "not found" in error_str:
                return (
                    "⚠️ Gemini model not available. "
                    "Please check your API key has access to gemini-2.5-flash."
                )

            # Any other error
            if attempt < retries:
                time.sleep(2)
                continue

            return f"⚠️ AI analysis failed: {str(e)}"

    return "⚠️ AI analysis failed after multiple attempts. Please try again."


# ============================================================
# FUNCTION 1: FULL RESUME ANALYSIS
# ============================================================

def analyze_resume(resume_text: str, skills: List[str]) -> Dict:
    """
    Sends the full resume to Gemini for comprehensive ATS-style analysis.
    This is the main analysis shown after uploading a resume.

    Args:
        resume_text : Full extracted text from the PDF
        skills      : List of skills already extracted by resume_parser.py

    Returns:
        Dictionary with:
            overall_feedback  - General resume quality assessment
            strengths         - What the resume does well
            weaknesses        - What needs improvement
            ats_tips          - Specific ATS optimization tips
            ats_score_reason  - Why it would score well or poorly in ATS
    """
    skills_str = ", ".join(skills) if skills else "None detected"

    prompt = f"""
You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.
Analyze the following resume and provide detailed, actionable feedback.

RESUME TEXT:
{resume_text[:3000]}

SKILLS DETECTED: {skills_str}

Please provide your analysis in EXACTLY this format with these exact headings:

OVERALL ASSESSMENT:
[Write 3-4 sentences about the overall quality and impression of this resume]

STRENGTHS:
[List 3-4 specific strengths of this resume, one per line starting with •]

AREAS FOR IMPROVEMENT:
[List 3-4 specific improvements needed, one per line starting with •]

ATS OPTIMIZATION TIPS:
[List 4-5 specific tips to make this resume more ATS-friendly, one per line starting with •]

MISSING SECTIONS:
[List any important resume sections that are missing or weak]

Keep your response practical, specific, and encouraging.
Focus on what will actually help the candidate get interviews.
"""

    response_text = _safe_generate(prompt)

    # Parse the structured response into a dictionary
    return {
        "full_analysis": response_text,
        "skills_count":  len(skills),
        "model_used":    GEMINI_MODEL
    }


# ============================================================
# FUNCTION 2: JOB MATCH ANALYSIS
# ============================================================

def analyze_job_match(
    resume_text: str,
    resume_skills: List[str],
    job: Dict
) -> Dict:
    """
    Compares a specific resume against a specific job description.
    Gives targeted advice on how to tailor the resume for that job.

    Args:
        resume_text   : Full extracted resume text
        resume_skills : Skills list from resume_parser.py
        job           : Full job dictionary from job_search.py

    Returns:
        Dictionary with match analysis and tailoring suggestions
    """
    resume_skills_str = ", ".join(resume_skills) if resume_skills else "None"
    job_skills_str    = ", ".join(
        job.get("skills_required", [])
    ) if job.get("skills_required") else "Not specified"

    prompt = f"""
You are an expert career coach helping a candidate tailor their resume for a specific job.

JOB DETAILS:
Title    : {job.get('title', 'N/A')}
Company  : {job.get('company', 'N/A')}
Location : {job.get('location', 'N/A')}
Required Skills: {job_skills_str}

Job Description:
{job.get('description', 'Not provided')[:1000]}

CANDIDATE RESUME (summary):
{resume_text[:2000]}

CANDIDATE SKILLS: {resume_skills_str}

Please provide analysis in EXACTLY this format:

MATCH SUMMARY:
[2-3 sentences on how well this candidate fits this specific role]

HOW TO TAILOR YOUR RESUME:
[List 4-5 specific changes to make the resume match this job better, starting with •]

SKILLS TO HIGHLIGHT:
[List the skills from the resume that are most relevant to this job, starting with •]

SKILLS TO ACQUIRE:
[List the required skills the candidate is missing and how to learn them, starting with •]

INTERVIEW PREPARATION TIPS:
[List 3-4 tips for preparing for an interview at this specific company, starting with •]

Be specific and actionable. Mention the company name and job title in your response.
"""

    response_text = _safe_generate(prompt)

    return {
        "match_analysis": response_text,
        "job_title":      job.get("title", ""),
        "company":        job.get("company", ""),
        "model_used":     GEMINI_MODEL
    }


# ============================================================
# FUNCTION 3: CAREER ROADMAP
# ============================================================

def generate_career_roadmap(
    skills: List[str],
    target_role: str,
    experience_level: str = "fresher"
) -> str:
    """
    Generates a personalized career roadmap based on current skills
    and the target job role the candidate wants to reach.

    Args:
        skills           : List of skills the candidate already has
        target_role      : The job role they want (e.g. "ML Engineer")
        experience_level : "fresher", "junior", or "senior"

    Returns:
        Formatted roadmap text from Gemini
    """
    skills_str = ", ".join(skills) if skills else "No technical skills listed"

    prompt = f"""
You are a senior tech career mentor helping a {experience_level} candidate
build their career path toward becoming a {target_role}.

CANDIDATE'S CURRENT SKILLS: {skills_str}

Create a detailed, realistic career roadmap in EXACTLY this format:

CAREER ROADMAP: {target_role.upper()}

CURRENT POSITION ASSESSMENT:
[Assess where the candidate stands right now based on their skills]

PHASE 1 — FOUNDATION (Months 1-3):
[List 4-5 specific skills or concepts to learn first, starting with •]

PHASE 2 — BUILDING EXPERTISE (Months 4-6):
[List 4-5 intermediate skills to develop, starting with •]

PHASE 3 — JOB READY (Months 7-9):
[List 4-5 advanced skills and portfolio projects to complete, starting with •]

RECOMMENDED RESOURCES:
[List 4-5 specific free resources like courses, websites, or certifications, starting with •]

INDIAN JOB MARKET INSIGHT:
[2-3 sentences about demand for this role in India, typical salary, and top companies hiring]

Keep advice practical for the Indian tech job market.
Mention specific platforms like LeetCode, Coursera, NPTEL where relevant.
"""

    return _safe_generate(prompt)


# ============================================================
# FUNCTION 4: SKILL GAP ANALYSIS
# ============================================================

def analyze_skill_gap(
    resume_skills: List[str],
    job_skills: List[str],
    job_title: str
) -> str:
    """
    Deep analysis of the skill gap between what the candidate has
    and what a specific job requires.

    Args:
        resume_skills : Skills from the candidate's resume
        job_skills    : Skills required by the job
        job_title     : Name of the job role

    Returns:
        Formatted skill gap analysis text from Gemini
    """
    have_str    = ", ".join(resume_skills) if resume_skills else "None listed"
    need_str    = ", ".join(job_skills) if job_skills else "None specified"

    prompt = f"""
You are a technical skills advisor analyzing the skill gap for a {job_title} position.

SKILLS CANDIDATE HAS: {have_str}
SKILLS JOB REQUIRES:  {need_str}

Provide analysis in EXACTLY this format:

SKILL GAP ANALYSIS FOR: {job_title.upper()}

SKILLS YOU ALREADY HAVE:
[List the matching skills and why they are valuable for this role, starting with •]

CRITICAL MISSING SKILLS:
[List the most important missing skills that are deal-breakers, starting with •]

NICE-TO-HAVE MISSING SKILLS:
[List missing skills that are helpful but not essential, starting with •]

30-DAY LEARNING PLAN:
[List specific actions to take in the next 30 days to close the gap, starting with •]

FREE LEARNING RESOURCES:
[List specific free resources for the top missing skills, starting with •]

Be honest but encouraging. Prioritize the most impactful skills to learn first.
"""

    return _safe_generate(prompt)


# ============================================================
# FUNCTION 5: RESUME IMPROVEMENT SUGGESTIONS
# ============================================================

def suggest_resume_improvements(
    resume_text: str,
    target_role: str
) -> str:
    """
    Gives specific line-by-line suggestions to improve the resume
    for a target job role.

    Args:
        resume_text : Full extracted resume text
        target_role : The type of job they are applying for

    Returns:
        Formatted improvement suggestions from Gemini
    """
    prompt = f"""
You are a professional resume writer helping optimize a resume for {target_role} positions.

CURRENT RESUME:
{resume_text[:2500]}

TARGET ROLE: {target_role}

Provide specific improvements in EXACTLY this format:

RESUME IMPROVEMENT REPORT

SUMMARY SECTION:
[Write an improved professional summary they can use directly, in 3-4 sentences]

BULLET POINT IMPROVEMENTS:
[Show 3-4 examples of weak bullet points rewritten with stronger action verbs and metrics, starting with •]

KEYWORDS TO ADD:
[List 8-10 important keywords for {target_role} that should appear in the resume, starting with •]

FORMATTING TIPS:
[List 4-5 formatting improvements to make the resume more readable, starting with •]

ATS SCORE BOOSTERS:
[List 3-4 specific changes that will improve ATS scan score, starting with •]

Be direct and specific. Give examples wherever possible.
"""

    return _safe_generate(prompt)


# ============================================================
# FUNCTION 6: QUICK CHAT (Career Q&A)
# ============================================================

def career_chat(
    question: str,
    context: str = "",
    chat_history: List[Dict] = None
) -> str:
    """
    Answers career-related questions from the user.
    Powers the AI Career Chat feature in the app.

    Args:
        question      : The user's question
        context       : Optional resume context to personalize answers
        chat_history  : Previous messages for conversation continuity

    Returns:
        Gemini's answer as formatted text
    """
    # Build context string if resume data is available
    context_section = ""
    if context:
        context_section = f"""
CANDIDATE CONTEXT (use this to personalize your answer):
{context[:500]}
"""

    # Build conversation history string
    history_section = ""
    if chat_history:
        history_lines = []
        for msg in chat_history[-4:]:  # Only last 4 messages for context
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.get('content', '')[:200]}")
        history_section = "\n".join(history_lines)
        history_section = f"\nPREVIOUS CONVERSATION:\n{history_section}\n"

    prompt = f"""
You are an expert AI career assistant specializing in the Indian tech job market.
You help fresh graduates and young professionals navigate their careers.
{context_section}
{history_section}

USER QUESTION: {question}

Instructions:
- Give practical, actionable advice
- Be encouraging but honest
- Keep response under 300 words
- Use bullet points for lists
- Mention Indian job market specifics when relevant
- If question is about salary, mention Indian LPA format
"""

    return _safe_generate(prompt)


# ============================================================
# FUNCTION 7: MOCK INTERVIEW QUESTIONS
# ============================================================

def generate_interview_questions(
    job_title: str,
    skills: List[str],
    company: str = ""
) -> str:
    """
    Generates relevant interview questions for a specific job role.
    Helps candidates prepare before applying.

    Args:
        job_title : The role they are interviewing for
        skills    : Their technical skills
        company   : Optional company name for company-specific questions

    Returns:
        Formatted list of interview questions from Gemini
    """
    skills_str      = ", ".join(skills[:10]) if skills else "General tech skills"
    company_section = f"at {company}" if company else ""

    prompt = f"""
You are an experienced technical interviewer preparing questions for a {job_title} role {company_section}.

CANDIDATE SKILLS: {skills_str}

Generate interview questions in EXACTLY this format:

INTERVIEW PREPARATION: {job_title.upper()}

TECHNICAL QUESTIONS (likely to be asked):
[List 5 technical questions specific to this role, starting with Q1., Q2., etc.]

BEHAVIORAL QUESTIONS:
[List 3 behavioral questions using STAR method format, starting with Q1., Q2., Q3.]

COMPANY/ROLE SPECIFIC QUESTIONS:
[List 3 questions about the company or role the candidate should prepare for, starting with Q1., Q2., Q3.]

QUESTIONS TO ASK THE INTERVIEWER:
[List 3 smart questions the candidate should ask, starting with •]

PREPARATION TIPS:
[List 3 specific tips for this type of interview, starting with •]

Keep questions realistic and based on actual interview patterns in Indian tech companies.
"""

    return _safe_generate(prompt)