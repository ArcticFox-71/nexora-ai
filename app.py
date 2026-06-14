"""
app.py
======
PURPOSE:
Main entry point for the AI Job Assistant application.
This is the ONLY file you run to start the entire app.

HOW TO RUN:
    streamlit run app.py

WHAT THIS FILE DOES:
  - Configures the Streamlit page settings
  - Loads custom CSS styling
  - Initializes the database on first run
  - Builds the complete UI with 5 tabs:
      Tab 1: Job Search
      Tab 2: Resume Analyzer
      Tab 3: Job Matcher
      Tab 4: Saved Jobs
      Tab 5: Career Chat

CONNECTS TO:
  Every single module in the project is imported here.
"""

import streamlit as st
import os
from dotenv import load_dotenv

# ── Module imports ──────────────────────────────────────────
from modules.database      import (
    initialize_database, save_job, get_saved_jobs,
    delete_saved_job, is_job_saved, log_search,
    get_search_history, save_resume_analysis,
    get_resume_history, track_application,
    get_applications, update_application_status,
    get_dashboard_stats
)
from modules.job_search    import (
    search_jobs, get_all_mock_jobs,
    get_available_locations
)
from modules.resume_parser import parse_resume, calculate_resume_score
from modules.ai_analyzer   import (
    analyze_resume, analyze_job_match,
    generate_career_roadmap, analyze_skill_gap,
    suggest_resume_improvements, career_chat,
    generate_interview_questions
)
from modules.matcher       import (
    calculate_match, match_resume_to_all_jobs, quick_score
)
from modules.charts        import (
    create_match_gauge, create_skill_gap_chart,
    create_resume_score_chart, create_skills_distribution_chart,
    create_score_breakdown_chart, create_country_distribution_chart
)
from utils.helpers         import (
    generate_job_card_html, generate_match_result_html,
    validate_pdf, validate_search_query, load_css
)

# Load environment variables
load_dotenv()


# ============================================================
# PAGE CONFIGURATION
# Must be the very first Streamlit call in the file
# ============================================================

st.set_page_config(
    page_title     = "Nexora AI",
    page_icon      =  "⚡",
    layout         = "wide",
    initial_sidebar_state = "expanded"
)


# ============================================================
# LOAD CUSTOM CSS
# ============================================================

def load_custom_css():
    """Reads assets/style.css and injects it into the Streamlit app."""
    css = load_css("assets/style.css")
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_custom_css()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

# This runs once when the app starts
# Creates all tables if they don't already exist
initialize_database()


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
# Streamlit reruns the entire script on every interaction.
# Session state persists data between reruns.

if "resume_data"      not in st.session_state:
    st.session_state.resume_data      = None   # Parsed resume dictionary
if "search_results"   not in st.session_state:
    st.session_state.search_results   = []     # Last search results
if "selected_job"     not in st.session_state:
    st.session_state.selected_job     = None   # Job selected for matching
if "chat_history"     not in st.session_state:
    st.session_state.chat_history     = []     # Career chat messages
if "last_query"       not in st.session_state:
    st.session_state.last_query       = ""     # Last search query
if "ai_analysis"      not in st.session_state:
    st.session_state.ai_analysis      = None   # Last AI analysis result
