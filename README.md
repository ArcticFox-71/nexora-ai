# ⚡ Nexora AI — AI Job Search & Career Assistant

> Built for the **Capabl. Challenge 2025** | Track A | Powered by Gemini 2.5 Flash

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red?style=for-the-badge&logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange?style=for-the-badge&logo=google)
![SQLite](https://img.shields.io/badge/SQLite-Database-green?style=for-the-badge&logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

---

## 🚀 Live Demo

🔗 **[Nexora AI — Live App](https://nexora-ai.streamlit.app)**

---

## 📌 Project Overview

**Nexora AI** is a full-stack AI-powered career assistant that helps job seekers:

- 🔍 Search jobs across **India and Global** markets
- 📄 Upload and analyze their **PDF resume**
- 🤖 Get **ATS-style feedback** powered by Google Gemini 2.5 Flash
- 🎯 Calculate **resume-job match scores**
- 📚 Identify **skill gaps** and get learning roadmaps
- 💬 Chat with an **AI career advisor**
- 💾 Save jobs and **track applications**

---

## ✨ Features

### 🔍 Job Search System
- Search by role, skill, location
- India 🇮🇳 and Global 🌍 toggle
- Remote only filter
- Experience and job type filters
- Mock data + RapidAPI JSearch integration
- Auto fallback to demo data if API unavailable

### 📄 Resume Analyzer
- PDF upload and text extraction
- Skill detection from resume
- Education and experience parsing
- Contact info extraction
- Resume quality score out of 100
- ATS-style breakdown chart

### 🤖 Gemini AI Integration
- Full resume analysis and feedback
- ATS optimization tips
- Resume improvement suggestions
- Career roadmap generation
- Skill gap analysis with 30-day learning plan
- Interview question generation

### 🎯 Job Matcher
- Resume vs job match score 0-100%
- Matched and missing skills visualization
- Score breakdown chart
- AI-powered tailoring suggestions
- Application tracking

### 💬 Career Chat
- Ask any career question
- Context-aware answers using your resume
- Quick question shortcuts
- Powered by Gemini 2.5 Flash

### 💾 Database
- Save favourite jobs
- Track job applications with status
- Resume analysis history
- Search history logging

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.58 |
| AI | Google Gemini 2.5 Flash |
| Database | SQLite |
| PDF Parsing | pdfplumber + PyPDF2 |
| Charts | Plotly 6.x |
| Job API | RapidAPI JSearch (optional) |
| Language | Python 3.12 |

---

## 📁 Project Structure

```
ai-job-assistant/
│
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── README.md               # This file
│
├── modules/
│   ├── __init__.py
│   ├── job_search.py       # Job search engine
│   ├── resume_parser.py    # PDF reader and skill extractor
│   ├── ai_analyzer.py      # Gemini AI prompts and logic
│   ├── matcher.py          # Resume-job matching algorithm
│   ├── database.py         # SQLite operations
│   └── charts.py           # Plotly visualizations
│
├── utils/
│   ├── __init__.py
│   └── helpers.py          # Shared utility functions
│
├── assets/
│   └── style.css           # Custom dark theme CSS
│
└── data/
    └── mock_jobs.json      # Offline job data for demo
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.10 or higher
- Google Gemini API key (free at https://aistudio.google.com)
- Git

### Step 1 — Clone the Repository

```bash
git clone https://github.com/ArcticFox-71/nexora-ai.git
cd nexora-ai
```

### Step 2 — Create Virtual Environment

```bash
python -m venv venv
```

**Windows:**
```bash
.\venv\Scripts\Activate.ps1
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GEMINI_API_KEY=your_gemini_api_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
USE_REAL_JOBS_API=false
```

### Step 5 — Run the App

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 🔑 API Keys Setup

### Google Gemini API (Required)
1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key into your `.env` file as `GEMINI_API_KEY`
4. Free tier — 1500 requests/day, 15 requests/minute

### RapidAPI JSearch (Optional — for real jobs)
1. Go to https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Subscribe to the free tier (200 requests/month)
3. Copy your key into `.env` as `RAPIDAPI_KEY`
4. Set `USE_REAL_JOBS_API=true` in `.env`
5. If not set, app uses built-in demo job data

---

## 🌐 Deployment on Streamlit Cloud

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Click **New App**
4. Select your repository and set **Main file** to `app.py`
5. Go to **Advanced Settings → Secrets** and add:

```toml
GEMINI_API_KEY = "your_key_here"
RAPIDAPI_KEY = "your_key_here"
USE_REAL_JOBS_API = "false"
```

6. Click **Deploy**

---

## 📊 How Job Matching Works

The match score is calculated from three factors:

| Factor | Weight | Description |
|---|---|---|
| Skill Match | 60 points | How many job skills appear in resume |
| Title Relevance | 20 points | Job title keywords in resume |
| Experience Match | 20 points | Job description keywords in resume |

**Score Interpretation:**
- 🟢 70-100% — Strong Match — Apply with confidence
- 🟡 40-69% — Moderate Match — Learn missing skills
- 🔴 0-39% — Weak Match — Build more relevant skills

---

## 🤖 AI Features Powered by Gemini

| Feature | Description |
|---|---|
| Resume Analysis | Full ATS-style feedback with strengths and weaknesses |
| Job Match Analysis | Targeted advice to tailor resume for specific job |
| Skill Gap Analysis | 30-day learning plan for missing skills |
| Career Roadmap | Phase-by-phase plan to reach target role |
| Resume Improvements | Rewritten bullet points and keyword suggestions |
| Interview Prep | Role-specific technical and behavioral questions |
| Career Chat | Open Q&A about jobs, salary, career advice |

---

## 🇮🇳 Indian Job Market Features

- Salary displayed in LPA format
- India-specific job locations (Bangalore, Mumbai, Hyderabad, Pune, Chennai)
- Indian company listings (Infosys, TCS, Wipro, Razorpay, Swiggy, Zomato)
- Notice period information (30/60/90 days)
- Indian tech job market insights from Gemini

---

## 🐛 Known Issues

- Resume detection in sidebar requires page interaction after upload
- ATS score may be lower for image-based PDFs (use text-based PDFs)
- Gemini rate limit of 15 requests/minute on free tier

---

## 🔮 Future Improvements

- LinkedIn profile import
- Email alerts for new matching jobs
- Resume version management
- Mock interview with voice
- Salary negotiation coach
- Company culture insights

---

## 👨‍💻 Developer

**Arjun**
- GitHub: [@ArcticFox-71](https://github.com/ArcticFox-71)
- Project: Capabl. Challenge 2025 — Track A

---

## 📄 License

MIT License — feel free to use and modify with attribution.