"""
modules/job_search.py
=====================
PURPOSE:
The job search engine for the entire app.
Supports two modes:
  1. Mock mode  - reads from data/mock_jobs.json (no API key needed)
  2. Real mode  - fetches live jobs from RapidAPI JSearch

HOW FALLBACK WORKS:
If real API fails for any reason, it automatically switches to mock data.
This ensures the app never crashes during a live demo.

CONNECTS TO:
  - app.py calls search_jobs() to get job listings
  - database.py logs every search automatically
  - utils/helpers.py used for skill extraction
"""

import os
import json
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.helpers import extract_skills_from_text, load_json_file

# Load environment variables from .env file
load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

# Path to our offline mock jobs data file
MOCK_JOBS_PATH = "data/mock_jobs.json"

# RapidAPI endpoint for JSearch — provides real job listings
RAPIDAPI_URL = "https://jsearch.p.rapidapi.com/search"

# Read API keys from .env file
RAPIDAPI_KEY      = os.getenv("RAPIDAPI_KEY", "")
USE_REAL_JOBS_API = os.getenv("USE_REAL_JOBS_API", "false").lower() == "true"


# ============================================================
# MAIN SEARCH FUNCTION
# ============================================================

def search_jobs(
    query: str,
    location: str = "",
    country: str = "India",
    experience: str = "Any",
    job_type: str = "Any",
    remote_only: bool = False,
    num_results: int = 10
) -> Dict:
    """
    Main function called by app.py to search for jobs.

    HOW IT DECIDES WHICH MODE TO USE:
    1. If USE_REAL_JOBS_API is true AND RAPIDAPI_KEY exists → try real API
    2. If real API fails OR keys are missing → fall back to mock data
    3. If USE_REAL_JOBS_API is false → go straight to mock data

    Args:
        query       : Job title or skill to search for (e.g. "Python Developer")
        location    : City or region (e.g. "Bangalore")
        country     : "India" or "Global"
        experience  : Experience level filter (e.g. "2-4 years")
        job_type    : Employment type filter (e.g. "Full-time")
        remote_only : If True, only show remote jobs
        num_results : Maximum number of results to return

    Returns:
        Dictionary with:
            jobs    - List of job dictionaries
            source  - "mock" or "api" (where data came from)
            count   - Total number of results
            error   - Error message if something went wrong (or None)
    """

    # Decide which mode to use
    if USE_REAL_JOBS_API and RAPIDAPI_KEY:
        result = _search_real_api(query, location, country, num_results)

        # If real API worked, return it
        if result["jobs"]:
            result["jobs"] = _apply_filters(
                result["jobs"], experience, job_type, remote_only, country
            )
            result["count"] = len(result["jobs"])
            return result

        # Real API failed — fall back to mock data silently
        mock_result = _search_mock_data(
            query, location, country,
            experience, job_type, remote_only, num_results
        )
        mock_result["error"] = (
            "Real API unavailable — showing demo data. "
            + (result.get("error") or "")
        )
        return mock_result

    # Default — use mock data
    return _search_mock_data(
        query, location, country,
        experience, job_type, remote_only, num_results
    )


# ============================================================
# MOCK DATA SEARCH
# ============================================================

