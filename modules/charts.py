"""
modules/charts.py
=================
Fixed for Plotly 6.x — titlefont replaced with title_font
"""

import plotly.graph_objects as go
from typing import Dict, List


COLORS = {
    "primary":    "#7c3aed",
    "secondary":  "#4f46e5",
    "success":    "#34d399",
    "warning":    "#fbbf24",
    "danger":     "#f87171",
    "text":       "#e2e8f0",
    "background": "#1e1e3f",
    "card":       "#2d2d5e",
    "border":     "#4a4a8a"
}

DARK_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font":          {"color": COLORS["text"], "family": "Inter, sans-serif"},
    "margin":        {"t": 40, "b": 20, "l": 20, "r": 20}
}


def create_match_gauge(score: int, title: str = "Match Score") -> go.Figure:
    if score >= 70:
        bar_color = COLORS["success"]
        label     = "Strong Match"
    elif score >= 40:
        bar_color = COLORS["warning"]
        label     = "Moderate Match"
    else:
        bar_color = COLORS["danger"]
        label     = "Weak Match"

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        title = {
            "text": f"{title}<br><span style='font-size:14px;color:{bar_color}'>{label}</span>",
            "font": {"size": 18, "color": COLORS["text"]}
        },
        number = {
            "suffix": "%",
            "font":   {"size": 36, "color": bar_color}
        },
        gauge = {
            "axis": {
                "range":    [0, 100],
                "tickwidth": 1,
                "tickcolor": COLORS["border"],
                "tickfont":  {"color": COLORS["text"]}
            },
            "bar":       {"color": bar_color, "thickness": 0.3},
            "bgcolor":   COLORS["background"],
            "bordercolor": COLORS["border"],
            "steps": [
                {"range": [0, 40],   "color": "rgba(248,113,113,0.15)"},
                {"range": [40, 70],  "color": "rgba(251,191,36,0.15)"},
                {"range": [70, 100], "color": "rgba(52,211,153,0.15)"}
            ],
            "threshold": {
                "line":      {"color": COLORS["text"], "width": 2},
                "thickness": 0.75,
                "value":     score
            }
        }
    ))

    fig.update_layout(height=280, **DARK_LAYOUT)
    return fig


def create_skill_gap_chart(
    matched_skills: List[str],
    missing_skills: List[str]
) -> go.Figure:
    matched = matched_skills[:10]
    missing = missing_skills[:10]

    all_skills = matched + missing
    all_values = [1] * len(all_skills)
    all_colors = (
        [COLORS["success"]] * len(matched) +
        [COLORS["danger"]]  * len(missing)
    )
    all_labels = (
        ["✅ Have"] * len(matched) +
        ["❌ Missing"] * len(missing)
    )

    if not all_skills:
        fig = go.Figure()
        fig.add_annotation(
            text="No skill data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"color": COLORS["text"], "size": 14}
        )
        fig.update_layout(height=300, **DARK_LAYOUT)
        return fig

    fig = go.Figure(go.Bar(
        x            = all_values,
        y            = all_skills,
        orientation  = "h",
        marker_color = all_colors,
        text         = all_labels,
        textposition = "inside",
        textfont     = {"color": "white", "size": 11},
        hovertemplate = "%{y}<extra></extra>"
    ))

    fig.update_layout(
        title   = {"text": "Skills Analysis", "font": {"size": 16, "color": COLORS["text"]}},
        xaxis   = {"visible": False},
        yaxis   = {"tickfont": {"color": COLORS["text"], "size": 11}},
        height  = max(250, len(all_skills) * 30 + 60),
        bargap  = 0.3,
        **DARK_LAYOUT
    )
    return fig


def create_resume_score_chart(breakdown: Dict) -> go.Figure:
    if not breakdown:
        fig = go.Figure()
        fig.add_annotation(
            text="No resume data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"color": COLORS["text"], "size": 14}
        )
        fig.update_layout(height=200, **DARK_LAYOUT)
        return fig

    categories  = list(breakdown.keys())
    scores      = [breakdown[c]["score"] for c in categories]
    maximums    = [breakdown[c]["max"]   for c in categories]
    notes       = [breakdown[c].get("note", "") for c in categories]

    percentages = [
        round((s / m) * 100) if m > 0 else 0
        for s, m in zip(scores, maximums)
    ]

    bar_colors = [
        COLORS["success"] if p >= 70
        else COLORS["warning"] if p >= 40
        else COLORS["danger"]
        for p in percentages
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name         = "Your Score",
        x            = scores,
        y            = categories,
        orientation  = "h",
        marker_color = bar_colors,
        text         = [f"{s}/{m}" for s, m in zip(scores, maximums)],
        textposition = "inside",
        textfont     = {"color": "white", "size": 12},
        hovertext    = notes,
        hovertemplate = "%{y}: %{x} points<br>%{hovertext}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name         = "Maximum",
        x            = maximums,
        y            = categories,
        orientation  = "h",
        marker_color = "rgba(74,74,138,0.3)",
        hoverinfo    = "skip"
    ))

    fig.update_layout(
        title      = {"text": "Resume Quality Breakdown", "font": {"size": 16, "color": COLORS["text"]}},
        barmode    = "overlay",
        xaxis      = {"title": {"text": "Points", "font": {"color": COLORS["text"]}}, "tickfont": {"color": COLORS["text"]}},
        yaxis      = {"tickfont": {"color": COLORS["text"], "size": 12}},
        height     = 280,
        showlegend = False,
        **DARK_LAYOUT
    )
    return fig


