"""
Streamlit Web Application: AI Resume Screening System
Enterprise Applicant Tracking System (ATS) Workspace.

Three primary functional routes:
1. Candidates (Database view, search, filters, compact table, batch actions)
2. Screening Overview (Analytics, metrics, competency coverage, score breakdown)
3. Candidate Review (Split-panel view: candidate list on left, deep-dive profile on right)
"""

import base64
import html
import io
import os
import streamlit as st
from typing import List, Dict, Any, Optional

from config import (
    DEFAULT_WEIGHT_TEXT_SIMILARITY,
    DEFAULT_WEIGHT_SKILL_MATCH,
    MIN_JOB_DESCRIPTION_CHARS,
    MAX_FILE_SIZE_MB,
    MAX_TEXT_PREVIEW_CHARS
)
from resume_parser import parse_resume
from requirement_extractor import extract_job_requirements, extract_job_title
from matcher import rank_resumes
from exporter import generate_candidates_csv


# Standard enterprise job description template
SAMPLE_JOB_DESCRIPTION = """Role: Java Full Stack Developer

Responsibilities:
- Design, build, and maintain high-performance microservices and secure REST APIs.
- Develop interactive web applications with modern frontend components and robust Java backend services.
- Collaborate with cross-functional Agile engineering teams using Git for version control.
- Design database schemas, write optimized queries, and manage persistence layers using MySQL and PostgreSQL.
- Implement CI/CD automation pipelines and deploy containerized services using Docker.

Required Qualifications & Skills:
- 3+ years of relevant software engineering experience in full stack application development.
- Strong proficiency in Java, Spring Boot, Microservices, and REST APIs.
- Solid hands-on experience with relational databases including MySQL and PostgreSQL.
- Proficient in version control using Git and collaborative Agile workflows.
- Experience with Docker containerization and build tools.
- Bachelor's degree in Computer Science, Information Technology, or a related technical field.

Preferred Qualifications:
- Experience with Kubernetes and AWS cloud deployments.
- Knowledge of Kafka event streaming and Redis caching.
- Familiarity with CI/CD automation tools like Jenkins or GitHub Actions.
"""