def _search_mock_data(
    query: str,
    location: str = "",
    country: str = "India",
    experience: str = "Any",
    job_type: str = "Any",
    remote_only: bool = False,
    num_results: int = 10
) -> Dict:
    """
    Searches through our local mock_jobs.json file.
    This is the offline/demo mode — always works without any API key.

    HOW MATCHING WORKS:
    It checks if the search query appears in:
      - Job title
      - Company name
      - Job description
      - Skills required list
    """
    try:
        # Load all jobs from the JSON file
        all_jobs = load_json_file(MOCK_JOBS_PATH)

        if not all_jobs:
            return {
                "jobs":   [],
                "source": "mock",
                "count":  0,
                "error":  "Mock data file not found"
            }

        # Filter by country first
        if country != "Both":
            all_jobs = [
                job for job in all_jobs
                if job.get("country", "India") == country
            ]

        # Filter by search query
        query_lower = query.lower().strip()
        matched_jobs = []

        for job in all_jobs:
            # Check if query matches title, company, description, or skills
            title_match       = query_lower in job.get("title", "").lower()
            company_match     = query_lower in job.get("company", "").lower()
            description_match = query_lower in job.get("description", "").lower()
            skills_match      = any(
                query_lower in skill.lower()
                for skill in job.get("skills_required", [])
            )

            if title_match or company_match or description_match or skills_match:
                matched_jobs.append(job)

        # If no exact match found, return all jobs for that country
        # This gives users something to see even with unusual queries
        if not matched_jobs:
            matched_jobs = all_jobs

        # Apply additional filters
        matched_jobs = _apply_filters(
            matched_jobs, experience, job_type, remote_only, country
        )

        # Apply location filter if provided
        if location and location.strip():
            location_lower   = location.lower().strip()
            location_matched = [
                job for job in matched_jobs
                if location_lower in job.get("location", "").lower()
            ]
            # Only use location filter if it gives results
            if location_matched:
                matched_jobs = location_matched

        # Limit to requested number of results
        matched_jobs = matched_jobs[:num_results]

        return {
            "jobs":   matched_jobs,
            "source": "mock",
            "count":  len(matched_jobs),
            "error":  None
        }

    except Exception as e:
        return {
            "jobs":   [],
            "source": "mock",
            "count":  0,
            "error":  f"Error loading mock data: {str(e)}"
        }


# ============================================================
# REAL API SEARCH (RapidAPI JSearch)
# ============================================================

def _search_real_api(
    query: str,
    location: str = "",
    country: str = "India",
    num_results: int = 10
) -> Dict:
    """
    Fetches real job listings from RapidAPI JSearch.
    Only called when USE_REAL_JOBS_API=true and RAPIDAPI_KEY is set.

    JSearch aggregates jobs from LinkedIn, Indeed, Glassdoor and others.
    Free tier gives 200 requests per month — enough for demo purposes.
    """
    try:
        # Build the search query string
        # Append country context for better results
        location_context = location if location else (
            "India" if country == "India" else ""
        )
        full_query = f"{query} {location_context}".strip()

        # API request parameters
        params = {
            "query":          full_query,
            "page":           "1",
            "num_pages":      "1",
            "date_posted":    "month"
        }

        # Request headers with API key
        headers = {
            "X-RapidAPI-Key":  RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }

        # Make the API request with 10 second timeout
        response = requests.get(
            RAPIDAPI_URL,
            headers=headers,
            params=params,
            timeout=10
        )

        # Check if request was successful
        if response.status_code != 200:
            return {
                "jobs":   [],
                "source": "api",
                "count":  0,
                "error":  f"API returned status {response.status_code}"
            }

        data = response.json()

        # Parse API response into our standard job format
        raw_jobs  = data.get("data", [])
        parsed_jobs = []

        for i, job in enumerate(raw_jobs[:num_results]):
            parsed = _parse_api_job(job, i, country)
            parsed_jobs.append(parsed)

        return {
            "jobs":   parsed_jobs,
            "source": "api",
            "count":  len(parsed_jobs),
            "error":  None
        }

    except requests.exceptions.Timeout:
        return {
            "jobs":   [],
            "source": "api",
            "count":  0,
            "error":  "API request timed out"
        }
    except requests.exceptions.ConnectionError:
        return {
            "jobs":   [],
            "source": "api",
            "count":  0,
            "error":  "No internet connection"
        }
    except Exception as e:
        return {
            "jobs":   [],
            "source": "api",
            "count":  0,
            "error":  f"API error: {str(e)}"
        }