def create_skills_distribution_chart(jobs: List[Dict]) -> go.Figure:
    skill_counts = {}

    for job in jobs:
        for skill in job.get("skills_required", []):
            skill_lower = skill.lower()
            skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1

    if not skill_counts:
        fig = go.Figure()
        fig.add_annotation(
            text="No skills data available yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"color": COLORS["text"], "size": 14}
        )
        fig.update_layout(height=300, **DARK_LAYOUT)
        return fig

    sorted_skills = sorted(
        skill_counts.items(), key=lambda x: x[1], reverse=True
    )[:15]

    skills = [s[0].title() for s in sorted_skills]
    counts = [s[1]         for s in sorted_skills]

    colors = [
        f"rgba(124,58,237,{max(0.4, 1 - i * 0.05)})"
        for i in range(len(skills))
    ]

    fig = go.Figure(go.Bar(
        x            = counts,
        y            = skills,
        orientation  = "h",
        marker_color = colors,
        text         = counts,
        textposition = "outside",
        textfont     = {"color": COLORS["text"], "size": 11},
        hovertemplate = "%{y}: %{x} jobs<extra></extra>"
    ))

    fig.update_layout(
        title  = {"text": "Most In-Demand Skills", "font": {"size": 16, "color": COLORS["text"]}},
        xaxis  = {
            "title":    {"text": "Number of Jobs", "font": {"color": COLORS["text"]}},
            "tickfont": {"color": COLORS["text"]}
        },
        yaxis  = {
            "tickfont":  {"color": COLORS["text"], "size": 11},
            "autorange": "reversed"
        },
        height = 450,
        **DARK_LAYOUT
    )
    return fig


def create_score_breakdown_chart(match_data: Dict) -> go.Figure:
    categories = ["Skill Match", "Title Relevance", "Experience Match"]
    scores     = [
        match_data.get("skill_score",      0),
        match_data.get("title_score",      0),
        match_data.get("experience_score", 0)
    ]
    maximums = [60, 20, 20]

    bar_colors = [
        COLORS["success"] if s >= m * 0.7
        else COLORS["warning"] if s >= m * 0.4
        else COLORS["danger"]
        for s, m in zip(scores, maximums)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name         = "Your Score",
        x            = categories,
        y            = scores,
        marker_color = bar_colors,
        text         = [f"{s}/{m}" for s, m in zip(scores, maximums)],
        textposition = "outside",
        textfont     = {"color": COLORS["text"]},
        hovertemplate = "%{x}: %{y} points<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name         = "Maximum",
        x            = categories,
        y            = maximums,
        marker_color = "rgba(74,74,138,0.3)",
        hoverinfo    = "skip"
    ))

    fig.update_layout(
        title    = {"text": "Match Score Breakdown", "font": {"size": 16, "color": COLORS["text"]}},
        barmode  = "overlay",
        xaxis    = {"tickfont": {"color": COLORS["text"]}},
        yaxis    = {
            "title":    {"text": "Points", "font": {"color": COLORS["text"]}},
            "tickfont": {"color": COLORS["text"]}
        },
        height   = 280,
        showlegend = False,
        **DARK_LAYOUT
    )
    return fig


def create_country_distribution_chart(jobs: List[Dict]) -> go.Figure:
    india_count  = sum(1 for j in jobs if j.get("country") == "India")
    global_count = sum(1 for j in jobs if j.get("country") != "India")

    if india_count == 0 and global_count == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No job data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={"color": COLORS["text"], "size": 14}
        )
        fig.update_layout(height=250, **DARK_LAYOUT)
        return fig

    fig = go.Figure(go.Pie(
        labels    = ["🇮🇳 India", "🌍 Global"],
        values    = [india_count, global_count],
        hole      = 0.5,
        marker    = {
            "colors": [COLORS["primary"], COLORS["secondary"]],
            "line":   {"color": COLORS["background"], "width": 2}
        },
        textfont  = {"color": "white", "size": 13},
        hovertemplate = "%{label}: %{value} jobs (%{percent})<extra></extra>"
    ))

    fig.update_layout(
        title  = {"text": "Job Distribution", "font": {"size": 16, "color": COLORS["text"]}},
        legend = {"font": {"color": COLORS["text"]}, "orientation": "h", "y": -0.1},
        height = 280,
        **DARK_LAYOUT
    )
    return fig