if "match_result"     not in st.session_state:
    st.session_state.match_result     = None   # Last match calculation


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    """Builds the left sidebar with navigation and quick stats."""

    with st.sidebar:
        # App logo and title
        st.markdown("""
        <div style='text-align:center; padding: 10px 0 20px 0;'>
           <div style='margin-bottom:8px;'>
                <svg width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#a78bfa"/>
                            <stop offset="100%" style="stop-color:#60a5fa"/>
                        </linearGradient>
                    </defs>
                    <rect width="56" height="56" rx="14" fill="url(#logoGrad)" opacity="0.15"/>
                    <rect width="56" height="56" rx="14" fill="none" stroke="url(#logoGrad)" stroke-width="1.5"/>
                    <path d="M28 12 L32 24 L44 24 L34 32 L38 44 L28 36 L18 44 L22 32 L12 24 L24 24 Z" fill="url(#logoGrad)"/>
                    <circle cx="28" cy="28" r="5" fill="white" opacity="0.9"/>
                </svg>
            </div>
            <div style='font-size:24px; font-weight:900;
                        background:linear-gradient(90deg,#a78bfa,#60a5fa);
                        -webkit-background-clip:text;
                        -webkit-text-fill-color:transparent;
                        letter-spacing:-0.5px;'>
                Nexora AI
            </div>
            <div style='font-size:11px; color:#6b7280; margin-top:4px;
                        letter-spacing:1px; text-transform:uppercase;'>
                Career Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Dashboard statistics
        stats = get_dashboard_stats()
        st.markdown("**📊 Your Activity**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Saved Jobs",   stats["saved_jobs"])
            st.metric("Resumes",      stats["resumes_analyzed"])
        with col2:
            st.metric("Searches",     stats["total_searches"])
            st.metric("Applications", stats["applications"])

        st.divider()

        # Country toggle — India or Global
        st.markdown("**🌍 Market**")
        country = st.radio(
            "Select market",
            ["India 🇮🇳", "Global 🌍", "Both"],
            index   = 0,
            label_visibility = "collapsed"
        )
        # Store clean country name in session state
        country_map = {
            "India 🇮🇳": "India",
            "Global 🌍":  "Global",
            "Both":       "Both"
        }
        st.session_state["selected_country"] = country_map[country]

        st.divider()

        # Resume status indicator
        st.markdown("**📄 Resume Status**")
        resume_data = st.session_state.get("resume_data", None)
        if resume_data and resume_data.get("success"):
            st.markdown(
                f'<div style="background:rgba(52,211,153,0.15);'
                f'border:1px solid #34d399;border-radius:10px;padding:10px;">'
                f'<div style="color:#34d399;font-weight:600;">✅ Resume Loaded</div>'
                f'<div style="color:#e2e8f0;font-size:13px;margin-top:4px;">'
                f'{resume_data["filename"]}</div>'
                f'<div style="color:#9ca3af;font-size:12px;margin-top:2px;">'
                f'{len(resume_data["skills"])} skills • '
                f'{resume_data["word_count"]} words • '
                f'{resume_data["page_count"]} page(s)</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="background:rgba(96,165,250,0.15);'
                'border:1px solid #60a5fa;border-radius:10px;padding:10px;">'
                '<div style="color:#60a5fa;font-size:13px;">📤 No resume uploaded yet</div>'
                '<div style="color:#6b7280;font-size:11px;margin-top:4px;">'
                'Go to Resume Analyzer tab to upload</div>'
                '</div>',
                unsafe_allow_html=True
            )

        st.divider()

        # Recent searches
        history = get_search_history(limit=5)
        if history:
            st.markdown("**🕐 Recent Searches**")
            for h in history:
                st.caption(f"🔍 {h['query']}")

        st.divider()

        # App info
        st.markdown("""
        <div style='font-size:11px; color:#6b7280; text-align:center;'>
            Built with Streamlit + Gemini AI<br>
            
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 1: JOB SEARCH
# ============================================================

def render_job_search_tab():
    """Builds the Job Search tab with search bar, filters, and job cards."""

    st.markdown(
        '<div class="section-header">🔍 Job Search</div>',
        unsafe_allow_html=True
    )

    # ── Search Bar ───────────────────────────────────────────
    col1, col2, col3 = st.columns([3, 2, 1])

    with col1:
        query = st.text_input(
            "Job Title or Skill",
            placeholder = "e.g. Python Developer, React, Machine Learning...",
            value       = st.session_state.last_query
        )
    with col2:
        location = st.text_input(
            "Location (optional)",
            placeholder = "e.g. Bangalore, Mumbai, Remote..."
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("🔍 Search", use_container_width=True)

    # ── Filters Row ──────────────────────────────────────────
    with st.expander("⚙️ Advanced Filters", expanded=False):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)

        with fcol1:
            experience = st.selectbox(
                "Experience",
                ["Any", "0-2 years", "2-4 years", "3-5 years", "5+ years"]
            )
        with fcol2:
            job_type = st.selectbox(
                "Job Type",
                ["Any", "Full-time", "Part-time", "Contract", "Internship"]
            )
        with fcol3:
            remote_only = st.checkbox("Remote Only 🏠")
        with fcol4:
            num_results = st.slider("Max Results", 5, 12, 10)

    # ── Perform Search ───────────────────────────────────────
    country = st.session_state.get("selected_country", "India")

    if search_clicked:
        is_valid, error_msg = validate_search_query(query)
        if not is_valid:
            st.error(error_msg)
        else:
            with st.spinner("🔍 Searching for jobs..."):
                result = search_jobs(
                    query       = query,
                    location    = location,
                    country     = country if country != "Both" else "India",
                    experience  = experience,
                    job_type    = job_type,
                    remote_only = remote_only,
                    num_results = num_results
                )

            # Save to session state for display
            st.session_state.search_results = result["jobs"]
            st.session_state.last_query     = query

            # Log search to database
            log_search(query, location, country, result["count"])

            # Show source info
            if result["source"] == "mock":
                st.info(
                    "📦 Showing demo job data. "
                    "Add RAPIDAPI_KEY to .env for live jobs."
                )
            if result.get("error"):
                st.warning(f"⚠️ {result['error']}")

    # ── Show Initial Jobs (before any search) ────────────────
    jobs_to_display = st.session_state.search_results

    if not jobs_to_display:
        # Show all mock jobs by default
        jobs_to_display = get_all_mock_jobs(
            country if country != "Both" else "Both"
        )

    # ── Results Header ───────────────────────────────────────
    st.markdown(
        f"<div style='color:#9ca3af; margin:12px 0;'>"
        f"Showing {len(jobs_to_display)} jobs"
        f"{'  •  ' + st.session_state.last_query if st.session_state.last_query else ''}"
        f"</div>",
        unsafe_allow_html=True
    )

    # ── Job Cards ────────────────────────────────────────────
    for job in jobs_to_display:

        # Show quick match score if resume is uploaded
        if st.session_state.resume_data:
            score = quick_score(
                st.session_state.resume_data.get("skills", []),
                job.get("skills_required", [])
            )
            score_color = (
                "#34d399" if score >= 70
                else "#fbbf24" if score >= 40
                else "#f87171"
            )
            st.markdown(
                f'<div style="float:right; margin-top:-10px;">'
                f'<span style="background:{score_color}20; '
                f'border:1px solid {score_color}; color:{score_color}; '
                f'padding:3px 12px; border-radius:20px; font-size:13px; '
                f'font-weight:600;">Match: {score}%</span></div>',
                unsafe_allow_html=True
            )

        # Render the job card HTML
        st.markdown(generate_job_card_html(job), unsafe_allow_html=True)

        # Action buttons below each card
        bcol1, bcol2, bcol3, bcol4 = st.columns([2, 2, 2, 4])

        with bcol1:
            already_saved = is_job_saved(job.get("id", ""))
            if already_saved:
                st.success("✅ Saved", icon=None)
            else:
                if st.button(
                    "💾 Save",
                    key=f"save_{job.get('id')}",
                    use_container_width=True
                ):
                    ok, msg = save_job(job)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning(msg)

        with bcol2:
            if st.button(
                "🎯 Match Resume",
                key=f"match_{job.get('id')}",
                use_container_width=True
            ):
                st.session_state.selected_job = job
                st.info("✅ Job selected! Go to Job Matcher tab.")

        with bcol3:
            if st.button(
                "❓ Interview Prep",
                key=f"interview_{job.get('id')}",
                use_container_width=True
            ):
                if st.session_state.resume_data:
                    with st.spinner("Generating interview questions..."):
                        questions = generate_interview_questions(
                            job_title = job.get("title", ""),
                            skills    = st.session_state.resume_data.get(
                                "skills", []
                            ),
                            company   = job.get("company", "")
                        )
                    st.markdown(
                        f'<div class="ai-box">{questions}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.warning(
                        "Upload your resume first to get "
                        "personalized interview questions."
                    )

        with bcol4:
            apply_link = job.get("apply_link", "#")
            st.markdown(
                f'<a href="{apply_link}" target="_blank">'
                f'<button style="background:linear-gradient(135deg,#059669,#34d399);'
                f'color:white;border:none;border-radius:8px;padding:8px 20px;'
                f'font-weight:600;cursor:pointer;width:100%;">'
                f'🚀 Apply Now</button></a>',
                unsafe_allow_html=True
            )

        st.markdown("---")


# ============================================================
# TAB 2: RESUME ANALYZER
# ============================================================

def render_resume_tab():
    """Builds the Resume Analyzer tab with PDF upload and AI analysis."""

    st.markdown(
        '<div class="section-header">📄 Resume Analyzer</div>',
        unsafe_allow_html=True
    )

    # ── Upload Section ───────────────────────────────────────
    st.markdown(
        '<div style="font-size:18px;font-weight:600;color:#a78bfa;margin-bottom:8px;">📤 Upload Your Resume</div>',
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader(
        "PDF format only • Max 5MB",
        type             = ["pdf"],
        label_visibility = "visible"
    )

    

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        is_valid, error_msg = validate_pdf(uploaded_file)
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return

        # Parse the resume
        with st.spinner("📖 Reading your resume..."):
            resume_data = parse_resume(uploaded_file)

        if not resume_data["success"]:
            st.error(f"❌ {resume_data['error']}")
            return

        # Save to session state so other tabs can use it
        st.session_state.resume_data = resume_data
        st.success(
            f"✅ Resume parsed successfully! "
            f"Found {len(resume_data['skills'])} skills."
        )

    # ── Display Analysis if Resume is Loaded ─────────────────
    if st.session_state.resume_data:
        resume = st.session_state.resume_data

        # Tabs for different analysis views
        r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs([
            "📊 Overview",
            "🤖 AI Analysis",
            "🛠️ Skills",
            "📈 Improvements"
        ])

        # ── Overview Tab ─────────────────────────────────────
        with r_tab1:
            # Quick metrics row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Skills Found",  len(resume["skills"]))
            with m2:
                st.metric("Word Count",    resume["word_count"])
            with m3:
                st.metric("Pages",         resume["page_count"])
            with m4:
                score_data = calculate_resume_score(resume)
                st.metric("Resume Score",  f"{score_data['total_score']}/100")

            st.markdown("---")

            # Two column layout
            oc1, oc2 = st.columns(2)

            with oc1:
                # Resume quality chart
                st.plotly_chart(
                    create_resume_score_chart(score_data["breakdown"]),
                    use_container_width=True
                )

                # Grade display
                st.markdown(
                    f'<div style="text-align:center; padding:10px;">'
                    f'<span style="font-size:14px; color:#9ca3af;">Grade: </span>'
                    f'<span style="font-size:18px; font-weight:700; color:#a78bfa;">'
                    f'{score_data["grade"]}</span></div>',
                    unsafe_allow_html=True
                )

            with oc2:
                # Contact info
                contact = resume.get("contact_info", {})
                st.markdown("**📬 Contact Information Detected**")

                if contact.get("email"):
                    st.markdown(f"📧 {contact['email']}")
                else:
                    st.warning("⚠️ No email found — add it to your resume!")

                if contact.get("phone"):
                    st.markdown(f"📱 {contact['phone']}")
                else:
                    st.warning("⚠️ No phone found — add it to your resume!")

                if contact.get("linkedin"):
                    st.markdown(f"💼 {contact['linkedin']}")

                if contact.get("github"):
                    st.markdown(f"🐙 {contact['github']}")

                st.markdown("---")

                # Education
                education = resume.get("education", [])
                if education:
                    st.markdown("**🎓 Education Detected**")
                    for edu in education[:3]:
                        st.markdown(
                            f"• {edu.get('degree', 'N/A')} "
                            f"{'— ' + edu['year'] if edu.get('year') else ''}"
                        )

        # ── AI Analysis Tab ──────────────────────────────────
        with r_tab2:
            st.markdown("**🤖 Gemini AI Resume Analysis**")
            st.caption(
                "Powered by Gemini 2.5 Flash — "
                "ATS-style feedback on your resume"
            )

            if st.button(
                "🚀 Analyze My Resume with AI",
                use_container_width=True
            ):
                with st.spinner(
                    "🤖 Gemini is analyzing your resume..."
                ):
                    ai_result = analyze_resume(
                        resume["raw_text"],
                        resume["skills"]
                    )
                    st.session_state.ai_analysis = ai_result

                    # Save to database
                    score_data = calculate_resume_score(resume)
                    save_resume_analysis(
                        filename       = resume["filename"],
                        extracted_text = resume["raw_text"],
                        skills         = resume["skills"],
                        ai_analysis    = ai_result["full_analysis"],
                        ats_score      = score_data["total_score"]
                    )

            if st.session_state.ai_analysis:
                analysis = st.session_state.ai_analysis
                st.markdown(
                    f'<div class="ai-box">'
                    f'{analysis["full_analysis"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.caption(
                    f"Analysis by {analysis['model_used']}"
                )

        # ── Skills Tab ───────────────────────────────────────
        with r_tab3:
            skills = resume.get("skills", [])

            if skills:
                st.markdown(
                    f"**🛠️ {len(skills)} Skills Detected in Your Resume**"
                )

                # Display all skills as tags
                skills_html = " ".join([
                    f'<span class="skill-tag">{s}</span>'
                    for s in skills
                ])
                st.markdown(
                    f'<div style="line-height:2.5;">{skills_html}</div>',
                    unsafe_allow_html=True
                )

                st.markdown("---")

                # Roadmap generator
                st.markdown("**🗺️ Generate Career Roadmap**")
                target_role = st.text_input(
                    "Target Role",
                    placeholder = "e.g. ML Engineer, Full Stack Developer..."
                )
                exp_level = st.selectbox(
                    "Your Level",
                    ["fresher", "junior", "mid-level", "senior"]
                )

                if st.button("🗺️ Generate Roadmap"):
                    if target_role:
                        with st.spinner("Building your roadmap..."):
                            roadmap = generate_career_roadmap(
                                skills           = skills,
                                target_role      = target_role,
                                experience_level = exp_level
                            )
                        st.markdown(
                            f'<div class="ai-box">{roadmap}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.warning("Please enter a target role first.")
            else:
                st.warning(
                    "No skills detected. "
                    "Make sure your resume has a Skills section."
                )

        # ── Improvements Tab ─────────────────────────────────
        with r_tab4:
            st.markdown("**📈 Resume Improvement Suggestions**")

            target = st.text_input(
                "What role are you targeting?",
                placeholder = "e.g. Python Developer, Data Scientist..."
            )

            if st.button("✨ Get Improvement Suggestions"):
                if target:
                    with st.spinner("Generating suggestions..."):
                        suggestions = suggest_resume_improvements(
                            resume["raw_text"], target
                        )
                    st.markdown(
                        f'<div class="ai-box">{suggestions}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.warning("Please enter a target role first.")

    else:
        # No resume uploaded yet
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#9ca3af;">
            <div style="font-size:48px;">📄</div>
            <div style="font-size:18px; margin-top:12px;">
                Upload your resume above to get started
            </div>
            <div style="font-size:13px; margin-top:8px;">
                You will get ATS analysis, skill detection,
                career roadmap, and improvement suggestions
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 3: JOB MATCHER
# ============================================================

def render_matcher_tab():
    """Builds the Job Matcher tab to compare resume against a job."""

    st.markdown(
        '<div class="section-header">🎯 Job Matcher</div>',
        unsafe_allow_html=True
    )

    # Check prerequisites
    if not st.session_state.resume_data:
        st.warning(
            "⚠️ Please upload your resume in the "
            "Resume Analyzer tab first."
        )
        return

    # Select job to match against
    st.markdown("**Select a job to match your resume against:**")

    jobs     = get_all_mock_jobs("Both")
    job_options = {
        f"{j['title']} @ {j['company']} ({j['country']})": j
        for j in jobs
    }

    # Pre-select if user clicked Match from search tab
    default_index = 0
    if st.session_state.selected_job:
        sel_key = (
            f"{st.session_state.selected_job['title']} @ "
            f"{st.session_state.selected_job['company']} "
            f"({st.session_state.selected_job['country']})"
        )
        keys = list(job_options.keys())
        if sel_key in keys:
            default_index = keys.index(sel_key)

    selected_label = st.selectbox(
        "Choose Job",
        options = list(job_options.keys()),
        index   = default_index,
        label_visibility = "collapsed"
    )

    selected_job = job_options[selected_label]

    # Match button
    if st.button(
        "🎯 Calculate Match Score",
        use_container_width=True
    ):
        with st.spinner("Calculating match..."):
            match_result = calculate_match(
                st.session_state.resume_data,
                selected_job
            )
            st.session_state.match_result = match_result

    # Display match results
    if st.session_state.match_result:
        result = st.session_state.match_result

        st.markdown("---")

        # Two column layout for results
        mc1, mc2 = st.columns(2)

        with mc1:
            # Gauge chart
            st.plotly_chart(
                create_match_gauge(result["score"]),
                use_container_width=True
            )
            # Grade
            st.markdown(
                f'<div style="text-align:center; font-size:16px; '
                f'font-weight:700; color:#a78bfa;">'
                f'{result["grade"]}</div>',
                unsafe_allow_html=True
            )
            # Recommendation
            st.markdown(
                f'<div style="text-align:center; font-size:13px; '
                f'color:#9ca3af; padding:8px;">'
                f'{result["recommendation"]}</div>',
                unsafe_allow_html=True
            )

        with mc2:
            # Score breakdown chart
            st.plotly_chart(
                create_score_breakdown_chart(result),
                use_container_width=True
            )

        st.markdown("---")

        # Matched and missing skills
        st.markdown(
            generate_match_result_html(result),
            unsafe_allow_html=True
        )

        st.markdown("---")

        # AI-powered match analysis
        st.markdown("**🤖 AI Match Analysis**")
        if st.button("Get AI Analysis for This Match"):
            with st.spinner("Gemini is analyzing the match..."):
                ai_match = analyze_job_match(
                    st.session_state.resume_data["raw_text"],
                    st.session_state.resume_data["skills"],
                    selected_job
                )
            st.markdown(
                f'<div class="ai-box">'
                f'{ai_match["match_analysis"]}'
                f'</div>',
                unsafe_allow_html=True
            )

        # Skill gap analysis
        if result["missing_skills"]:
            st.markdown("**📚 Skill Gap Analysis**")
            if st.button("Analyze Skill Gaps"):
                with st.spinner("Analyzing skill gaps..."):
                    gap_analysis = analyze_skill_gap(
                        st.session_state.resume_data["skills"],
                        selected_job.get("skills_required", []),
                        selected_job.get("title", "")
                    )
                st.markdown(
                    f'<div class="ai-box">{gap_analysis}</div>',
                    unsafe_allow_html=True
                )

        # Skill gap chart
        if result["matched_skills"] or result["missing_skills"]:
            st.plotly_chart(
                create_skill_gap_chart(
                    result["matched_skills"],
                    result["missing_skills"]
                ),
                use_container_width=True
            )

        # Track application button
        st.markdown("---")
        if st.button(
            "📝 Track This Application",
            use_container_width=True
        ):
            ok = track_application(
                job_id      = selected_job.get("id", ""),
                job_title   = selected_job.get("title", ""),
                company     = selected_job.get("company", ""),
                match_score = result["score"]
            )
            if ok:
                st.success("✅ Application tracked successfully!")
            else:
                st.error("Failed to track application.")


# ============================================================
# TAB 4: SAVED JOBS
# ============================================================

def render_saved_jobs_tab():
    """Builds the Saved Jobs tab showing bookmarked jobs."""

    st.markdown(
        '<div class="section-header">💾 Saved Jobs</div>',
        unsafe_allow_html=True
    )

    country = st.session_state.get("selected_country", "India")
    saved   = get_saved_jobs(
        country if country != "Both" else None
    )

    if not saved:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#9ca3af;">
            <div style="font-size:48px;">💾</div>
            <div style="font-size:18px; margin-top:12px;">
                No saved jobs yet
            </div>
            <div style="font-size:13px; margin-top:8px;">
                Go to Job Search tab and click Save on jobs you like
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Stats row
    st.markdown(
        f"<div style='color:#9ca3af; margin-bottom:16px;'>"
        f"💾 {len(saved)} saved job{'s' if len(saved) > 1 else ''}"
        f"</div>",
        unsafe_allow_html=True
    )

    # Skills distribution chart across saved jobs
    if len(saved) >= 3:
        st.plotly_chart(
            create_skills_distribution_chart(saved),
            use_container_width=True
        )

    st.markdown("---")

    # Display each saved job
    for job in saved:
        st.markdown(
            generate_job_card_html(job),
            unsafe_allow_html=True
        )

        sc1, sc2, sc3 = st.columns([2, 2, 6])

        with sc1:
            if st.button(
                "🗑️ Remove",
                key=f"del_{job.get('job_id', job.get('id'))}",
                use_container_width=True
            ):
                delete_saved_job(
                    job.get("job_id", job.get("id", ""))
                )
                st.success("Removed from saved jobs")
                st.rerun()

        with sc2:
            apply_link = job.get("apply_link", "#")
            st.markdown(
                f'<a href="{apply_link}" target="_blank">'
                f'<button style="background:linear-gradient('
                f'135deg,#059669,#34d399);color:white;border:none;'
                f'border-radius:8px;padding:8px 20px;font-weight:600;'
                f'cursor:pointer;width:100%;">🚀 Apply</button></a>',
                unsafe_allow_html=True
            )

        st.markdown("---")

    # Country distribution chart
    if len(saved) >= 2:
        st.plotly_chart(
            create_country_distribution_chart(saved),
            use_container_width=True
        )


# ============================================================
# TAB 5: CAREER CHAT
# ============================================================

def render_career_chat_tab():
    """Builds the AI Career Chat tab for Q&A with Gemini."""

    st.markdown(
        '<div class="section-header">💬 AI Career Chat</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div style="color:#9ca3af; margin-bottom:16px; font-size:14px;">
        Ask anything about jobs, salaries, skills, interview prep,
        or career advice. Powered by Gemini 2.5 Flash.
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(
                f'<div style="background:#2d2d5e; border-radius:12px; '
                f'padding:12px 16px; margin:8px 0; margin-left:40px;">'
                f'👤 {message["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="ai-box">🤖 {message["content"]}</div>',
                unsafe_allow_html=True
            )

    # Quick question buttons
    st.markdown("**💡 Quick Questions:**")
    qq_col1, qq_col2, qq_col3 = st.columns(3)

    quick_questions = [
        "What skills should I learn for a Python Developer job in India?",
        "What is a good salary for a fresher software engineer in Bangalore?",
        "How do I prepare for a technical interview at TCS or Infosys?"
    ]

    for i, (col, question) in enumerate(
        zip([qq_col1, qq_col2, qq_col3], quick_questions)
    ):
        with col:
            if st.button(
                question[:40] + "...",
                key=f"qq_{i}",
                use_container_width=True
            ):
                # Add to chat and get response
                st.session_state.chat_history.append({
                    "role":    "user",
                    "content": question
                })
                with st.spinner("🤖 Thinking..."):
                    context = ""
                    if st.session_state.resume_data:
                        skills = st.session_state.resume_data.get(
                            "skills", []
                        )
                        context = f"Skills: {', '.join(skills[:10])}"

                    response = career_chat(
                        question      = question,
                        context       = context,
                        chat_history  = st.session_state.chat_history
                    )
                st.session_state.chat_history.append({
                    "role":    "assistant",
                    "content": response
                })
                st.rerun()

    # Custom question input
    st.markdown("---")
    user_input = st.text_input(
        "Ask a career question...",
        placeholder = "e.g. How do I negotiate salary in India?",
        key         = "chat_input"
    )

    if st.button("Send 💬", use_container_width=False):
        if user_input.strip():
            st.session_state.chat_history.append({
                "role":    "user",
                "content": user_input
            })

            with st.spinner("🤖 Gemini is thinking..."):
                context = ""
                if st.session_state.resume_data:
                    skills  = st.session_state.resume_data.get("skills", [])
                    context = f"Skills: {', '.join(skills[:10])}"

                response = career_chat(
                    question     = user_input,
                    context      = context,
                    chat_history = st.session_state.chat_history
                )

            st.session_state.chat_history.append({
                "role":    "assistant",
                "content": response
            })
            st.rerun()

        else:
            st.warning("Please type a question first.")

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


# ============================================================
# MAIN APP — PUTS IT ALL TOGETHER
# ============================================================

def main():
    """
    Main function that renders the entire application.
    Builds the sidebar and all 5 tabs.
    """
    # Render sidebar
    render_sidebar()

    # Main header
    st.markdown("""
    <div style="text-align:center; padding:20px 0 10px 0;">
        <div style="margin-bottom:16px;">
            <svg width="72" height="72" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="mainLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:#a78bfa"/>
                        <stop offset="50%" style="stop-color:#60a5fa"/>
                        <stop offset="100%" style="stop-color:#34d399"/>
                    </linearGradient>
                </defs>
                <rect width="56" height="56" rx="14" fill="url(#mainLogoGrad)" opacity="0.15"/>
                <rect width="56" height="56" rx="14" fill="none" stroke="url(#mainLogoGrad)" stroke-width="1.5"/>
                <path d="M28 10 L33 22 L46 22 L36 31 L40 44 L28 35 L16 44 L20 31 L10 22 L23 22 Z" fill="url(#mainLogoGrad)"/>
                <circle cx="28" cy="28" r="5" fill="white" opacity="0.95"/>
            </svg>
        </div>
        <div style="font-size:42px; font-weight:900;
                    background:linear-gradient(90deg,#a78bfa,#60a5fa,#34d399);
                    -webkit-background-clip:text;
                    -webkit-text-fill-color:transparent;
                    letter-spacing:-1px; line-height:1.1;">
            Nexora AI
        </div>
        <div style="font-size:16px; color:#9ca3af; margin-top:8px;
                    letter-spacing:0.5px;">
            Find jobs • Analyze your resume • Match with AI • Plan your career
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Create the 5 main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Job Search",
        "📄 Resume Analyzer",
        "🎯 Job Matcher",
        "💾 Saved Jobs",
        "💬 Career Chat"
    ])

    with tab1:
        render_job_search_tab()

    with tab2:
        render_resume_tab()

    with tab3:
        render_matcher_tab()

    with tab4:
        render_saved_jobs_tab()

    with tab5:
        render_career_chat_tab()


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    main()