def _parse_api_job(raw_job: Dict, index: int, country: str) -> Dict:
    """
    Converts a raw JSearch API response job into our standard format.
    Our app expects a specific structure — this function creates that.

    Args:
        raw_job : Raw job dictionary from JSearch API
        index   : Job number (used to create unique ID)
        country : India or Global context

    Returns:
        Job dictionary matching our mock_jobs.json structure
    """
    # Extract salary information
    min_salary = raw_job.get("job_min_salary")
    max_salary = raw_job.get("job_max_salary")
    currency   = raw_job.get("job_salary_currency", "USD")

    if min_salary and max_salary:
        salary = f"{currency} {int(min_salary):,} - {int(max_salary):,}"
    elif min_salary:
        salary = f"{currency} {int(min_salary):,}+"
    else:
        salary = "Not disclosed"

    # Extract skills from job description using our helper function
    description    = raw_job.get("job_description", "")
    skills_found   = extract_skills_from_text(description)

    # Build the standardized job dictionary
    return {
        "id":             f"api_job_{index}_{raw_job.get('job_id', index)}",
        "title":          raw_job.get("job_title", "N/A"),
        "company":        raw_job.get("employer_name", "N/A"),
        "location":       (
            f"{raw_job.get('job_city', '')}, "
            f"{raw_job.get('job_country', '')}"
        ).strip(", "),
        "country":        country,
        "salary":         salary,
        "salary_numeric": min_salary or 0,
        "job_type":       raw_job.get("job_employment_type", "Full-time"),
        "experience":     raw_job.get("job_required_experience", {}).get(
                              "required_experience_in_months", "N/A"
                          ),
        "description":    description[:500] if description else "N/A",
        "skills_required": skills_found[:8],
        "apply_link":     raw_job.get("job_apply_link", "#"),
        "posted_date":    raw_job.get("job_posted_at_datetime_utc", "")[:10],
        "remote":         raw_job.get("job_is_remote", False),
        "notice_period":  "Immediate"
    }


# ============================================================
# FILTER FUNCTION
# ============================================================

def _apply_filters(
    jobs: List[Dict],
    experience: str = "Any",
    job_type: str = "Any",
    remote_only: bool = False,
    country: str = "Both"
) -> List[Dict]:
    """
    Applies additional filters to job results after searching.

    Filters available:
    - Experience level
    - Job type (Full-time, Part-time, Contract)
    - Remote only toggle
    - Country (India or Global)
    """
    filtered = jobs

    # Filter by remote
    if remote_only:
        filtered = [j for j in filtered if j.get("remote") is True]

    # Filter by job type
    if job_type and job_type != "Any":
        filtered = [
            j for j in filtered
            if job_type.lower() in j.get("job_type", "").lower()
        ]

    # Filter by experience
    if experience and experience != "Any":
        filtered = [
            j for j in filtered
            if experience.lower() in j.get("experience", "").lower()
        ]

    return filtered


# ============================================================
# HELPER FUNCTIONS FOR APP.PY
# ============================================================

def get_all_mock_jobs(country: str = "Both") -> List[Dict]:
    """
    Returns all mock jobs without any search filter.
    Used to populate the initial job listing on the dashboard.
    """
    all_jobs = load_json_file(MOCK_JOBS_PATH)

    if country != "Both":
        all_jobs = [
            job for job in all_jobs
            if job.get("country", "India") == country
        ]

    return all_jobs


def get_job_by_id(job_id: str) -> Optional[Dict]:
    """
    Finds and returns a single job by its ID.
    Used when user clicks on a job card to see full details.
    """
    all_jobs = load_json_file(MOCK_JOBS_PATH)
    for job in all_jobs:
        if job.get("id") == job_id:
            return job
    return None


def get_available_locations(country: str = "India") -> List[str]:
    """
    Returns list of unique locations from mock data.
    Used to populate the location filter dropdown in the sidebar.
    """
    all_jobs  = load_json_file(MOCK_JOBS_PATH)
    locations = set()

    for job in all_jobs:
        if country == "Both" or job.get("country") == country:
            loc = job.get("location", "")
            if loc:
                # Extract just the city name (before the comma)
                city = loc.split(",")[0].strip()
                locations.add(city)

    return sorted(list(locations))