def setup_theme_and_styles():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")
    page_icon_asset = logo_path if os.path.exists(logo_path) else "💼"

    st.set_page_config(
        page_title="AI Resume Screening System",
        page_icon=page_icon_asset,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Cohesive Enterprise ATS Design System
    # Modern SaaS visual hierarchy inspired by Mobbin recruiting patterns and Aceternity UI surfaces
    st.markdown("""
        <style>
        /* Modern Design System Tokens */
        :root {
            --ats-primary: #1E3A8A;
            --ats-primary-hover: #172554;
            --ats-primary-light: #EFF6FF;
            --ats-primary-border: #BFDBFE;
            --ats-navy-dark: #0F172A;
            --ats-bg: #F8FAFC;
            --ats-surface: #FFFFFF;
            --ats-border: #E2E8F0;
            --ats-border-subtle: #F1F5F9;
            --ats-text-main: #0F172A;
            --ats-text-muted: #64748B;
            --ats-text-subtle: #94A3B8;
            --ats-success: #15803D;
            --ats-success-bg: #F0FDF4;
            --ats-success-border: #BBF7D0;
            --ats-warning: #B45309;
            --ats-warning-bg: #FFFBEB;
            --ats-warning-border: #FDE68A;
            --ats-error: #B91C1C;
            --ats-error-bg: #FEF2F2;
            --ats-error-border: #FECACA;
            --ats-radius-sm: 6px;
            --ats-radius-md: 10px;
            --ats-radius-lg: 14px;
            --ats-shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
            --ats-shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
            --ats-shadow-hover: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
            --ats-transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        /* Root Canvas & Containers */
        html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], .main, .stMain, section.main, .block-container {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif !important;
            color: var(--ats-text-main) !important;
            background-color: var(--ats-bg) !important;
            -webkit-font-smoothing: antialiased;
        }

        /* Responsive Container padding */
        .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1440px !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
            }
        }

        /* Native Header & Navigation Architecture */
        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            background: transparent !important;
            color: var(--ats-text-main) !important;
            border: none !important;
            box-shadow: none !important;
            pointer-events: none !important;
            z-index: 999990 !important;
            height: 3.5rem !important;
        }
        header[data-testid="stHeader"] * {
            pointer-events: auto;
        }

        /* Suppress unwanted Streamlit default chrome */
        #MainMenu, footer, .stAppDeployButton, [data-testid="stDecoration"], [data-testid="stToolbarActions"], [data-testid="stStatusWidget"] {
            visibility: hidden;
            display: none !important;
        }

        /* Native Sidebar Collapse Control (when sidebar is open) */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button {
            visibility: visible !important;
            opacity: 1 !important;
            display: flex !important;
            color: var(--ats-primary) !important;
            cursor: pointer !important;
        }
        [data-testid="stSidebarCollapseButton"] button:hover {
            background-color: var(--ats-primary-light) !important;
            border-radius: var(--ats-radius-sm) !important;
        }

        /* Native Sidebar Expand Control (when sidebar is collapsed) */
        button[data-testid="stExpandSidebarButton"],
        [data-testid="stExpandSidebarButton"] {
            visibility: visible !important;
            opacity: 1 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: var(--ats-primary) !important;
            background-color: var(--ats-surface) !important;
            border: 1px solid var(--ats-border) !important;
            border-radius: var(--ats-radius-sm) !important;
            padding: 6px 8px !important;
            margin: 0.5rem 0 0 0.5rem !important;
            box-shadow: var(--ats-shadow-md) !important;
            cursor: pointer !important;
            pointer-events: auto !important;
            z-index: 999999 !important;
            transition: var(--ats-transition) !important;
        }
        button[data-testid="stExpandSidebarButton"]:hover,
        [data-testid="stExpandSidebarButton"]:hover {
            background-color: var(--ats-primary-light) !important;
            border-color: var(--ats-primary-border) !important;
            color: var(--ats-primary) !important;
            transform: scale(1.02);
        }

        /* Sidebar Styling (Aceternity UI clean collapsible style) */
        section[data-testid="stSidebar"], [data-testid="stSidebarContent"], [data-testid="stSidebarNav"] {
            background-color: var(--ats-surface) !important;
            border-right: 1px solid var(--ats-border) !important;
            color: var(--ats-text-main) !important;
            box-shadow: 1px 0 3px rgba(15, 23, 42, 0.02) !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: var(--ats-border) !important;
        }

        .sidebar-brand {
            padding: 0.5rem 0.25rem 1.15rem 0.25rem;
            border-bottom: 1px solid var(--ats-border-subtle);
            margin-bottom: 1.25rem;
        }
        .sidebar-brand-header {
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }
        .sidebar-brand-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            object-fit: contain;
            box-shadow: var(--ats-shadow-sm);
            flex-shrink: 0;
        }
        .sidebar-brand-title {
            font-size: 0.9375rem;
            font-weight: 700;
            color: var(--ats-navy-dark);
            letter-spacing: -0.02em;
            line-height: 1.25;
            margin: 0;
        }
        .sidebar-brand-badge {
            display: inline-flex;
            align-items: center;
            font-size: 0.6875rem;
            font-weight: 600;
            color: var(--ats-primary);
            background: var(--ats-primary-light);
            border: 1px solid var(--ats-primary-border);
            border-radius: 9999px;
            padding: 0.15rem 0.5rem;
            margin-top: 0.5rem;
            letter-spacing: 0.02em;
        }

        /* Top Application Shell Header (Mobbin SaaS Command Header) */
        .ats-top-header {
            background: var(--ats-surface);
            border: 1px solid var(--ats-border);
            border-radius: var(--ats-radius-md);
            padding: 1.1rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            box-shadow: var(--ats-shadow-sm);
            transition: var(--ats-transition);
        }
        .ats-top-header:hover {
            box-shadow: var(--ats-shadow-md);
            border-color: #CBD5E1;
        }
        .ats-header-left {
            display: flex;
            flex-direction: column;
        }
        .ats-header-title {
            font-size: 1.375rem;
            font-weight: 700;
            color: var(--ats-navy-dark);
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.3;
        }
        .ats-header-sub {
            font-size: 0.8125rem;
            color: var(--ats-text-muted);
            margin-top: 0.2rem;
            font-weight: 400;
        }
        .ats-header-right {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.625rem;
        }
        .ats-pill-badge {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--ats-primary);
            background: var(--ats-primary-light);
            border: 1px solid var(--ats-primary-border);
            border-radius: var(--ats-radius-sm);
            padding: 0.35rem 0.75rem;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            box-shadow: var(--ats-shadow-sm);
        }

        /* Headings & Markdown Text */
        h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
            color: var(--ats-navy-dark) !important;
            font-weight: 600 !important;
            letter-spacing: -0.015em !important;
        }
        p, span, label, div, [data-testid="stMarkdownContainer"] p {
            color: var(--ats-text-main);
        }

        /* Form Inputs & Text Areas */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"], .stTextInput input, .stTextArea textarea {
            background-color: var(--ats-surface) !important;
            color: var(--ats-text-main) !important;
            border: 1px solid var(--ats-border) !important;
            border-radius: var(--ats-radius-sm) !important;
            box-shadow: var(--ats-shadow-sm) !important;
            font-size: 0.875rem !important;
            transition: var(--ats-transition) !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--ats-primary) !important;
            box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.12) !important;
            outline: none !important;
        }

        /* Selectboxes */
        div[data-baseweb="select"] > div {
            background-color: var(--ats-surface) !important;
            color: var(--ats-text-main) !important;
            border: 1px solid var(--ats-border) !important;
            border-radius: var(--ats-radius-sm) !important;
            box-shadow: var(--ats-shadow-sm) !important;
            font-size: 0.8125rem !important;
            transition: var(--ats-transition) !important;
        }
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--ats-primary) !important;
            box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.12) !important;
        }

        /* Buttons with tactile hover and focus */
        .stButton > button {
            border-radius: var(--ats-radius-sm) !important;
            font-weight: 600 !important;
            font-size: 0.8125rem !important;
            letter-spacing: 0.01em !important;
            transition: var(--ats-transition) !important;
            box-shadow: var(--ats-shadow-sm) !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton > button:focus-visible {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.25) !important;
        }
        .stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
            background-color: var(--ats-primary) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--ats-primary) !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--ats-primary-hover) !important;
            border-color: var(--ats-primary-hover) !important;
            color: #FFFFFF !important;
            box-shadow: var(--ats-shadow-md) !important;
            transform: translateY(-1px);
        }
        .stButton > button[kind="secondary"], .stButton > button[data-testid="baseButton-secondary"] {
            background-color: var(--ats-surface) !important;
            color: #334155 !important;
            border: 1px solid var(--ats-border) !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background-color: #F8FAFC !important;
            border-color: #94A3B8 !important;
            color: var(--ats-navy-dark) !important;
            box-shadow: var(--ats-shadow-sm) !important;
        }
        .stButton > button:disabled {
            opacity: 0.6 !important;
            cursor: not-allowed !important;
            transform: none !important;
        }

        /* Modern Aceternity UI Inspired File Uploader */
        [data-testid="stFileUploader"] {
            background-color: var(--ats-surface) !important;
            border: 1.5px dashed #CBD5E1 !important;
            border-radius: var(--ats-radius-md) !important;
            padding: 0.75rem !important;
            transition: var(--ats-transition) !important;
            box-shadow: var(--ats-shadow-sm) !important;
        }
        [data-testid="stFileUploader"]:hover {
            border-color: var(--ats-primary) !important;
            background-color: #FAFBFD !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background-color: #F8FAFC !important;
            border-radius: var(--ats-radius-sm) !important;
            border: none !important;
            padding: 1.25rem !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] {
            color: var(--ats-text-muted) !important;
            font-size: 0.8125rem !important;
        }

        /* Streamlit Native Container Cards */
        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--ats-border) !important;
            border-radius: var(--ats-radius-md) !important;
            background: var(--ats-surface) !important;
            box-shadow: var(--ats-shadow-sm) !important;
            transition: var(--ats-transition) !important;
        }
        [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: var(--ats-shadow-md) !important;
            border-color: #CBD5E1 !important;
        }

        /* Tabs (Clean Enterprise Underline style) */
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--ats-border) !important;
            background-color: transparent !important;
            gap: 1.5rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: var(--ats-text-muted) !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.6rem 0.35rem !important;
            border: none !important;
            background: transparent !important;
            transition: var(--ats-transition) !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--ats-navy-dark) !important;
        }
        .stTabs [aria-selected="true"] {
            color: var(--ats-primary) !important;
            font-weight: 600 !important;
            border-bottom: 2.5px solid var(--ats-primary) !important;
        }

        /* Sidebar Radio Navigation (Mobbin Nav Rail Style) */
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 0.55rem 0.75rem !important;
            border-radius: var(--ats-radius-sm) !important;
            color: #475467 !important;
            font-weight: 500 !important;
            font-size: 0.84375rem !important;
            margin-bottom: 0.25rem !important;
            transition: var(--ats-transition) !important;
            border: 1px solid transparent !important;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background-color: var(--ats-primary-light) !important;
            color: var(--ats-primary) !important;
            border-color: var(--ats-primary-border) !important;
        }

        /* Surface Cards */
        .ats-card {
            background: var(--ats-surface);
            border: 1px solid var(--ats-border);
            border-radius: var(--ats-radius-md);
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: var(--ats-shadow-sm);
            transition: var(--ats-transition);
        }
        .ats-card:hover {
            box-shadow: var(--ats-shadow-md);
            border-color: #CBD5E1;
        }
        .ats-card-header {
            font-size: 0.9375rem;
            font-weight: 600;
            color: var(--ats-navy-dark);
            margin-bottom: 0.85rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--ats-border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Metric Grid (KPI Header Cards) */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .metric-item {
            background: var(--ats-surface);
            border: 1px solid var(--ats-border);
            border-radius: var(--ats-radius-md);
            padding: 1.1rem 1.25rem;
            box-shadow: var(--ats-shadow-sm);
            transition: var(--ats-transition);
            position: relative;
            overflow: hidden;
        }
        .metric-item:hover {
            box-shadow: var(--ats-shadow-md);
            border-color: #CBD5E1;
            transform: translateY(-2px);
        }
        .metric-item::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--ats-primary);
            border-radius: 4px 0 0 4px;
        }
        .metric-item-label {
            font-size: 0.6875rem;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--ats-text-muted);
            letter-spacing: 0.06em;
            margin-bottom: 0.35rem;
        }
        .metric-item-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--ats-navy-dark);
            line-height: 1.2;
            letter-spacing: -0.02em;
        }
        .metric-item-sub {
            font-size: 0.75rem;
            color: var(--ats-text-muted);
            margin-top: 0.35rem;
        }

        /* Gauge Cards */
        .gauge-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .gauge-card {
            background: var(--ats-surface);
            border: 1px solid var(--ats-border);
            border-radius: var(--ats-radius-md);
            padding: 1.25rem 1rem;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: var(--ats-shadow-sm);
            transition: var(--ats-transition);
        }
        .gauge-card:hover {
            box-shadow: var(--ats-shadow-md);
            border-color: #CBD5E1;
            transform: translateY(-2px);
        }
        .gauge-label {
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--ats-navy-dark);
            margin-top: 0.5rem;
        }
        .gauge-sub {
            font-size: 0.6875rem;
            color: var(--ats-text-muted);
            margin-top: 0.2rem;
        }

        /* Polished Data Tables (Enterprise dense data table) */
        .data-table-container {
            width: 100%;
            overflow-x: auto;
            border: 1px solid var(--ats-border);
            border-radius: var(--ats-radius-md);
            background: var(--ats-surface);
            margin-top: 0.75rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--ats-shadow-sm);
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8125rem;
            color: var(--ats-text-main);
            text-align: left;
        }
        .data-table th {
            background-color: #F8FAFC;
            color: #475467;
            font-weight: 600;
            font-size: 0.75rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--ats-border);
            white-space: nowrap;
        }
        .data-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--ats-border-subtle);
            vertical-align: middle;
            transition: background 0.15s ease;
        }
        .data-table tbody tr:hover td {
            background-color: #F8FAFC;
        }
        .data-table tbody tr:last-child td {
            border-bottom: none;
        }

        /* Candidate Avatar Circle */
        .candidate-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background-color: var(--ats-primary-light);
            border: 1px solid var(--ats-primary-border);
            color: var(--ats-primary);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.6875rem;
            margin-right: 0.65rem;
            vertical-align: middle;
        }

        /* Status tags */
        .badge-ready {
            color: var(--ats-success);
            background: var(--ats-success-bg);
            border: 1px solid var(--ats-success-border);
            padding: 0.2rem 0.55rem;
            border-radius: var(--ats-radius-sm);
            font-size: 0.6875rem;
            font-weight: 600;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }
        .badge-warning {
            color: var(--ats-warning);
            background: var(--ats-warning-bg);
            border: 1px solid var(--ats-warning-border);
            padding: 0.2rem 0.55rem;
            border-radius: var(--ats-radius-sm);
            font-size: 0.6875rem;
            font-weight: 600;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }
        .badge-error {
            color: var(--ats-error);
            background: var(--ats-error-bg);
            border: 1px solid var(--ats-error-border);
            padding: 0.2rem 0.55rem;
            border-radius: var(--ats-radius-sm);
            font-size: 0.6875rem;
            font-weight: 600;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }

        /* Tag pill */
        .tag-pill {
            display: inline-flex;
            align-items: center;
            background-color: #F1F5F9;
            color: #334155;
            border: 1px solid #CBD5E1;
            border-radius: var(--ats-radius-sm);
            padding: 0.25rem 0.55rem;
            font-size: 0.75rem;
            font-weight: 500;
            line-height: 1.2;
            margin: 0.15rem;
            white-space: nowrap;
            transition: var(--ats-transition);
        }
        .tag-pill:hover {
            border-color: #94A3B8;
            background-color: #E2E8F0;
        }
        .tag-pill-match {
            background-color: var(--ats-success-bg);
            color: var(--ats-success);
            border-color: var(--ats-success-border);
            font-weight: 600;
        }
        .tag-pill-missing {
            background-color: #F8FAFC;
            color: var(--ats-text-muted);
            border-color: var(--ats-border);
        }

        /* Score visual indicator */
        .score-bar-bg {
            background-color: #E2E8F0;
            border-radius: 9999px;
            height: 6px;
            width: 70px;
            display: inline-block;
            vertical-align: middle;
            margin-left: 0.5rem;
            overflow: hidden;
        }
        .score-bar-fill {
            background-color: var(--ats-primary);
            height: 100%;
            border-radius: 9999px;
        }

        /* Coverage Bar in Analytics */
        .coverage-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.65rem;
            font-size: 0.8125rem;
        }
        .coverage-label {
            width: 140px;
            font-weight: 600;
            color: var(--ats-navy-dark);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .coverage-bar-track {
            flex: 1;
            background: #E2E8F0;
            height: 8px;
            border-radius: 9999px;
            overflow: hidden;
        }
        .coverage-bar-fill {
            background: var(--ats-primary);
            height: 100%;
            border-radius: 9999px;
        }
        .coverage-count {
            width: 75px;
            text-align: right;
            font-size: 0.75rem;
            color: var(--ats-text-muted);
            font-weight: 600;
        }

        /* Candidate review cards */
        .review-candidate-item {
            padding: 0.75rem 0.85rem;
            border-bottom: 1px solid var(--ats-border-subtle);
            cursor: pointer;
            border-left: 3px solid transparent;
            background: var(--ats-surface);
            transition: var(--ats-transition);
        }
        .review-candidate-item.active {
            background: var(--ats-primary-light);
            border-left-color: var(--ats-primary);
        }
        .review-candidate-item:hover {
            background: #F8FAFC;
        }

        .evidence-quote {
            background: #F8FAFC;
            border-left: 3px solid var(--ats-primary);
            padding: 0.5rem 0.75rem;
            font-size: 0.78125rem;
            color: #334155;
            margin-bottom: 0.5rem;
            border-radius: 0 var(--ats-radius-sm) var(--ats-radius-sm) 0;
            line-height: 1.5;
            border-top: 1px solid var(--ats-border-subtle);
            border-right: 1px solid var(--ats-border-subtle);
            border-bottom: 1px solid var(--ats-border-subtle);
        }

        .callout-warning {
            background: var(--ats-warning-bg);
            border: 1px solid var(--ats-warning-border);
            color: var(--ats-warning);
            padding: 0.65rem 0.85rem;
            border-radius: var(--ats-radius-sm);
            font-size: 0.78125rem;
            margin-bottom: 0.85rem;
        }

        /* Accessibility: Respect Reduced Motion Preferences */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)


def format_field(value: Optional[Any], default: str = "Not available") -> str:
    """Format string or collection value safely, returning default if absent."""
    if value is None:
        return default
    if isinstance(value, (list, tuple, set)):
        items = [str(x).strip() for x in value if str(x).strip()]
        return ", ".join(items) if items else default
    val_str = str(value).strip()
    return val_str if val_str else default


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable string (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def build_candidate_table_html(candidates: List[Dict[str, Any]]) -> str:
    """Construct a clean, pandas-independent HTML table with full XSS escaping for backwards-compatibility."""
    rows_html = []
    for c in candidates:
        rank_escaped = html.escape(f"#{c.get('rank', '-')}")
        name_val = format_field(c.get("name"), default="Not detected")
        name_escaped = html.escape(name_val)
        filename_escaped = html.escape(c.get("filename", "unknown"))

        score_overall = f"{c.get('overall_score', 0.0):.1f}%"
        score_text = f"{c.get('text_similarity_score', 0.0):.1f}%"
        score_skill = f"{c.get('skill_match_score', 0.0):.1f}%"
        skills_count = str(len(c.get("matched_skills", [])))

        if not c.get("success"):
            status_html = '<span class="badge-error">Extraction failed</span>'
        elif c.get("warning"):
            status_html = '<span class="badge-warning">Limited text</span>'
        else:
            status_html = '<span class="badge-ready">Parsed</span>'

        row = (
            f"<tr>"
            f"<td style='font-weight: 600; color: #4B5563;'>{rank_escaped}</td>"
            f"<td style='font-weight: 500; color: #111827;'>{name_escaped}</td>"
            f"<td style='color: #6B7280; font-family: monospace; font-size: 0.75rem;'>{filename_escaped}</td>"
            f"<td style='font-weight: 600; color: #111827;'>{score_overall}</td>"
            f"<td style='color: #4B5563;'>{score_text}</td>"
            f"<td style='color: #4B5563;'>{score_skill}</td>"
            f"<td style='color: #4B5563;'>{skills_count}</td>"
            f"<td>{status_html}</td>"
            f"</tr>"
        )
        rows_html.append(row)

    table_html = (
        '<div class="data-table-container">'
        '<table class="data-table leaderboard-table">'
        '<thead>'
        '<tr>'
        '<th>Rank</th>'
        '<th>Candidate Name</th>'
        '<th>Original Filename</th>'
        '<th>Overall Score</th>'
        '<th>Text Similarity</th>'
        '<th>Skill Match</th>'
        '<th>Matched Skills</th>'
        '<th>Review Status</th>'
        '</tr>'
        '</thead>'
        '<tbody>'
        + "".join(rows_html)
        + '</tbody>'
        '</table>'
        '</div>'
    )
    return table_html


def render_sidebar_nav() -> str:
    """Render the persistent ATS navigation sidebar and scoring configuration."""
    logo_svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.svg")
    logo_img_tag = ""
    if os.path.exists(logo_svg_path):
        try:
            with open(logo_svg_path, "rb") as f:
                b64_logo = base64.b64encode(f.read()).decode("utf-8")
                logo_img_tag = f'<img src="data:image/svg+xml;base64,{b64_logo}" class="sidebar-brand-icon" alt="Logo" />'
        except Exception:
            logo_img_tag = ""

    with st.sidebar:
        st.markdown(f"""
            <div class="sidebar-brand">
                <div class="sidebar-brand-header">
                    {logo_img_tag}
                    <div>
                        <div class="sidebar-brand-title">AI Resume Screening System</div>
                    </div>
                </div>
                <div class="sidebar-brand-badge">Enterprise Workspace</div>
            </div>
        """, unsafe_allow_html=True)

        options = ["Candidates", "Screening Overview", "Candidate Review"]
        if "nav_page" not in st.session_state:
            query_page = st.query_params.get("page")
            st.session_state["nav_page"] = query_page if query_page in options else "Candidates"

        page = st.radio(
            "Navigation",
            options=options,
            key="nav_page",
            label_visibility="collapsed"
        )
        if st.query_params.get("page") != page:
            st.query_params["page"] = page

        st.markdown("<div style='margin-top: 1.25rem; border-top: 1px solid var(--ats-border); padding-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.8125rem; font-weight: 700; color: var(--ats-navy-dark); margin-bottom: 0.25rem;'>Screening Configuration</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.71875rem; color: var(--ats-text-muted); margin-bottom: 0.75rem; line-height: 1.4;'>Complementary model weights used during candidate ranking:</div>", unsafe_allow_html=True)

        text_weight = st.slider(
            "Text Similarity Weight",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_WEIGHT_TEXT_SIMILARITY,
            step=0.05,
            help="TF-IDF full-text similarity weight. The remaining percentage is assigned to Competency Match."
        )
        skill_weight = round(1.0 - text_weight, 2)
        st.markdown(
            f"<div style='font-size: 0.75rem; color: var(--ats-text-muted); background: var(--ats-primary-light); border: 1px solid var(--ats-primary-border); border-radius: var(--ats-radius-sm); padding: 0.45rem 0.65rem; margin-top: 0.35rem;'>"
            f"<div>Full-Text Similarity: <strong>{text_weight*100:.0f}%</strong></div>"
            f"<div style='margin-top: 0.15rem;'>Competency Match: <strong>{skill_weight*100:.0f}%</strong></div>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.session_state["config_text_weight"] = text_weight
        st.session_state["config_skill_weight"] = skill_weight

        st.markdown("<div style='margin-top: 1.25rem; border-top: 1px solid var(--ats-border); padding-top: 0.85rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size: 0.71875rem; color: var(--ats-text-muted); line-height: 1.5;'>"
            "Privacy Standard: <strong>100% Local Processing</strong><br>"
            "Ethical Standard: <strong>Decision-Support</strong> (No auto-reject)"
            "</div>",
            unsafe_allow_html=True
        )

    return page


def get_effective_job_title() -> str:
    """
    Get synchronized job title across all pages.
    Uses the persistent job description if present.
    If empty, falls back to analyzed_jd if screening results exist.
    Otherwise returns 'Not Specified'.
    """
    current_jd = st.session_state.get("persistent_jd_text", "") or st.session_state.get("jd_textarea", "")
    if current_jd and current_jd.strip():
        return extract_job_title(current_jd)
    analyzed_jd = st.session_state.get("analyzed_jd", "")
    if analyzed_jd and analyzed_jd.strip() and st.session_state.get("screening_results"):
        return extract_job_title(analyzed_jd)
    return "Not Specified"


def render_top_header(title: str, subtitle: str, session_info: Optional[str] = None):
    """Render top application shell header bar."""
    if session_info is None:
        session_info = get_effective_job_title()
    st.markdown(f"""
        <div class="ats-top-header">
            <div class="ats-header-left">
                <h1 class="ats-header-title">{html.escape(title)}</h1>
                <div class="ats-header-sub">{html.escape(subtitle)}</div>
            </div>
            <div class="ats-header-right">
                <div class="ats-pill-badge">Job: {html.escape(session_info)}</div>
                <div class="ats-pill-badge" style="background: #F5F6F8; color: #4B5563; border-color: #E1E5EA;">Processing: Local</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# PAGE 1: CANDIDATES OVERVIEW
# ==============================================================================
def render_page_candidates():
    render_top_header(
        title="Candidates",
        subtitle="Manage, upload, and review candidate resume submissions"
    )

    # 1. Job Description & Upload Accordion/Split
    col_jd, col_up = st.columns([1, 1], gap="medium")

    with col_jd:
        with st.container(border=True):
            st.markdown("<div class='ats-card-header'><span>Job Description Setup</span></div>", unsafe_allow_html=True)

            # Ensure persistent_jd_text exists
            if "persistent_jd_text" not in st.session_state:
                st.session_state["persistent_jd_text"] = ""

            # Ensure jd_textarea key is initialized with persistent_jd_text if unmounted or empty
            if "jd_textarea" not in st.session_state or not st.session_state.get("jd_textarea"):
                if st.session_state.get("persistent_jd_text"):
                    st.session_state["jd_textarea"] = st.session_state["persistent_jd_text"]

            # Callbacks for loading and clearing job description
            def load_sample_jd():
                st.session_state["persistent_jd_text"] = SAMPLE_JOB_DESCRIPTION
                st.session_state["jd_textarea"] = SAMPLE_JOB_DESCRIPTION

            def clear_jd():
                st.session_state["persistent_jd_text"] = ""
                st.session_state["jd_textarea"] = ""
                st.session_state["analyzed_jd"] = ""
                st.session_state["screening_results"] = []
                st.session_state["selected_candidate_id"] = None
                st.session_state["uploaded_resumes_cache"] = []
                st.session_state["analyzed_filenames"] = []
                st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1

            def sync_jd_text():
                st.session_state["persistent_jd_text"] = st.session_state.get("jd_textarea", "")

            b_col1, b_col2 = st.columns([1, 1])
            with b_col1:
                st.button(
                    "Load Sample Job Description",
                    on_click=load_sample_jd,
                    use_container_width=True
                )
            with b_col2:
                st.button(
                    "Clear Job Description",
                    on_click=clear_jd,
                    use_container_width=True
                )

            job_description = st.text_area(
                "Job Description Text",
                height=200,
                placeholder="Paste role requirements, technical skills, and experience criteria...",
                key="jd_textarea",
                on_change=sync_jd_text,
                label_visibility="collapsed"
            )
            # Keep persistent_jd_text synchronized
            st.session_state["persistent_jd_text"] = job_description

            if job_description and job_description.strip():
                reqs = extract_job_requirements(job_description)
                if reqs["all_skills"]:
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #4B5563; margin-top: 0.35rem;'>Detected Skills:</div>", unsafe_allow_html=True)
                    badges = " ".join([f"<span class='tag-pill'>{html.escape(s)}</span>" for s in reqs["all_skills"]])
                    st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.35rem;'>{badges}</div>", unsafe_allow_html=True)
            else:
                st.info("No Job Description loaded. Click 'Load Sample Job Description' or paste requirements above.")

    with col_up:
        with st.container(border=True):
            st.markdown("<div class='ats-card-header'><span>Resume Upload & Screening Queue</span></div>", unsafe_allow_html=True)

            uploader_key = f"resume_uploader_{st.session_state.get('uploader_key', 0)}"
            uploaded_files = st.file_uploader(
                "Upload resumes (PDF, DOCX, TXT)",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help=f"Accepts PDF, DOCX, TXT up to {MAX_FILE_SIZE_MB}MB.",
                key=uploader_key,
                label_visibility="collapsed"
            )

            # Ingest newly uploaded files into session cache (single source of truth)
            if "uploaded_resumes_cache" not in st.session_state:
                st.session_state["uploaded_resumes_cache"] = []

            if uploaded_files:
                existing_filenames = {item["filename"] for item in st.session_state["uploaded_resumes_cache"]}
                for f in uploaded_files:
                    if f.name not in existing_filenames:
                        st.session_state["uploaded_resumes_cache"].append({
                            "filename": f.name,
                            "bytes": f.getvalue(),
                            "size": len(f.getvalue())
                        })
                        existing_filenames.add(f.name)

            cached_queue = st.session_state.get("uploaded_resumes_cache", [])

            if cached_queue:
                num_queued = len(cached_queue)
                st.markdown(
                    f"<div style='font-size: 0.8125rem; color: var(--ats-success); background: var(--ats-success-bg); border: 1px solid var(--ats-success-border); border-radius: var(--ats-radius-sm); padding: 0.45rem 0.75rem; font-weight: 600; margin-bottom: 0.45rem; display: flex; align-items: center; justify-content: space-between;'>"
                    f"<span>✓ <strong>{num_queued}</strong> candidate document(s) in active queue</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Render directly visible file queue container (always visible with filenames and sizes)
                file_items_html = []
                for item in cached_queue:
                    size_str = format_file_size(item["size"])
                    fname = html.escape(item["filename"])
                    file_items_html.append(
                        f"<div class='queue-file-item' style='display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0.6rem; margin-bottom: 0.25rem; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; font-size: 0.78125rem; color: #1E293B;'>"
                        f"<span style='overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 75%; display: flex; align-items: center; gap: 0.4rem;'>"
                        f"<span>📄</span> <strong>{fname}</strong>"
                        f"</span>"
                        f"<span style='color: #64748B; font-size: 0.71875rem; font-weight: 500;'>{size_str}</span>"
                        f"</div>"
                    )

                st.markdown(
                    f"<div class='queue-files-container' style='max-height: 160px; overflow-y: auto; margin-bottom: 0.5rem; padding-right: 2px;'>"
                    f"{''.join(file_items_html)}"
                    f"</div>",
                    unsafe_allow_html=True
                )

                if st.button("Clear Resume Queue", key="btn_clear_resume_queue", use_container_width=True):
                    st.session_state["uploaded_resumes_cache"] = []
                    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
                    st.rerun()
            else:
                st.markdown(
                    f"<div style='font-size: 0.75rem; color: var(--ats-text-muted); margin-bottom: 0.65rem; line-height: 1.4;'>"
                    f"Supported formats: <strong>PDF, DOCX, TXT</strong> · Max limit: <strong>{MAX_FILE_SIZE_MB} MB per file</strong>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Analyze action & Optional Demo Dataset Loader
            is_jd_ready = bool(job_description and len(job_description.strip()) >= MIN_JOB_DESCRIPTION_CHARS)
            
            analyze_btn = st.button(
                "Analyze & Rank Candidates",
                type="primary",
                use_container_width=True,
                disabled=not is_jd_ready,
                help="Analyze candidate relevance against this Job Description." if is_jd_ready else f"Provide a complete Job Description (at least {MIN_JOB_DESCRIPTION_CHARS} characters) to enable screening."
            )
            
            # Explicit secondary action to load demo sample resumes for evaluation
            load_demo_btn = st.button(
                "Load & Screen Sample Resumes (Demo)",
                type="secondary",
                use_container_width=True,
                disabled=not is_jd_ready,
                help="Evaluate the 4 prebuilt demo candidate resumes against this Job Description."
            )
            
            if not is_jd_ready:
                st.caption(f"Job Description required ({MIN_JOB_DESCRIPTION_CHARS}+ characters) to run screening.")

    # Screening execution (Explicit user uploads or explicit demo resumes)
    if analyze_btn or load_demo_btn:
        if not is_jd_ready:
            st.error(f"Please provide a complete Job Description (at least {MIN_JOB_DESCRIPTION_CHARS} characters).")
            return

        # If user clicked primary Analyze but has no uploaded resumes, require upload
        active_resumes = st.session_state.get("uploaded_resumes_cache", [])
        if analyze_btn and not active_resumes:
            st.error("Please upload at least one candidate resume document (PDF, DOCX, or TXT) to screen, or click 'Load & Screen Sample Resumes (Demo)' below.")
            return

        with st.spinner("Analyzing candidate documents and vectorizing relevance..."):
            parsed_resumes = []
            failed_parse_count = 0

            if load_demo_btn:
                # Explicitly requested demo resumes only
                resumes_dir = "sample_resumes"
                sample_files = [
                    "resume_01_strong_match.txt",
                    "resume_02_partial_match.docx",
                    "resume_03_unrelated.txt",
                    "resume_04_python_dev.pdf"
                ]
                demo_filenames = []
                for fname in sample_files:
                    fpath = os.path.join(resumes_dir, fname)
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f:
                            parsed_demo = parse_resume(f.read(), fname)
                            # Clearly tag as demo candidate in filename/tag
                            parsed_demo["warning"] = "Demo Sample Candidate"
                            parsed_resumes.append(parsed_demo)
                            demo_filenames.append(fname)
                st.session_state["analyzed_filenames"] = demo_filenames
            else:
                # Strictly process user uploaded files from persistent active queue
                for item in active_resumes:
                    file_bytes = item["bytes"]
                    filename = item["filename"]
                    parsed_res = parse_resume(file_bytes, filename)
                    if not parsed_res.get("success"):
                        failed_parse_count += 1
                    parsed_resumes.append(parsed_res)
                st.session_state["analyzed_filenames"] = [item["filename"] for item in active_resumes]

            if failed_parse_count > 0:
                st.warning(f"{failed_parse_count} uploaded document(s) encountered extraction failures and are flagged below.")

            text_w = st.session_state.get("config_text_weight", DEFAULT_WEIGHT_TEXT_SIMILARITY)
            skill_w = st.session_state.get("config_skill_weight", DEFAULT_WEIGHT_SKILL_MATCH)

            ranked = rank_resumes(
                job_description=job_description,
                parsed_resumes=parsed_resumes,
                weight_text_sim=text_w,
                weight_skill_match=skill_w
            )

            st.session_state["screening_results"] = ranked
            st.session_state["analyzed_jd"] = job_description
            if ranked:
                st.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]
            else:
                st.session_state["selected_candidate_id"] = None

    # Candidate Database Table View
    candidates = st.session_state.get("screening_results", [])

    if not candidates:
        st.markdown(
            '<div style="text-align: center; padding: 3.5rem 1.5rem; color: var(--ats-text-muted); background: var(--ats-surface); border: 1.5px dashed var(--ats-border); border-radius: var(--ats-radius-md); margin-top: 1.5rem; box-shadow: var(--ats-shadow-sm);">'
            '<div style="width: 44px; height: 44px; margin: 0 auto 1rem auto; border-radius: 50%; background: var(--ats-primary-light); display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">📄</div>'
            '<div style="font-size: 1.125rem; font-weight: 700; color: var(--ats-navy-dark); margin-bottom: 0.35rem;">No candidates currently screened</div>'
            '<div style="font-size: 0.84375rem; color: var(--ats-text-muted); max-width: 520px; margin: 0 auto; line-height: 1.5;">Load or enter a Job Description, upload candidate resumes (PDF, DOCX, TXT), and click <strong>Analyze & Rank Candidates</strong> to generate the candidate leaderboard.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    # Stale screening results detection
    analyzed_jd = st.session_state.get("analyzed_jd", "")
    analyzed_filenames = st.session_state.get("analyzed_filenames", [])
    current_filenames = [item["filename"] for item in st.session_state.get("uploaded_resumes_cache", [])]

    jd_is_stale = bool(job_description and analyzed_jd and job_description.strip() != analyzed_jd.strip())
    queue_is_stale = bool(analyzed_filenames and current_filenames and current_filenames != analyzed_filenames)

    if jd_is_stale:
        st.warning(
            "The job description in the editor has been modified since the last screening run. "
            "Click **Analyze & Rank Candidates** above to update candidate rankings for the new requirements."
        )
    elif queue_is_stale:
        st.warning(
            "The candidate documents in the screening queue have changed since the last screening run. "
            "Click **Analyze & Rank Candidates** above to update candidate rankings for the updated documents."
        )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Filter & Search Controls Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
    with f_col1:
        search_query = st.text_input("Search candidates", placeholder="🔍 Search candidates by name, email, or filename...", label_visibility="collapsed")
    with f_col2:
        status_filter = st.selectbox("Status", options=["All Statuses", "Ready for Review", "Review Notice", "Extraction Failed"], label_visibility="collapsed")
    with f_col3:
        min_score = st.selectbox("Min Score", options=["All Scores", ">= 40%", ">= 25%", "< 25%"], label_visibility="collapsed")
    with f_col4:
        if candidates:
            csv_data = generate_candidates_csv(candidates)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data.encode("utf-8-sig"),
                file_name="candidate_screening_report.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Filter candidates
    filtered = []
    for c in candidates:
        # Search match
        name = c.get("name") or ""
        email = " ".join(c.get("emails", []))
        filename = c.get("filename", "")
        combined_text = f"{name} {email} {filename}".lower()
        if search_query and search_query.strip().lower() not in combined_text:
            continue

        # Status filter
        if status_filter == "Ready for Review" and (not c.get("success") or c.get("warning")):
            continue
        elif status_filter == "Review Notice" and not c.get("warning"):
            continue
        elif status_filter == "Extraction Failed" and c.get("success"):
            continue

        # Score filter
        score = c.get("overall_score", 0.0)
        if min_score == ">= 40%" and score < 40.0:
            continue
        elif min_score == ">= 25%" and score < 25.0:
            continue
        elif min_score == "< 25%" and score >= 25.0:
            continue

        filtered.append(c)

    if not candidates:
        st.markdown("""
            <div class="ats-card" style="text-align: center; padding: 3rem 1rem; color: #667085;">
                <div style="font-size: 1.1rem; font-weight: 600; color: #202733; margin-bottom: 0.5rem;">No candidates loaded</div>
                <div style="font-size: 0.8125rem;">Paste a job description and upload resumes above, or click "Load Sample Job Description" to run screening.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"<div style='font-size: 0.8125rem; color: #667085; margin-bottom: 0.35rem;'>Showing <strong>{len(filtered)}</strong> of <strong>{len(candidates)}</strong> candidate(s)</div>", unsafe_allow_html=True)

    # Render data table
    table_rows = []
    for c in filtered:
        rank_str = html.escape(f"#{c.get('rank', '-')}")
        name_val = format_field(c.get("name"), default="Not detected")
        name_str = html.escape(name_val)
        initials = "".join([part[0].upper() for part in name_val.split()[:2]]) if name_val != "Not detected" else "??"
        avatar_html = f"<span class='candidate-avatar'>{html.escape(initials)}</span>"
        email_val = ", ".join(c.get("emails", [])) if c.get("emails") else ""
        email_str = f"<div style='font-size: 0.75rem; color: #667085;'>{html.escape(email_val)}</div>" if email_val else ""
        filename_str = html.escape(c.get("filename", ""))

        score = c.get("overall_score", 0.0)
        score_bar = f"<div class='score-bar-bg'><div class='score-bar-fill' style='width: {min(100, int(score))}%;'></div></div>"
        score_cell = f"<strong>{score:.1f}%</strong>{score_bar}"

        sim_score = c.get("text_similarity_score", 0.0)
        sim_cell = f"{sim_score:.1f}%"

        skill_sc = c.get("skill_match_score", 0.0)
        skill_score_cell = f"{skill_sc:.1f}%"

        matched_skills = c.get("matched_skills", [])
        if matched_skills:
            top_skills = matched_skills[:3]
            skill_badges_inner = " ".join([f"<span class='tag-pill tag-pill-match'>{html.escape(s)}</span>" for s in top_skills])
            if len(matched_skills) > 3:
                skill_badges_inner += f" <span class='tag-pill'>+{len(matched_skills)-3}</span>"
            skill_badges = f"<div style='display: flex; flex-wrap: wrap; gap: 0.25rem; align-items: center;'>{skill_badges_inner}</div>"
        else:
            skill_badges = "<span style='color: #9CA3AF; font-size: 0.75rem;'>None matched</span>"

        # Status badge
        if not c.get("success"):
            status_cell = '<span class="badge-error">Extraction failed</span>'
        elif c.get("warning"):
            status_cell = '<span class="badge-warning">Review notice</span>'
        else:
            status_cell = '<span class="badge-ready">Ready for review</span>'

        row = (
            f"<tr>"
            f"<td style='font-weight: 600; color: #4B5563;'>{rank_str}</td>"
            f"<td>{avatar_html}<strong>{name_str}</strong>{email_str}</td>"
            f"<td style='color: #6B7280; font-family: monospace; font-size: 0.75rem;'>{filename_str}</td>"
            f"<td>{score_cell}</td>"
            f"<td style='color: #4B5563;'>{sim_cell}</td>"
            f"<td style='color: #4B5563;'>{skill_score_cell}</td>"
            f"<td>{skill_badges}</td>"
            f"<td>{status_cell}</td>"
            f"</tr>"
        )
        table_rows.append(row)

    table_markup = (
        '<div class="data-table-container">'
        '<table class="data-table leaderboard-table">'
        '<thead>'
        '<tr>'
        '<th>Rank</th>'
        '<th>Candidate Name</th>'
        '<th>Original Filename</th>'
        '<th>Overall Score</th>'
        '<th>Text Similarity</th>'
        '<th>Skill Match</th>'
        '<th>Matched Skills</th>'
        '<th>Review Status</th>'
        '</tr>'
        '</thead>'
        '<tbody>'
        + "".join(table_rows)
        + '</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(table_markup, unsafe_allow_html=True)


def render_gauge_svg(score: float, label: str, sub: str) -> str:
    """Render a clean semi-circular SVG gauge matching enterprise assessment displays."""
    pct = max(0.0, min(100.0, score))
    offset = 125.6 * (1.0 - (pct / 100.0))
    return (
        f'<div class="gauge-card">'
        f'<svg viewBox="0 0 100 58" width="130" height="72">'
        f'<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#EAEFF5" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#304B70" stroke-width="8" stroke-dasharray="125.6" stroke-dashoffset="{offset:.1f}" stroke-linecap="round"/>'
        f'<text x="50" y="47" font-size="14" font-weight="700" text-anchor="middle" fill="#202733">{score:.1f}%</text>'
        f'</svg>'
        f'<div class="gauge-label">{html.escape(label)}</div>'
        f'<div class="gauge-sub">{html.escape(sub)}</div>'
        f'</div>'
    )


# ==============================================================================
# PAGE 2: SCREENING OVERVIEW & ANALYTICS
# ==============================================================================
def render_page_overview():
    render_top_header(
        title="Screening Overview",
        subtitle="Analytical overview of candidate match rates and role competency coverage"
    )

    candidates = st.session_state.get("screening_results", [])
    current_jd = st.session_state.get("persistent_jd_text", "") or st.session_state.get("jd_textarea", "")
    analyzed_jd = st.session_state.get("analyzed_jd", "")
    job_description = analyzed_jd or current_jd

    analyzed_filenames = st.session_state.get("analyzed_filenames", [])
    current_filenames = [item["filename"] for item in st.session_state.get("uploaded_resumes_cache", [])]

    jd_is_stale = bool(current_jd.strip() and analyzed_jd.strip() and current_jd.strip() != analyzed_jd.strip() and candidates)
    queue_is_stale = bool(candidates and analyzed_filenames and current_filenames and current_filenames != analyzed_filenames)

    if jd_is_stale:
        st.warning(
            "The metrics and competency coverage below reflect the previously analyzed job description. "
            "Return to **Candidates** and click **Analyze & Rank Candidates** to refresh analysis for the updated job description."
        )
    elif queue_is_stale:
        st.warning(
            "The metrics and competency coverage below reflect previous candidate documents. "
            "Return to **Candidates** and click **Analyze & Rank Candidates** to refresh analysis for the updated screening queue."
        )

    if not candidates:
        st.markdown(
            '<div style="text-align: center; padding: 3.5rem 1.5rem; color: var(--ats-text-muted); background: var(--ats-surface); border: 1.5px dashed var(--ats-border); border-radius: var(--ats-radius-md); box-shadow: var(--ats-shadow-sm);">'
            '<div style="width: 44px; height: 44px; margin: 0 auto 1rem auto; border-radius: 50%; background: var(--ats-primary-light); display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">📊</div>'
            '<div style="font-size: 1.125rem; font-weight: 700; color: var(--ats-navy-dark); margin-bottom: 0.35rem;">No screening analysis available</div>'
            '<div style="font-size: 0.84375rem; color: var(--ats-text-muted); max-width: 500px; margin: 0 auto; line-height: 1.5;">Switch to the <strong>Candidates</strong> tab to load or enter a Job Description, upload applicant resumes, and trigger the screening pipeline.</div>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    successful = [c for c in candidates if c.get("success")]
    failed = [c for c in candidates if not c.get("success")]
    with_skills = [c for c in successful if len(c.get("matched_skills", [])) > 0]
    with_warnings = [c for c in successful if c.get("warning")]

    avg_score = sum(c.get("overall_score", 0.0) for c in successful) / len(successful) if successful else 0.0
    top_score = max((c.get("overall_score", 0.0) for c in successful), default=0.0)
    coverage_rate = (len(with_skills) / len(successful) * 100.0) if successful else 0.0
    top_cand = next((c for c in successful if c.get("overall_score", 0.0) == top_score), None)
    top_name = top_cand.get("name", "Candidate") if top_cand else "None"

    # Reference 3 Top Semi-Circular Visual Gauges
    g1 = render_gauge_svg(top_score, "Top Candidate Match", f"{top_name}")
    g2 = render_gauge_svg(avg_score, "Cohort Average Match", f"{len(successful)} candidates evaluated")
    g3 = render_gauge_svg(coverage_rate, "Competency Coverage", f"{len(with_skills)}/{len(successful)} met 1+ skills")
    st.markdown(f'<div class="gauge-grid">{g1}{g2}{g3}</div>', unsafe_allow_html=True)

    # 1. Summary Metrics
    st.markdown(
        f'<div class="metric-grid">'
        f'<div class="metric-item"><div class="metric-item-label">Candidates Evaluated</div><div class="metric-item-value">{len(candidates)}</div><div class="metric-item-sub">{len(successful)} parsed successfully</div></div>'
        f'<div class="metric-item"><div class="metric-item-label">Average Match Score</div><div class="metric-item-value">{avg_score:.1f}%</div><div class="metric-item-sub">Top match: {top_score:.1f}%</div></div>'
        f'<div class="metric-item"><div class="metric-item-label">Competency Matches</div><div class="metric-item-value">{len(with_skills)}</div><div class="metric-item-sub">Had 1+ required skills</div></div>'
        f'<div class="metric-item"><div class="metric-item-label">Requires Review</div><div class="metric-item-value">{len(failed) + len(with_warnings)}</div><div class="metric-item-sub">{len(with_warnings)} limited text, {len(failed)} failed</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    col_l, col_r = st.columns([1, 1], gap="medium")

    # 2. Competency Coverage Breakdown
    with col_l:
        with st.container(border=True):
            st.markdown("<div class='ats-card-header'><span>Required Competency Coverage</span></div>", unsafe_allow_html=True)

            reqs = extract_job_requirements(job_description)
            required_skills = reqs.get("required_skills", [])

            if required_skills:
                total_cand = len(successful) or 1
                for skill in required_skills:
                    matching_count = sum(1 for c in successful if skill in c.get("matched_skills", []))
                    pct = int((matching_count / total_cand) * 100)

                    st.markdown(
                        f'<div class="coverage-row">'
                        f'<div class="coverage-label" title="{html.escape(skill)}">{html.escape(skill)}</div>'
                        f'<div class="coverage-bar-track"><div class="coverage-bar-fill" style="width: {pct}%;"></div></div>'
                        f'<div class="coverage-count">{matching_count}/{total_cand} ({pct}%)</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No explicit skills extracted from the active job description.")

    # 3. Role Specification Summary & Weights
    with col_r:
        with st.container(border=True):
            st.markdown("<div class='ats-card-header'><span>Screening Criteria & Configuration</span></div>", unsafe_allow_html=True)

            text_w = st.session_state.get("config_text_weight", DEFAULT_WEIGHT_TEXT_SIMILARITY)
            skill_w = st.session_state.get("config_skill_weight", DEFAULT_WEIGHT_SKILL_MATCH)

            st.markdown(
                f'<div style="font-size: 0.8125rem; line-height: 1.6;">'
                f'<div>• <strong>Textual Similarity Weight:</strong> {text_w*100:.0f}% (TF-IDF Cosine Vector Alignment)</div>'
                f'<div>• <strong>Competency Overlap Weight:</strong> {skill_w*100:.0f}% (Cataloged Taxonomy Overlap)</div>'
                f'<div>• <strong>Total Cataloged Skills in Role:</strong> {len(reqs.get("all_skills", []))}</div>'
                f'<div>• <strong>Preferred Qualifications Distinguishable:</strong> {"Yes" if reqs.get("preferred_skills") else "None listed"}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            if reqs.get("experience_requirements"):
                st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #4B5563; margin-top: 0.75rem;'>Experience Criteria Extracted:</div>", unsafe_allow_html=True)
                for e in reqs["experience_requirements"][:3]:
                    st.markdown(f"<div class='evidence-quote'>{html.escape(e)}</div>", unsafe_allow_html=True)

    # 4. Top Candidate Score Comparison Table
    with st.container(border=True):
        st.markdown("<div class='ats-card-header'><span>Candidate Match Comparison</span></div>", unsafe_allow_html=True)

        comp_rows = []
        for c in candidates[:10]:
            name_val = format_field(c.get("name"), default="Not detected")
            status_val = '<span class="badge-ready">Parsed</span>' if c.get("success") and not c.get("warning") else ('<span class="badge-warning">Limited text</span>' if c.get("warning") else '<span class="badge-error">Failed</span>')

            comp_rows.append(
                f"<tr>"
                f"<td style='font-weight: 600; color: #4B5563;'>#{c.get('rank', '-')}</td>"
                f"<td><strong>{html.escape(name_val)}</strong></td>"
                f"<td><code>{html.escape(c.get('filename', ''))}</code></td>"
                f"<td><strong>{c.get('overall_score', 0.0):.1f}%</strong></td>"
                f"<td>{c.get('text_similarity_score', 0.0):.1f}%</td>"
                f"<td>{c.get('skill_match_score', 0.0):.1f}%</td>"
                f"<td>{len(c.get('matched_skills', []))} matched</td>"
                f"<td>{status_val}</td>"
                f"</tr>"
            )

        st.markdown(
            f'<div class="data-table-container">'
            f'<table class="data-table">'
            f'<thead><tr><th>Rank</th><th>Candidate</th><th>Filename</th><th>Overall Score</th><th>Text Similarity</th><th>Competency Match</th><th>Skills</th><th>Status</th></tr></thead>'
            f'<tbody>{"".join(comp_rows)}</tbody>'
            f'</table>'
            f'</div>',
            unsafe_allow_html=True
        )


# ==============================================================================
# PAGE 3: CANDIDATE REVIEW WORKSPACE
# ==============================================================================
def render_page_review():
    render_top_header(
        title="Candidate Review",
        subtitle="Individual profile inspection, qualification evidence, and skill comparison"
    )

    candidates = st.session_state.get("screening_results", [])
    current_jd = st.session_state.get("persistent_jd_text", "") or st.session_state.get("jd_textarea", "")
    analyzed_jd = st.session_state.get("analyzed_jd", "")

    analyzed_filenames = st.session_state.get("analyzed_filenames", [])
    current_filenames = [item["filename"] for item in st.session_state.get("uploaded_resumes_cache", [])]

    jd_is_stale = bool(current_jd.strip() and analyzed_jd.strip() and current_jd.strip() != analyzed_jd.strip() and candidates)
    queue_is_stale = bool(candidates and analyzed_filenames and current_filenames and current_filenames != analyzed_filenames)

    if jd_is_stale:
        st.warning(
            "The candidate evaluations below reflect the previously analyzed job description. "
            "Return to **Candidates** and click **Analyze & Rank Candidates** to refresh analysis for the updated job description."
        )
    elif queue_is_stale:
        st.warning(
            "The candidate evaluations below reflect previous candidate documents. "
            "Return to **Candidates** and click **Analyze & Rank Candidates** to refresh analysis for the updated screening queue."
        )

    if not candidates:
        st.markdown("""
            <div style="text-align: center; padding: 3.5rem 1.5rem; color: var(--ats-text-muted); background: var(--ats-surface); border: 1.5px dashed var(--ats-border); border-radius: var(--ats-radius-md); box-shadow: var(--ats-shadow-sm);">
                <div style="width: 44px; height: 44px; margin: 0 auto 1rem auto; border-radius: 50%; background: var(--ats-primary-light); display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">🔍</div>
                <div style="font-size: 1.125rem; font-weight: 700; color: var(--ats-navy-dark); margin-bottom: 0.35rem;">No candidates available for review</div>
                <div style="font-size: 0.84375rem; color: var(--ats-text-muted); max-width: 500px; margin: 0 auto; line-height: 1.5;">Switch to the <strong>Candidates</strong> page to upload resumes and run screening. Candidates will appear in this workspace for split-panel dossier review.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    # Two-Panel Layout: Left Candidate Selector, Right Detailed Dossier
    col_list, col_profile = st.columns([1, 2], gap="large")

    # Maintain selection in session state
    candidate_ids = [c["candidate_id"] for c in candidates]
    if "selected_candidate_id" not in st.session_state or st.session_state["selected_candidate_id"] not in candidate_ids:
        st.session_state["selected_candidate_id"] = candidate_ids[0]

    with col_list:
        with st.container(border=True):
            st.markdown("<div style='font-size: 0.8125rem; font-weight: 600; color: #304B70; padding-bottom: 0.5rem; border-bottom: 1px solid #E1E5EA; margin-bottom: 0.5rem;'>Candidate Queue</div>", unsafe_allow_html=True)

            # Candidate selection list
            for cand in candidates:
                c_id = cand["candidate_id"]
                name = format_field(cand.get("name"), default=cand.get("filename", "Unknown"))
                score = cand.get("overall_score", 0.0)
                skills_count = len(cand.get("matched_skills", []))
                is_active = (c_id == st.session_state["selected_candidate_id"])

                label = f"#{cand.get('rank', '-')} {name} — {score:.1f}% ({skills_count} skills)"
                if st.button(label, key=f"sel_{c_id}", use_container_width=True, type="secondary" if not is_active else "primary"):
                    st.session_state["selected_candidate_id"] = c_id
                    st.rerun()

    # Active Candidate Record
    selected = next((c for c in candidates if c["candidate_id"] == st.session_state["selected_candidate_id"]), candidates[0])

    with col_profile:
        with st.container(border=True):
            cand_name = format_field(selected.get("name"), default="Not detected")
            rank_label = f"#{selected.get('rank', '-')}"
            score_label = f"{selected.get('overall_score', 0.0):.1f}%"

            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid #E1E5EA; padding-bottom: 0.75rem; margin-bottom: 1rem;">
                    <div>
                        <h2 style="font-size: 1.25rem; font-weight: 700; color: #202733; margin: 0;">{html.escape(cand_name)}</h2>
                        <div style="font-size: 0.8125rem; color: #667085; margin-top: 0.15rem;">Rank {rank_label} · File: <code>{html.escape(selected.get('filename', ''))}</code></div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.35rem; font-weight: 700; color: #304B70;">{score_label}</div>
                        <div style="font-size: 0.75rem; color: #667085;">Composite Match</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if not selected.get("success"):
                st.error(f"Extraction Failure: {selected.get('error', 'Unknown parsing error')}")
                st.caption("Verify that document text is uncorrupted.")
                return

            if selected.get("warning"):
                st.markdown(f"<div class='callout-warning'><strong>Extraction Notice:</strong> {html.escape(selected['warning'])}</div>", unsafe_allow_html=True)

            # Tabbed profile view for compactness
            tab_profile, tab_skills, tab_evidence, tab_raw = st.tabs(["Overview & Contact", "Skills Alignment", "Evidence Quotes", "Raw Document"])

            with tab_profile:
                p_col1, p_col2 = st.columns([1, 1])
                with p_col1:
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #667085; text-transform: uppercase;'>Contact Details</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8125rem; margin-top: 0.35rem;'>Email: <strong>{html.escape(format_field(selected.get('emails')))}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8125rem; margin-top: 0.2rem;'>Phone: <strong>{html.escape(format_field(selected.get('phones')))}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8125rem; margin-top: 0.2rem;'>Document: <code>{html.escape(selected.get('filename', ''))}</code></div>", unsafe_allow_html=True)

                with p_col2:
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #667085; text-transform: uppercase;'>Scoring Components</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8125rem; margin-top: 0.35rem;'>Textual Similarity: <strong>{selected.get('text_similarity_score', 0.0):.1f}%</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.8125rem; margin-top: 0.2rem;'>Competency Match: <strong>{selected.get('skill_match_score', 0.0):.1f}%</strong></div>", unsafe_allow_html=True)
                    st.caption(selected.get("score_explanation", ""))

            with tab_skills:
                matched = selected.get("matched_skills", [])
                missing = selected.get("missing_skills", [])
                candidate_all = selected.get("candidate_skills", [])

                st.markdown(f"<div style='font-size: 0.8125rem; font-weight: 600; color: #166534; margin-bottom: 0.35rem;'>Matched Competencies ({len(matched)}):</div>", unsafe_allow_html=True)
                if matched:
                    badges_m = " ".join([f"<span class='tag-pill tag-pill-match'>{html.escape(s)}</span>" for s in matched])
                    st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.75rem;'>{badges_m}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No cataloged role competencies matched in document text.")

                st.markdown(f"<div style='font-size: 0.8125rem; font-weight: 600; color: #4B5563; margin-bottom: 0.35rem;'>Unmatched Role Competencies ({len(missing)}):</div>", unsafe_allow_html=True)
                if missing:
                    badges_u = " ".join([f"<span class='tag-pill tag-pill-missing'>{html.escape(s)}</span>" for s in missing])
                    st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.75rem;'>{badges_u}</div>", unsafe_allow_html=True)
                else:
                    st.caption("All role competencies matched.")

                if candidate_all:
                    st.markdown(f"<div style='font-size: 0.8125rem; font-weight: 600; color: #1E293B; margin-top: 0.75rem; margin-bottom: 0.35rem;'>All Detected Candidate Skills ({len(candidate_all)}):</div>", unsafe_allow_html=True)
                    badges_cand = " ".join([f"<span class='tag-pill'>{html.escape(s)}</span>" for s in candidate_all])
                    st.markdown(f"<div style='display: flex; flex-wrap: wrap; gap: 0.35rem;'>{badges_cand}</div>", unsafe_allow_html=True)

            with tab_evidence:
                ev_col1, ev_col2 = st.columns([1, 1])
                with ev_col1:
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #667085; text-transform: uppercase; margin-bottom: 0.35rem;'>Education Evidence</div>", unsafe_allow_html=True)
                    edu_ev = selected.get("education_evidence", [])
                    if edu_ev:
                        for item in edu_ev:
                            st.markdown(f"<div class='evidence-quote'>{html.escape(item)}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("No explicit degree keywords matched in resume text.")

                with ev_col2:
                    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #667085; text-transform: uppercase; margin-bottom: 0.35rem;'>Experience Evidence</div>", unsafe_allow_html=True)
                    exp_ev = selected.get("experience_evidence", [])
                    if exp_ev:
                        for item in exp_ev:
                            st.markdown(f"<div class='evidence-quote'>{html.escape(item)}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("No explicit work experience indicators detected.")

            with tab_raw:
                raw_text = selected.get("raw_text", "")
                if len(raw_text) > MAX_TEXT_PREVIEW_CHARS:
                    preview = raw_text[:MAX_TEXT_PREVIEW_CHARS] + "\n\n... [Preview truncated for display]"
                else:
                    preview = raw_text
                st.text_area("Extracted Resume Text", value=preview, height=220, disabled=True, label_visibility="collapsed")


def seed_default_candidates():
    """Ensure the Candidates page opens with active candidate data, metrics, and dossier review."""
    resumes_dir = "sample_resumes"
    sample_files = [
        "resume_01_strong_match.txt",
        "resume_02_partial_match.docx",
        "resume_03_unrelated.txt",
        "resume_04_python_dev.pdf"
    ]
    parsed_resumes = []
    for fname in sample_files:
        fpath = os.path.join(resumes_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "rb") as f:
                    parsed = parse_resume(f.read(), fname)
                    parsed_resumes.append(parsed)
            except Exception:
                pass
    if parsed_resumes:
        ranked = rank_resumes(SAMPLE_JOB_DESCRIPTION, parsed_resumes)
        st.session_state["screening_results"] = ranked
        st.session_state["analyzed_jd"] = SAMPLE_JOB_DESCRIPTION
        st.session_state["analyzed_filenames"] = [c["filename"] for c in ranked]
        if ranked:
            st.session_state["selected_candidate_id"] = ranked[0]["candidate_id"]


# ==============================================================================
# MAIN ROUTING CONTROLLER
# ==============================================================================
def main():
    setup_theme_and_styles()

    # Initialize persistent ATS session state variables
    if "persistent_jd_text" not in st.session_state:
        st.session_state["persistent_jd_text"] = ""
    if "uploaded_resumes_cache" not in st.session_state:
        st.session_state["uploaded_resumes_cache"] = []
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0
    if "analyzed_filenames" not in st.session_state:
        st.session_state["analyzed_filenames"] = []
    if "screening_results" not in st.session_state:
        st.session_state["screening_results"] = []
    if "analyzed_jd" not in st.session_state:
        st.session_state["analyzed_jd"] = ""
    if "selected_candidate_id" not in st.session_state:
        st.session_state["selected_candidate_id"] = None

    selected_page = render_sidebar_nav()

    if selected_page == "Candidates":
        render_page_candidates()
    elif selected_page == "Screening Overview":
        render_page_overview()
    elif selected_page == "Candidate Review":
        render_page_review()


if __name__ == "__main__":
    main()
