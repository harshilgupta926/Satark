'''


# 🧰 CORE PYTHON / SYSTEM
import os
import re
import json
import base64
import hashlib
import socket
import ipaddress
import html
from datetime import datetime

# 🌐 WEB / URL HANDLING
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

# 🤖 AI / WEB APP
import streamlit as st
from groq import Groq

# 📄 FILE & IMAGE PROCESSING
from pypdf import PdfReader
from PIL import Image

# 📑 PDF GENERATION
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether
)

# ============================================================
# SATARK — Smart AI Threat Analysis & Risk Knowledge
# FINAL single-file Streamlit application
#
# Keeps the original SATARK analysis flow, while adding:
# - automatic Groq model discovery
# - resilient vision-model selection (now with fallback chain)
# - improved result presentation
# - session history + report export
# - Scam Challenge
# - SATARK Academy
# - Classroom Mode
# - evidence / confidence / actions
# - privacy-first session storage
#
# CHANGES IN THIS VERSION:
# 1. calibrate_confidence() no longer force-floors confidence to 95-99.99%.
#    It now reports a value that actually reflects model + evidence strength,
#    across the full 0-100 range.
# 2. render_result() color-codes the confidence metric (red/amber/green)
#    so low-confidence results are visually distinct.
# 3. VISION_MODEL_PREFERENCES is now a real fallback chain instead of a
#    single hardcoded model; analyze_with_groq tries each in order instead
#    of giving up after the first failure.
# 4. is_scam_claim / normalize_result_consistency now trust the model's
#    explicit threat_category field first, and only fall back to regex
#    parsing of prose when the category is missing/ambiguous. This makes
#    scam/phishing detection less fragile to wording changes.
# 5. SYSTEM_PROMPT's confidence instruction is now explicit about using the
#    full 0-100 range honestly instead of defaulting high.
# ============================================================

st.set_page_config(
    page_title="SATARK — AI Threat Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS ----------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap');

:root {
    --bg:#050505; --surface:#111113; --surface2:#18181b;
    --line:rgba(255,255,255,.10); --line2:rgba(255,255,255,.16);
    --text:#f7f7f9; --soft:#e1e1e6; --muted:#b4b4bd;
    --violet:#a99cff; --violet2:rgba(155,140,255,.13);
    --safe:#30d158; --warn:#ffb340; --danger:#ff453a;
}
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:"Manrope",sans-serif}
body{background:var(--bg);color:var(--text)}
h1,h2,h3,h4,h5,h6{color:#f5f5f7!important}
div[data-testid="stMarkdownContainer"] p,div[data-testid="stMarkdownContainer"] li{color:#e2e2e8!important}
div[data-testid="stCaptionContainer"]{color:#c8c8d1!important}
a{color:#a99cff}

.stApp{min-height:100vh;background:
 radial-gradient(circle at 50% -10%,rgba(155,140,255,.09),transparent 30rem),
 radial-gradient(circle at 90% 35%,rgba(255,255,255,.035),transparent 25rem),
 linear-gradient(180deg,#050505 0%,#080809 55%,#050505 100%)}
.block-container{max-width:1480px;padding:1.2rem clamp(1rem,3vw,3rem) 4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0a0b,#060607);border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"]>div:first-child{padding-top:1.1rem}
[data-testid="stSidebar"] label{color:#f5f5f7!important;font-weight:650!important}
[data-testid="stSidebar"] input::placeholder{color:#8f8f98!important}

.brand{padding:8px 4px 24px}.brand-logo{font-family:Sora;font-weight:900;font-size:1.55rem;letter-spacing:-.06em;color:#ffffff;text-shadow:0 0 22px rgba(169,156,255,.22)}.brand-dot{color:#c9c1ff;text-shadow:0 0 10px rgba(169,156,255,.65)}
.brand-tag{margin-top:5px;color:var(--muted);font-size:.78rem;line-height:1.45}
.side-label{margin:19px 0 8px;color:#8f8f98;font-size:.67rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.privacy{padding:14px;border:1px solid var(--line);border-radius:15px;background:rgba(255,255,255,.035);color:var(--soft);font-size:.78rem;line-height:1.55}

.hero{
    position:relative;
    overflow:hidden;
    padding:clamp(3.2rem,7vw,6.4rem) 1.5rem;
    margin-bottom:2.2rem;
    border:1px solid var(--line);
    border-radius:28px;
    text-align:center;
    background:
        radial-gradient(circle at 50% 0%,rgba(255,255,255,.085),transparent 38%),
        radial-gradient(circle at 82% 70%,rgba(155,140,255,.07),transparent 28%),
        linear-gradient(145deg,rgba(25,25,28,.82),rgba(9,9,10,.92));
    box-shadow:0 30px 90px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.06);
    backdrop-filter:blur(24px);
    -webkit-backdrop-filter:blur(24px);
}
.hero:before{
    content:"";position:absolute;width:360px;height:360px;left:50%;top:-300px;
    transform:translateX(-50%);border-radius:50%;background:rgba(255,255,255,.08);
    filter:blur(80px);pointer-events:none;
}
.hero:after{
    content:"";position:absolute;left:15%;right:15%;bottom:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(214,179,106,.65),transparent);
}
.pill{
    position:relative;display:inline-flex;align-items:center;min-height:34px;padding:6px 14px;
    border:1px solid rgba(214,179,106,.36);border-radius:999px;color:#e8d5a7;
    background:rgba(214,179,106,.07);font-size:.68rem;font-weight:800;letter-spacing:.15em;
}
.hero h1{
    position:relative;margin:18px 0 12px;font-family:Sora,"Manrope",sans-serif;
    font-size:clamp(3.05rem,8vw,6.2rem);line-height:.91;letter-spacing:-.075em;
    color:var(--text);
}
.hero h1 .hero-primary{display:inline-block;font-weight:450;color:#f3f3f6;font-size:.86em}
.hero h1 .hero-secondary{display:inline-block;font-weight:450;color:#e6e6eb;font-size:.86em}
.hero h1 .hero-brand{font-weight:850;color:#ffffff;background:linear-gradient(105deg,#ffffff 8%,#e2defe 55%,#a99cff 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{position:relative;max-width:780px;margin:0 auto;color:#bfc0c8;font-size:clamp(1rem,2vw,1.12rem);line-height:1.7}
.hero p strong{color:#f0f0f3;font-weight:750}
.hero-actions{margin-top:24px}
.section-title{margin:2rem 0 .4rem;font-family:Sora;font-size:1.25rem;font-weight:750;color:#f2f2f5}.section-copy{margin:0 0 1rem;color:#d0d0d8;font-size:.9rem}.section-copy strong{color:#f0f0f3;font-weight:650}

div[data-testid="stButton"]>button{min-height:46px;border-radius:13px;border:1px solid var(--line);background:rgba(255,255,255,.045);color:var(--text);font-weight:700;transition:.2s ease}
div[data-testid="stButton"]>button:hover{transform:translateY(-2px);border-color:rgba(155,140,255,.48);background:rgba(155,140,255,.08);box-shadow:0 15px 35px rgba(0,0,0,.28)}
div[data-testid="stButton"]>button[kind="primary"]{border-color:rgba(155,140,255,.55);background:linear-gradient(135deg,#28233f,#15151a)}

.scanner{min-height:88px;padding:10px 12px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.035);text-align:center}.scanner-icon{font-size:1.05rem;line-height:1}.scanner-title{margin-top:4px;font-weight:800;color:#f4f4f7}.scanner-copy{margin-top:2px;color:#d0d0d8;font-size:.68rem;line-height:1.35}.active{border-color:rgba(169,156,255,.62);background:rgba(155,140,255,.09);box-shadow:0 0 0 1px rgba(155,140,255,.10)}

textarea,[data-testid="stTextInput"] input,[data-baseweb="select"]>div{font-size:16px!important;color:var(--text)!important;background:#141416!important;border:1px solid var(--line)!important;border-radius:13px!important}
textarea::placeholder,[data-testid="stTextInput"] input::placeholder{color:#9a9aa4!important;opacity:1!important}
textarea:focus,[data-testid="stTextInput"] input:focus{border-color:rgba(155,140,255,.7)!important;box-shadow:0 0 0 3px rgba(155,140,255,.12)!important}
[data-baseweb="select"] input{caret-color:transparent!important}
[data-baseweb="popover"],[data-baseweb="menu"]{background:#19191c!important;border:1px solid var(--line)!important;border-radius:13px!important;color:#fff!important}
[data-baseweb="menu"] [role="option"]{background:transparent!important;color:#fff!important;min-height:44px!important}.stFileUploader>div{border-radius:14px!important}
[data-testid="stFileUploaderDropzone"]{min-height:125px!important;border:1.5px dashed rgba(155,140,255,.42)!important;border-radius:15px!important;background:rgba(155,140,255,.035)!important}
[data-testid="stFileUploader"] *{color:#e1e1e6!important}

.analyze{margin-top:10px}.analyze div[data-testid="stButton"]>button{min-height:53px;border-radius:999px;font-size:1rem;background:linear-gradient(135deg,#2a2443,#151519)}

.result{padding:24px;margin-top:20px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.018));box-shadow:0 25px 65px rgba(0,0,0,.25)}
.result-head{font-family:Sora;font-size:1.3rem;font-weight:800;color:#f5f5f7}.eyebrow{color:#c9c9d2;font-size:.75rem;margin-top:4px}.metric{min-height:112px;padding:17px;border:1px solid var(--line);border-radius:15px;background:rgba(255,255,255,.03)}.metric-label{color:#d0d0d8;font-size:.68rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}.metric-value{margin-top:7px;font-family:Sora;font-size:1.4rem;font-weight:800;color:#f5f5f7}.safe{color:var(--safe)}.caution{color:var(--warn)}.critical{color:var(--danger)}
.bar{height:10px;margin:12px 0;border-radius:999px;background:#252528;overflow:hidden}.bar>div{height:100%;background:linear-gradient(90deg,var(--safe),var(--warn),var(--danger));border-radius:inherit}
.verdict{padding:17px;margin-top:14px;border-left:3px solid var(--violet);border-radius:12px;background:var(--violet2);line-height:1.65;color:#e1e1e6}.verdict strong{color:#ffffff}
.evidence,.action,.info-card,.challenge-card{height:100%;padding:17px;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.03)}
.evidence>strong,.action>strong{color:#f4f4f7}.evidence-item{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.08);color:#e0e0e5}.evidence-item:last-child{border-bottom:0}
.action-item{display:flex;gap:10px;padding:9px 0;color:#e0e0e5}
.badge{display:inline-block;padding:5px 9px;border-radius:999px;background:rgba(155,140,255,.1);border:1px solid rgba(155,140,255,.2);color:#cfc9ff;font-size:.7rem;font-weight:800}
.confidence{font-size:.82rem;color:#bdbdc5}

.feature-card{padding:20px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.03);height:100%}.feature-icon{font-size:1.4rem}.feature-title{margin-top:8px;font-weight:800;color:#f1f1f4}.feature-copy{margin-top:5px;color:#d0d0d8;font-size:.78rem;line-height:1.5}
.challenge-q{font-family:Sora;font-size:1.15rem;font-weight:750;line-height:1.45;color:#f1f1f4}.challenge-answer{padding:13px;border-radius:12px;background:rgba(255,255,255,.04);border:1px solid var(--line);color:#f0f0f3;line-height:1.55}


.report-section{margin-top:24px;padding:22px;border:1px solid rgba(255,255,255,.12);border-radius:20px;background:linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.018));box-shadow:0 18px 45px rgba(0,0,0,.18)}
.report-section h3{margin:0 0 14px;font-family:Sora,sans-serif;color:#ffffff;font-size:1.15rem;font-weight:800;letter-spacing:-.02em}
.report-section p{color:#e4e4ea;line-height:1.75;margin:.45rem 0}
.report-table{width:100%;border-collapse:collapse;overflow:hidden;border-radius:12px;border:1px solid rgba(255,255,255,.11)}
.report-table th{padding:12px 13px;text-align:left;color:#ffffff;background:rgba(169,156,255,.13);font-size:.78rem;letter-spacing:.04em}
.report-table td{padding:11px 13px;color:#ededf2;border-top:1px solid rgba(255,255,255,.09);vertical-align:top;font-size:.84rem}
.report-table tr:nth-child(even) td{background:rgba(255,255,255,.025)}
.check-detected{color:#4dff88;font-weight:850}.check-clear{color:#ff526b;font-weight:850}.check-low{color:#ffd34d;font-weight:850}.check-review{color:#ffd34d;font-weight:850}
.status-legend{margin-top:14px;padding:13px 15px;border:1px solid rgba(255,255,255,.10);border-radius:13px;background:rgba(255,255,255,.025);color:#e7e7ed;font-size:.78rem;line-height:1.65}
.status-legend-title{font-weight:800;color:#ffffff;margin-bottom:5px}.status-item{display:inline-block;margin-right:18px;margin-top:3px}.status-detected{color:#4dff88;font-weight:850}.status-review{color:#ffd34d;font-weight:850}.status-clear{color:#ff526b;font-weight:850}
.source-link{color:#a99cff!important;text-decoration:underline!important;text-decoration-thickness:1px!important;text-underline-offset:3px}
.conclusion-card{padding:18px 20px;border-left:3px solid #a99cff;border-radius:14px;background:linear-gradient(135deg,rgba(169,156,255,.14),rgba(169,156,255,.05));color:#f0f0f4;line-height:1.75}
.analysis-loader{height:5px;border-radius:999px;margin:10px 0 4px;overflow:hidden;background:rgba(255,255,255,.10);box-shadow:0 0 0 1px rgba(255,255,255,.06)}
.analysis-loader span{display:block;width:42%;height:100%;border-radius:999px;background:linear-gradient(90deg,#a99cff,#e7e1ff,#a99cff);box-shadow:0 0 18px rgba(169,156,255,.9);animation:satark-loader 1.25s ease-in-out infinite}
@keyframes satark-loader{0%{transform:translateX(-120%)}100%{transform:translateX(270%)}}

.footer{margin-top:4rem;padding-top:1.2rem;border-top:1px solid var(--line);text-align:center;color:#64646b;font-size:.74rem;line-height:1.6}
.stAlert{border-radius:13px!important}
[data-testid="stDownloadButton"] button{background:#ffffff!important;color:#17171a!important;border:1px solid #ffffff!important;font-weight:800!important;min-height:50px!important}
[data-testid="stDownloadButton"] button:hover{background:#f1efff!important;color:#17171a!important;border-color:#c8c0ff!important}
[data-testid="stDownloadButton"] button p,[data-testid="stDownloadButton"] button span{color:#17171a!important;font-weight:800!important}
[data-testid="stFileUploaderDropzoneInstructions"] div{color:#e9e9ef!important}

@media(max-width:768px){.block-container{padding:.7rem .65rem 3rem}.hero{padding:3rem .85rem;border-radius:20px}.hero h1{font-size:clamp(2.65rem,12vw,4.2rem);line-height:.94}.hero p{font-size:.96rem}.scanner{min-height:82px;padding:9px}div[data-testid="stButton"]>button{width:100%}.result{padding:17px}}
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------- Helpers --------------------------

def safe_text(value, default=""):  # cleans the text
    if value is None:
        return default
    return str(value).strip()




def clamp_score(value):
    try:
        return max(0, min(100, int(float(value))))  # limits score to 0–100
    except (TypeError, ValueError):
        st.warning(
            "⚠️ Threat score unavailable: Insufficient security indicators "
            "were found to make a reliable assessment. Please provide more "
            "complete information and try again."
        )
        return 50




def is_scam_claim(category, verdict, summary=""):
    """Detect a scam claim, trusting the model's explicit threat_category field first.

    The category field is a constrained enum the model was explicitly asked to
    fill in, so it is a far more reliable signal than re-deriving "is this a
    scam" from free-text prose. Regex parsing of the verdict/summary is now
    only a fallback for when the category is missing or ambiguous (e.g. still
    "Needs review"), rather than the primary signal.
    """
    category_text = safe_text(category).strip().lower()

    if category_text == "scam":
        return True

    if category_text and category_text not in {"needs review", ""}:
        # The model gave a specific, non-scam category (e.g. "Safe", "Phishing",
        # "Malware"). Trust it instead of re-scanning prose that might mention
        # the word "scam" in a hedged, comparative, or negated sentence.
        return False

    text = " ".join(
        safe_text(v) for v in (category, verdict, summary)
    ).lower()

    negative_patterns = (
        r"\bnot\s+(?:necessarily\s+)?(?:a\s+)?scam\b",
        r"\bno\s+(?:evidence\s+of\s+)?(?:a\s+)?scam\b",
        r"\b(?:does|do)\s+not\s+(?:appear|seem)\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\bunlikely\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\b(?:cannot|can't)\s+(?:confirm|verify)\s+(?:that\s+it\s+is\s+)?(?:a\s+)?scam\b",
        r"\bno\s+clear\s+indication\s+of\s+(?:a\s+)?scam\b",
    )

    if any(re.search(pattern, text) for pattern in negative_patterns):
        return False

    return bool(re.search(r"\bscam\b", text))




    def has_unverified_public_figure_claim(result):
    """Generic detector: flags any unverified real-person + endorsement/authority
    claim pattern, without hardcoding specific names, roles, or countries."""
    text = " ".join([
        safe_text(result.get("summary", "")),
        safe_text(result.get("verdict", "")),
        " ".join(result.get("key_indicators", [])),
    ]).lower()

    endorsement_terms = (
        r"brand ambassador", r"endorses?", r"endorsement",
        r"official partner", r"spokesperson", r"testimonial",
        r"partners? with", r"backed by", r"recommended by"
    )
    authority_or_fame_terms = (
        r"prime minister", r"president", r"minister", r"chief minister",
        r"governor", r"judge", r"official\b", r"government (?:body|agency|official)",
        r"celebrity", r"public figure", r"ceo\b", r"chairman", r"actor",
        r"cricketer", r"athlete", r"influencer"
    )

    endorsement_re = "|".join(endorsement_terms)
    authority_re = "|".join(authority_or_fame_terms)

    pattern = rf"\b({endorsement_re})\b.{{0,60}}\b({authority_re})\b|\b({authority_re})\b.{{0,60}}\b({endorsement_re})\b"
    return bool(re.search(pattern, text))




def normalize_result_consistency(result):
    """Keep scam/phishing category, risk score and displayed verdict consistent."""
    category = safe_text(
        result.get("threat_category", "Needs review"),
        "Needs review"
    )
    verdict = safe_text(
        result.get("verdict", "Manual review recommended."),
        "Manual review recommended."
    )
    summary = safe_text(result.get("summary", ""))

    category_lower = category.lower()
    combined_text = f"{category} {verdict} {summary}".lower()

    is_scam = is_scam_claim(category, verdict, summary)

    # Prefer the explicit category for phishing too; fall back to phrase
    # matching only when the category doesn't already say "Phishing".
    is_phishing = category_lower == "phishing" or bool(re.search(
        r"\b(phishing attempt|phishing attack|phishing link|phishing message|is phishing|appears to be phishing)\b",
        combined_text
    ))

    if is_scam or is_phishing:
        if is_scam:
            result["threat_category"] = "Scam"

        result["risk_score"] = max(
            70,
            clamp_score(result.get("risk_score", 50))
        )

        if is_scam and not re.search(r"\bscam\b", verdict.lower()):
            result["verdict"] = "This message is a scam and should not be trusted."

    else:
        result["risk_score"] = clamp_score(
            result.get("risk_score", 50)
        )

    if has_unverified_public_figure_claim(result) and result["risk_score"] < 40:
        result["risk_score"] = max(40, result["risk_score"])
        if result["threat_category"] in ("Safe", "Needs review"):
            result["threat_category"] = "Unverified Claim"

    return result

#-------------------------------------------------------------------------------------------------















def risk_label(score, category=""):
    score = clamp_score(score)
    if safe_text(category).lower() == "scam":
        return "SCAM", "critical"
    if score < 35:
        return "SAFE", "safe"
    if score < 70:
        return "CAUTION", "caution"
    return "CRITICAL THREAT", "critical"


def clean_json_text(text):
    text = safe_text(text)
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.I)
    start = text.find("{")
    end = text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text




THREAT_CHECKS = [
    "Scam Indicators",
    "Phishing Signs",
    "Deepfake Risk",
    "Fake Information",
    "Suspicious Links",
    "Impersonation",
    "Malware Indicators",
    "Social Engineering",
]




OFFICIAL_VERIFICATION_SOURCES = [
    {
        "source": "National Cyber Crime Reporting Portal (NCRP)",
        "purpose": "Report cybercrime and financial fraud, and check or report suspicious identifiers such as phone numbers, email IDs, URLs and social-media accounts.",
        "website": "https://www.cybercrime.gov.in/",
    },
    {
        "source": "Indian Cybercrime Coordination Centre (I4C)",
        "purpose": "Government of India initiative coordinating cybercrime prevention, analysis, reporting and response.",
        "website": "https://i4c.mha.gov.in/",
    },
    {
        "source": "CERT-In",
        "purpose": "India's national agency for cybersecurity incident response, alerts, advisories and security guidance.",
        "website": "https://www.cert-in.org.in/",
    },
    {
        "source": "Reserve Bank of India (RBI)",
        "purpose": "Official guidance on banking, digital payments, OTP/PIN safety and prevention of financial and payment fraud.",
        "website": "https://www.rbi.org.in/",
    },
    {
        "source": "National Payments Corporation of India (NPCI)",
        "purpose": "Official information and safety guidance for UPI and India's retail payment systems.",
        "website": "https://www.npci.org.in/",
    },
    {
        "source": "Securities and Exchange Board of India (SEBI)",
        "purpose": "Official investor-protection resources for identifying investment scams, unregistered entities and fraudulent schemes.",
        "website": "https://www.sebi.gov.in/",
    },
    {
        "source": "Sanchar Saathi — Department of Telecommunications",
        "purpose": "Report suspected fraudulent calls, SMS and WhatsApp communications and check mobile connections and handset information.",
        "website": "https://www.sancharsaathi.gov.in/",
    },
    {
        "source": "UIDAI",
        "purpose": "Official Aadhaar services and security guidance for protecting Aadhaar-related identity information.",
        "website": "https://uidai.gov.in/",
    },
    {
        "source": "IRDAI",
        "purpose": "Official insurance-sector guidance and consumer awareness regarding insurance fraud and cybersecurity risks.",
        "website": "https://irdai.gov.in/",
    },
    {
        "source": "National Consumer Helpline (NCH)",
        "purpose": "Government consumer grievance platform for consumer fraud and complaint-related support.",
        "website": "https://consumerhelpline.gov.in/",
    },
    {
        "source": "Employees' Provident Fund Organisation (EPFO)",
        "purpose": "Official guidance for protecting EPFO, UAN and pension-related information from impersonation and fraud.",
        "website": "https://www.epfindia.gov.in/",
    },
    {
        "source": "Income Tax Department",
        "purpose": "Official tax-related services and guidance for identifying fraudulent tax, PAN and income-tax communications.",
        "website": "https://www.incometax.gov.in/",
    },
    {
        "source": "Ministry of Corporate Affairs (MCA)",
        "purpose": "Official company and corporate information for cross-checking registered businesses and corporate identities.",
        "website": "https://www.mca.gov.in/",
    },
]



def normalize_check_value(value):
    if isinstance(value, bool):
        return "Detected" if value else "Not detected"
    if isinstance(value, (int, float)):
        if value >= 70:
            return "High"
        if value >= 35:
            return "Medium"
        return "Low"
    text = safe_text(value)
    if not text:
        return "Needs review"
    return text[:80]


def check_class(value):
    text = safe_text(value).lower()

    if any(x in text for x in (
        "not detected", "none", "no sign", "clear", "false", "absent"
    )):
        return "check-clear"

    if "low" in text:
        return "check-low"

    if any(x in text for x in (
        "detected", "present", "high", "yes", "true", "strong"
    )):
        return "check-detected"

    return "check-review"







#-------------------------------------------------------------------------------------------


def build_fallback_threat_analysis(result):
    category = safe_text(result.get("threat_category", "")).lower()
    indicators = " ".join(result.get("key_indicators", [])).lower()
    summary = safe_text(result.get("summary", "")).lower()
    verdict = safe_text(result.get("verdict", "")).lower()

    text = category + " " + indicators + " " + summary + " " + verdict

    def has(*terms):
        return any(term in text for term in terms)

    public_figure_claim = has(
        "public figure", "celebrity", "politician",
        "brand ambassador", "endorsement", "endorses",
        "celebrity endorsement", "public figure endorsement"
    )

    deepfake = has(
        "deepfake", "deep fake", "synthetic media",
        "ai-generated", "ai generated", "manipulated image",
        "face manipulation", "digitally manipulated"
    )

    fake_claim = has(
        "fake", "false", "fabricat", "misinformation",
        "misleading", "unverified", "unsupported claim",
        "false claim", "deceptive"
    )

    return {
        "Scam Indicators": "Detected" if has(
            "scam", "fraud", "prize", "fee"
        ) else "Needs review",

        "Phishing Signs": "Detected" if has(
            "phishing", "credential", "login", "password", "otp"
        ) else "Needs review",

        "Deepfake Risk": (
            "High" if deepfake
            else "Medium" if public_figure_claim
            else "Low"
        ),

        "Fake Information": "Detected" if fake_claim else "Needs review",

        "Suspicious Links": "Detected" if has(
            "suspicious link", "malicious link", "url", "domain"
        ) else "Needs review",

        "Impersonation": "Detected" if (
            public_figure_claim or has(
                "impersonation", "impersonat",
                "pretend", "fake authority"
            )
        ) else "Needs review",

        "Malware Indicators": "Detected" if has(
            "malware", "trojan", "ransomware", "apk", "virus"
        ) else "Not detected",

        "Social Engineering": "Detected" if has(
            "social engineering", "urgency", "pressure", "manipulation"
        ) else "Needs review",
    }




def build_final_conclusion(result):
    existing = safe_text(result.get("final_conclusion", ""))
    if existing:
        return existing
    label, _ = risk_label(result.get("risk_score", 50), result.get("threat_category", ""))
    summary = safe_text(result.get("summary", ""))
    verdict = safe_text(result.get("verdict", "Manual review recommended."))
    if summary:
        return f"SATARK assessed this item as {label.lower()} based on the evidence identified during analysis. {summary} {verdict} Verify the source independently before taking any high-impact action."
    return f"SATARK assessed this item as {label.lower()}. {verdict} Verify the source independently before taking any high-impact action."


def calibrate_confidence(data, result):
    """Report a SATARK confidence value that reflects real evidence strength.

    Unlike the previous implementation, this does NOT force the value into a
    fixed high band. The raw model confidence is kept as ``model_confidence``
    for auditability, and the user-facing ``confidence`` is the raw value
    adjusted only slightly by how complete/ambiguous the supporting evidence
    is. Weak or ambiguous evidence can and should produce a low confidence
    score — that is the whole point of showing it.
    """
    try:
        raw_conf = float(data.get("confidence", result.get("confidence", 70)))
    except (TypeError, ValueError):
        raw_conf = 70.0
    raw_conf = max(0.0, min(100.0, raw_conf))
    result["model_confidence"] = round(raw_conf, 2)

    checks = result.get("threat_analysis", {}) or {}
    review_count = sum(1 for value in checks.values() if check_class(value) == "check-review")
    evidence_count = len(result.get("key_indicators", []))

    # Ambiguous/unresolved checks should pull confidence down, not up.
    ambiguity_penalty = (review_count / max(1, len(THREAT_CHECKS))) * 20.0

    # Well-evidenced findings get a small, capped bonus — not a floor.
    evidence_bonus = min(5.0, evidence_count * 1.0)

    calibrated = raw_conf - ambiguity_penalty + evidence_bonus
    result["confidence"] = round(max(0.0, min(100.0, calibrated)), 2)
    return result


def normalize_result(data, raw="", model_used=""):
    if not isinstance(data, dict):
        data = {}
    indicators = data.get("key_indicators", data.get("indicators", []))
    recommendations = data.get("recommendations", data.get("safety_recommendations", []))
    if isinstance(indicators, str): indicators = [indicators]
    if isinstance(recommendations, str): recommendations = [recommendations]
    if not isinstance(indicators, list): indicators = []
    if not isinstance(recommendations, list): recommendations = []

    raw_checks = data.get("threat_analysis", {})
    if not isinstance(raw_checks, dict):
        raw_checks = {}
    threat_analysis = {
        check: normalize_check_value(raw_checks.get(check, ""))
        for check in THREAT_CHECKS
    }

    result = {
        "risk_score": clamp_score(data.get("risk_score", data.get("threat_score", 50))),
        "threat_category": safe_text(data.get("threat_category", data.get("category", "Needs review")), "Needs review"),
        "verdict": safe_text(data.get("verdict", data.get("final_verdict", "Manual review recommended.")), "Manual review recommended."),
        "summary": safe_text(data.get("summary", data.get("executive_summary", ""))),
        "key_indicators": [safe_text(x) for x in indicators if safe_text(x)][:8],
        "recommendations": [safe_text(x) for x in recommendations if safe_text(x)][:8],
        "confidence": clamp_score(data.get("confidence", 70)),
        "model_used": model_used or safe_text(data.get("model_used", "")),
        "scam_pattern": safe_text(data.get("scam_pattern", data.get("pattern", ""))),
        "threat_analysis": threat_analysis,
        "final_conclusion": safe_text(data.get("final_conclusion", data.get("conclusion", ""))),
        "verification_sources": OFFICIAL_VERIFICATION_SOURCES,
        "raw": raw,
    }
    result = normalize_result_consistency(result)
    if not result["scam_pattern"]:
        result["scam_pattern"] = result["threat_category"]
    fallback = build_fallback_threat_analysis(result)
    for check in THREAT_CHECKS:
        if result["threat_analysis"][check] == "Needs review":
            result["threat_analysis"][check] = fallback[check]
    result["final_conclusion"] = build_final_conclusion(result)
    result = calibrate_confidence(data, result)
    return result


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return "\n".join(self.parts)


def is_public_url(url):
    parsed = urlparse(safe_text(url))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = socket.getaddrinfo(host, None)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError, OSError):
        return True
    return True


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_public_url(newurl):
            raise ValueError("The URL redirects to a private or unsafe network address.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url):
    url = safe_text(url)
    if not is_public_url(url):
        raise ValueError("For safety, only public HTTP/HTTPS URLs can be fetched.")
    request = Request(url, headers={"User-Agent":"SATARK-Security-Analyzer/2.0", "Accept":"text/html,application/xhtml+xml,text/plain"})
    opener = build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        raw = response.read(1_500_000)
        final_url = response.geturl()
    if not is_public_url(final_url):
        raise ValueError("The final URL is not a public address and was blocked.")
    if "text" not in content_type and "html" not in content_type and "xml" not in content_type:
        return raw.decode("utf-8", errors="ignore")[:12000]
    parser = VisibleTextParser()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    text = parser.text() or raw.decode("utf-8", errors="ignore")
    return text[:30000]


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages[:30]:
        try:
            text = page.extract_text() or ""
            if text.strip(): pages.append(text)
        except Exception:
            pass
    text = "\n\n".join(pages).strip()
    if not text:
        raise ValueError("No readable text was found in this PDF. It may be scanned/image-only. Please use a screenshot/image of the relevant page for vision analysis.")
    return text[:50000]


def image_to_data_url(uploaded_file):
    """Convert one uploaded image to a compact JPEG data URL."""
    from io import BytesIO
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    image = Image.open(uploaded_file).convert("RGB")
    max_side = 1400
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    for quality in (82, 72, 62, 52):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        if len(encoded) <= 2_200_000 or quality == 52:
            return f"data:image/jpeg;base64,{encoded}"
    return f"data:image/jpeg;base64,{encoded}"


def images_to_data_urls(uploaded_files, max_images=5):
    """Convert multiple uploaded images while keeping the request manageable."""
    if not uploaded_files:
        return []
    urls = []
    for uploaded_file in list(uploaded_files)[:max_images]:
        urls.append(image_to_data_url(uploaded_file))
    return urls


def uploaded_fingerprint(uploaded_files):
    """Return a content fingerprint so a new scan cannot reuse stale image state."""
    if not uploaded_files:
        return ""
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        try:
            data = uploaded_file.getvalue()
        except Exception:
            data = b""
        digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
        digest.update(str(len(data)).encode("ascii"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def get_client(api_key):
    key = safe_text(api_key)
    return Groq(api_key=key) if key else None


# ---------------------- Model discovery ------------------------
TEXT_MODEL_PREFERENCES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
# Vision model fallback chain. Previously this was a single hardcoded model
# (qwen/qwen3.6-27b), which meant image/QR analysis broke entirely the moment
# that one model became unavailable or the API key lost access to it.
# analyze_with_groq now tries each of these in order and only reports failure
# once every candidate has been exhausted.
VISION_MODEL_PREFERENCES = [
    "qwen/qwen3.6-27b",
    "llama-3.2-90b-vision-preview",
    "llama-3.2-11b-vision-preview",
]


def discover_models(client):
    """Ask Groq which models this exact API key can access."""
    try:
        listing = client.models.list()
        items = getattr(listing, "data", listing)
        ids = set()
        for item in items or []:
            mid = getattr(item, "id", None)
            if mid:
                ids.add(str(mid))
            elif isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
        return ids
    except Exception:
        return set()


def choose_model(available, preferences):
    if not available:
        return preferences[0]
    for model in preferences:
        if model in available:
            return model
    return None


def model_status(client):
    available = discover_models(client)
    text_model = choose_model(available, TEXT_MODEL_PREFERENCES)
    vision_model = choose_model(available, VISION_MODEL_PREFERENCES)
    return available, text_model, vision_model


# ------------------------- AI analysis --------------------------
SYSTEM_PROMPT = """
You are SATARK, a careful digital-threat and content-authenticity analysis assistant.

Analyze the supplied content for scams, phishing, social engineering, malware indicators,
impersonation, suspicious links, credential theft, fraud, manipulation, fake offers,
payment fraud, account takeover, malicious QR codes, deepfakes, AI-generated content,
digitally manipulated media, fabricated information, misleading claims, fake quotes,
and deceptive endorsements.

Rules:
- Never claim certainty when evidence is weak.
- Explain findings in plain English for students, teachers and non-technical users.
- A high risk score means higher risk; a low score never guarantees safety.
- Distinguish evidence from inference.
- Confidence must reflect the strength and completeness of the available evidence. Use the
  full 0-100 range honestly: weak or ambiguous evidence should produce low confidence
  (below 50), and only strong, unambiguous, well-supported evidence should produce high
  confidence (above 85). Do not default to a high number.
- Do not invent URLs, organizations, sender details, or facts not visible in the input.

IMAGE AUTHENTICITY RULES:
- For images, inspect visible text, URLs, QR-related content, logos, layout and instructions.
- Analyze whether the image may be AI-generated, digitally manipulated, or a deepfake.
- Identify factual claims made by the image, including quotes, endorsements, affiliations,
  identities, products, services, events, and other real-world claims.
- Treat claims involving people, organizations, products, services, or events as claims
  that may require verification.
- Do not classify an image as Safe merely because it looks like a normal advertisement
  or professional graphic.
- If a claim appears fabricated, misleading, manipulated, or unsupported by the available
  evidence, reflect this in the risk assessment and explain why.
- If a person's identity, statement, image, or endorsement appears to be falsely
  represented or manipulated, assess the appropriate Impersonation, Deepfake Risk,
  and Fake Information fields.
- Separate cybersecurity safety from content authenticity: content can be malware-free
  while still being deceptive, manipulated, or misleading.
- Do not assume that realistic-looking content is authentic.

For URLs/web pages:
- Consider domain mismatch, suspicious redirects, credential requests, urgency,
  impersonation and other suspicious behavior.

Return ONLY valid JSON. No markdown. No code fences.

Required JSON schema:
{
  "risk_score": 0,
  "confidence": 0,
  "threat_category": "Safe / Phishing / Scam / Malware / Impersonation / Suspicious Link / Payment Fraud / Account Takeover / Other",
  "verdict": "one short sentence",
  "summary": "2-4 sentence plain-English explanation",
  "key_indicators": ["indicator 1", "indicator 2"],
  "recommendations": ["action 1", "action 2"],
  "scam_pattern": "one short pattern name",
  "threat_analysis": {
    "Scam Indicators": "Detected / Not detected / Low / Medium / High",
    "Phishing Signs": "Detected / Not detected / Low / Medium / High",
    "Deepfake Risk": "Detected / Not detected / Low / Medium / High",
    "Fake Information": "Detected / Not detected / Low / Medium / High",
    "Suspicious Links": "Detected / Not detected / Low / Medium / High",
    "Impersonation": "Detected / Not detected / Low / Medium / High",
    "Malware Indicators": "Detected / Not detected / Low / Medium / High",
    "Social Engineering": "Detected / Not detected / Low / Medium / High"
  },
  "final_conclusion": "2-4 sentence final conclusion explaining why the assessment was reached"
}
"""


def analyze_with_groq(client, content, mode, role, image_data_urls=None, available_models=None):
    """Run a SATARK analysis using an appropriate Groq model.

    Vision requests now try each model in VISION_MODEL_PREFERENCES in order
    instead of a single hardcoded model, so a deprecated/inaccessible vision
    model no longer breaks image/QR analysis entirely. Text scans keep the
    existing SATARK text-model fallback chain.

    The model-list endpoint is treated as a hint only: if the key can call the
    model successfully, SATARK proceeds even when model discovery is incomplete.
    """
    available_models = available_models or set()
    image_data_urls = list(image_data_urls or [])

    if len(image_data_urls) > 5:
        image_data_urls = image_data_urls[:5]

    user_prompt = f"""
Analysis type: {mode}
User profile: {role}

Analyze this content carefully:
{content}

Return a complete SATARK result using the required JSON schema. Do not omit
fields. For threat_analysis, use exactly one of: Detected, Needs review,
Not detected, Low, Medium, High.
"""

    def call(model, repair=False):
        common = {
            "model": model,
            "temperature": 0 if repair else 0.1,
            "max_tokens": 1400 if not repair else 1100,
            "response_format": {"type": "json_object"},
        }

        if image_data_urls:
            multimodal_content = [{"type": "text", "text": user_prompt}]
            for image_url in image_data_urls:
                multimodal_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": multimodal_content},
            ]
            common["reasoning_effort"] = "none"
        else:
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

        return client.chat.completions.create(**common)

    if image_data_urls:
        # Try every configured vision model in order rather than only the
        # first one. This is the fallback chain fix — previously the loop
        # below would `break` after a single failure for image requests.
        discovered_first = [m for m in VISION_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in VISION_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks
    else:
        discovered_first = [m for m in TEXT_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in TEXT_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks

    errors = []

    for model in candidates:
        try:
            response = call(model)
            raw = response.choices[0].message.content or ""

            # Groq normally returns a string. Be defensive if an SDK version
            # exposes structured content instead.
            if not isinstance(raw, str):
                if isinstance(raw, list):
                    raw = "".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in raw
                    )
                else:
                    raw = str(raw)

            raw = raw.strip()
            if not raw:
                raise RuntimeError("The AI model returned an empty response.")

            try:
                parsed = json.loads(clean_json_text(raw))
            except (json.JSONDecodeError, TypeError, ValueError) as parse_error:
                # JSON mode should make this uncommon. If a provider/SDK still
                # returns malformed content, perform one controlled repair call
                # with JSON mode enabled instead of falling through to another
                # unrelated model.
                repair_prompt = (
                    "Convert the following SATARK analysis into one valid JSON object. "
                    "Return ONLY JSON. Use exactly these top-level keys: "
                    "risk_score, confidence, threat_category, verdict, summary, "
                    "key_indicators, recommendations, scam_pattern, threat_analysis, "
                    "final_conclusion.\n\n"
                    + raw
                )
                original_prompt = user_prompt
                user_prompt = repair_prompt
                try:
                    repair_response = call(model, repair=True)
                finally:
                    user_prompt = original_prompt

                repaired = repair_response.choices[0].message.content or ""
                if not isinstance(repaired, str):
                    repaired = str(repaired)
                repaired = repaired.strip()
                if not repaired:
                    raise RuntimeError("The AI model returned an empty JSON repair response.")
                parsed = json.loads(clean_json_text(repaired))
                raw = repaired

            if not isinstance(parsed, dict):
                raise RuntimeError("The AI model returned JSON, but it was not a JSON object.")

            result = normalize_result(parsed, raw, model)
            result["scam_pattern"] = safe_text(
                parsed.get("scam_pattern", result.get("threat_category", "Needs review")),
                result.get("threat_category", "Needs review"),
            )
            return normalize_result_consistency(result)

        except Exception as exc:
            errors.append(f"{model}: {exc}")
            # Move on to the next candidate model instead of giving up
            # immediately — this applies to both text and vision requests now.
            continue

    detail = "\n".join(errors[-4:])
    kind = "image/QR" if image_data_urls else "text"

    if image_data_urls:
        raise RuntimeError(
            "SATARK could not complete the image/QR analysis with any configured "
            "vision model (tried: " + ", ".join(candidates) + "). Please verify "
            "that this Groq API key/project has access to at least one supported "
            "vision model and try again.\n" + detail
        )

    raise RuntimeError(
        f"SATARK could not complete the {kind} analysis with any configured Groq model.\n{detail}"
    )


# ---------------------- UI/result helpers ----------------------
def render_threat_analysis(result):
    rows = []
    for check in THREAT_CHECKS:
        value = safe_text(result.get("threat_analysis", {}).get(check, "Needs review"), "Needs review")
        cls = check_class(value)
        icon = "✖" if cls == "check-clear" else "✓" if cls == "check-detected" else "•"
        rows.append(f'<tr><td>{html.escape(check)}</td><td class="{cls}">{icon} {html.escape(value)}</td></tr>')
    table = (
        '<table class="report-table"><thead><tr><th>Security Check</th><th>Result</th></tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody></table>'
    )
    legend = (
        '<div class="status-legend">'
        '<div class="status-legend-title">How to read the results</div>'
        '<span class="status-item"><span class="status-detected">✓ Detected</span> — sufficient evidence that the indicator is present.</span>'
        '<span class="status-item"><span class="status-review">• Needs review</span> — evidence is ambiguous or insufficient; verify it manually.</span>'
        '<span class="status-item"><span class="status-clear">✖ Not detected</span> — no meaningful evidence of that indicator was found.</span>'
        '</div>'
    )
    st.markdown(f'<section class="report-section"><h3>🔎 Threat Analysis</h3>{table}{legend}</section>', unsafe_allow_html=True)


def render_verification_sources(result):
    rows=[]
    for item in result.get("verification_sources", OFFICIAL_VERIFICATION_SOURCES):
        source=html.escape(safe_text(item.get("source")))
        purpose=html.escape(safe_text(item.get("purpose")))
        website=safe_text(item.get("website"))
        safe_href=html.escape(website, quote=True)
        safe_label=html.escape(website)
        rows.append(f'<tr><td>{source}</td><td>{purpose}</td><td><a class="source-link" href="{safe_href}" target="_blank">{safe_label}</a></td></tr>')
    table=(
        '<table class="report-table"><thead><tr><th>Source</th><th>Purpose</th><th>Official Website</th></tr></thead>'
        '<tbody>'+''.join(rows)+'</tbody></table>'
    )
    st.markdown(f'<section class="report-section"><h3>📚 Official Verification Sources</h3>{table}</section>', unsafe_allow_html=True)


def confidence_css_class(confidence):
    """Color-code the confidence metric so low-confidence results are visually
    distinct instead of looking identical to high-confidence ones."""
    if confidence >= 85:
        return "safe"
    if confidence >= 50:
        return "caution"
    return "critical"


def render_result(result):
    score = clamp_score(result.get("risk_score",50))
    label, css = risk_label(score, result.get("threat_category", ""))
    indicators = result.get("key_indicators", [])
    recs = result.get("recommendations", [])
    confidence = float(result.get("confidence",70.0))
    conf_css = confidence_css_class(confidence)
    category = html.escape(result.get("threat_category","Needs review"))
    verdict = html.escape(result.get("verdict","Manual review recommended."))
    pattern = html.escape(result.get("scam_pattern", category))

    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown('<div class="result-head">🛡️ SATARK Security Report</div><div class="eyebrow">Evidence-first AI assessment • advisory, not a guarantee</div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Threat level</div><div class="metric-value {css}">{label}</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Risk score</div><div class="metric-value">{score}/100</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">Pattern</div><div class="metric-value" style="font-size:1rem">{pattern}</div></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="metric"><div class="metric-label">AI confidence</div><div class="metric-value {conf_css}">{confidence:.2f}%</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="bar"><div style="width:{score}%"></div></div>',unsafe_allow_html=True)
    if confidence < 50:
        st.info("ℹ️ Confidence is low — the evidence found was limited or ambiguous. Treat this result as a starting point, not a final answer, and verify manually.")
    st.markdown(f'<div class="verdict"><strong>Final verdict</strong><br>{verdict}</div>',unsafe_allow_html=True)

    if result.get("summary"):
        st.markdown("### 🔎 What SATARK found")
        st.markdown(f'<p style="color:#e4e4ea;line-height:1.8">{html.escape(result["summary"])}</p>', unsafe_allow_html=True)

    left,right = st.columns(2)
    with left:
        st.markdown('<div class="evidence"><strong>🧩 Evidence detected</strong>',unsafe_allow_html=True)
        if indicators:
            for item in indicators:
                st.markdown(f'<div class="evidence-item">⚠️ {html.escape(item)}</div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="evidence-item">No specific indicators were returned.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="evidence"><strong>🧭 What to do now</strong>',unsafe_allow_html=True)
        if recs:
            for item in recs:
                st.markdown(f'<div class="action-item"><span>✓</span><span>{html.escape(item)}</span></div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="action-item">Review the content manually before acting.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    render_threat_analysis(result)
    render_verification_sources(result)

    conclusion = html.escape(build_final_conclusion(result))
    st.markdown(f'<section class="report-section"><h3>💡 Final Conclusion</h3><div class="conclusion-card">{conclusion}</div></section>', unsafe_allow_html=True)


def pdf_escape(text):
    return html.escape(safe_text(text)).replace("\n", "<br/>")


def make_pdf_report(result, mode):
    """Create a polished, readable PDF version of the complete SATARK report."""
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm, title="SATARK Security Report"
    )
    styles = getSampleStyleSheet()
    dark = colors.HexColor("#111113")
    muted = colors.HexColor("#5f6270")
    violet = colors.HexColor("#6656d9")
    light_violet = colors.HexColor("#f0edff")
    line = colors.HexColor("#d9d9e2")
    green = colors.HexColor("#188a4b")
    red = colors.HexColor("#c92a4d")
    amber = colors.HexColor("#9a6500")

    title = ParagraphStyle("SATARKTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=dark, spaceAfter=5)
    subtitle = ParagraphStyle("SATARKSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=muted, spaceAfter=12)
    h2 = ParagraphStyle("SATARKH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=dark, spaceBefore=12, spaceAfter=8)
    body = ParagraphStyle("SATARKBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=dark, spaceAfter=6)
    small = ParagraphStyle("SATARKSmall", parent=body, fontSize=8, leading=11, textColor=muted)
    verdict_style = ParagraphStyle("SATARKVerdict", parent=body, fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=dark)
    centered = ParagraphStyle("SATARKCentered", parent=body, alignment=TA_CENTER, fontSize=8, textColor=muted)

    score=clamp_score(result.get("risk_score",50)); label,_=risk_label(score,result.get("threat_category",""))
    confidence_value = float(result.get('confidence',70.0))
    confidence_color = green if confidence_value >= 85 else (amber if confidence_value >= 50 else red)
    story=[]
    story.append(Paragraph("SATARK", title))
    story.append(Paragraph("Smart AI Threat Analysis & Risk Knowledge", subtitle))
    conf_cell_style = ParagraphStyle("SATARKConfCell", parent=body, textColor=confidence_color, fontName="Helvetica-Bold")
    meta=[[Paragraph("Scanner", body), Paragraph(pdf_escape(mode), body), Paragraph("Generated", body), Paragraph(datetime.now().strftime('%d %b %Y, %I:%M %p'), body)],
          [Paragraph("Threat level", body), Paragraph(pdf_escape(label), body), Paragraph("Risk score", body), Paragraph(f"{score}/100", body)],
          [Paragraph("Pattern", body), Paragraph(pdf_escape(result.get('scam_pattern','Needs review')), body), Paragraph("AI confidence", body), Paragraph(f"{confidence_value:.2f}%", conf_cell_style)]]
    meta_table=Table(meta,colWidths=[25*mm,60*mm,30*mm,60*mm],hAlign='LEFT')
    meta_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f7f6fb')),('BOX',(0,0),(-1,-1),0.7,line),('INNERGRID',(0,0),(-1,-1),0.4,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(meta_table)

    story.append(Paragraph("Final Verdict", h2))
    verdict_data=[[Paragraph(pdf_escape(result.get('verdict','Manual review recommended.')), verdict_style)]]
    vt=Table(verdict_data,colWidths=[175*mm])
    vt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_violet),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#b6adff')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(vt)

    story.append(Paragraph("What SATARK Found", h2))
    story.append(Paragraph(pdf_escape(result.get('summary','No summary was returned.')), body))

    story.append(Paragraph("Evidence Detected", h2))
    evidence=result.get('key_indicators',[]) or ['No specific indicators were returned.']
    story.append(Paragraph('<br/>'.join('• '+pdf_escape(x) for x in evidence), body))

    story.append(Paragraph("What To Do Now", h2))
    recs=result.get('recommendations',[]) or ['Review the content manually before acting.']
    story.append(Paragraph('<br/>'.join('• '+pdf_escape(x) for x in recs), body))

    story.append(Paragraph("Threat Analysis", h2))
    threat_data=[[Paragraph('<b>Security Check</b>',body),Paragraph('<b>Result</b>',body)]]
    for check in THREAT_CHECKS:
        value=safe_text(result.get('threat_analysis',{}).get(check,'Needs review'),'Needs review')
        threat_data.append([Paragraph(pdf_escape(check),body),Paragraph(pdf_escape(value),body)])
    tt=Table(threat_data,colWidths=[95*mm,80*mm],repeatRows=1)
    ts=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeaff')),('TEXTCOLOR',(0,0),(-1,0),dark),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
    for row_idx in range(1,len(threat_data)):
        value=safe_text(result.get('threat_analysis',{}).get(THREAT_CHECKS[row_idx-1],''))
        cls=check_class(value)
        text_color=green if cls=='check-detected' else red if cls=='check-clear' else amber
        ts.append(('TEXTCOLOR',(1,row_idx),(1,row_idx),text_color))
    tt.setStyle(TableStyle(ts))
    story.append(tt)
    legend_style = ParagraphStyle("SATARKLegend", parent=small, fontSize=8, leading=11, textColor=dark, spaceBefore=5)
    story.append(Paragraph(
        '<b>Status guide:</b> '
        '<font color="#188a4b"><b>Detected</b></font> — sufficient evidence that the indicator is present. '
        '<font color="#b07a00"><b>Needs review</b></font> — evidence is ambiguous or insufficient; verify it manually. '
        '<font color="#c92a4d"><b>Not detected</b></font> — no meaningful evidence of that indicator was found.',
        legend_style
    ))

    story.append(Paragraph("Official Verification Sources", h2))
    source_data=[[Paragraph('<b>Source</b>',body),Paragraph('<b>Purpose</b>',body),Paragraph('<b>Official Website</b>',body)]]
    for item in result.get('verification_sources',OFFICIAL_VERIFICATION_SOURCES):
        website=safe_text(item.get('website'))
        source_data.append([Paragraph(pdf_escape(item.get('source')),body),Paragraph(pdf_escape(item.get('purpose')),body),Paragraph(f'<link href="{html.escape(website,quote=True)}" color="#4d3dcc"><u>{pdf_escape(website)}</u></link>',body)])
    stbl=Table(source_data,colWidths=[42*mm,75*mm,58*mm],repeatRows=1)
    stbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeaff')),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(stbl)

    story.append(Paragraph("Final Conclusion", h2))
    conclusion=Paragraph(pdf_escape(build_final_conclusion(result)),body)
    ct=Table([[conclusion]],colWidths=[175*mm])
    ct.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_violet),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#b6adff')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(ct)
    story.append(Spacer(1,8))
    story.append(Paragraph("SATARK is an AI-assisted advisory tool. Verify high-impact security decisions independently.", centered))

    def add_page(canvas, doc):
        canvas.saveState()
        width,height=A4
        canvas.setFillColor(violet)
        canvas.rect(0,height-5*mm,width,5*mm,fill=1,stroke=0)
        canvas.setFillColor(muted)
        canvas.setFont('Helvetica',7.5)
        canvas.drawString(15*mm,8*mm,'SATARK • Smart AI Threat Analysis & Risk Knowledge')
        canvas.drawRightString(width-15*mm,8*mm,f'Page {doc.page}')
        canvas.restoreState()

    doc.build(story,onFirstPage=add_page,onLaterPages=add_page)
    return buffer.getvalue()


def add_history(result, mode):
    if "history" not in st.session_state: st.session_state.history=[]
    entry = {
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "mode": mode,
        "score": clamp_score(result.get("risk_score",50)),
        "category": result.get("threat_category","Needs review"),
        "verdict": result.get("verdict",""),
        "result": result,
    }
    st.session_state.history.insert(0,entry)
    st.session_state.history=st.session_state.history[:20]



# ----------------------- Session state -------------------------
def init_state():
    defaults={
        "mode":"Text","result":None,"history":[],
        "challenge_index":0,"challenge_score":0,"challenge_answered":False,
        "available_models":set(),"text_model":None,"vision_model":None,
        "last_input_fingerprint":"","analysis_request_id":"",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()

# --------------------------- Sidebar ---------------------------
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-logo">SATARK <span class="brand-dot">◦</span></div><div class="brand-tag">Smart AI Threat Analysis & Risk Knowledge</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">Navigate</div>',unsafe_allow_html=True)
    for page,label in [("Analyze","🔎 Check something"),("History","🕘 History"),("Challenge","🎯 Scam Challenge"),("Academy","🎓 SATARK Academy"),("Classroom","👨‍🏫 Classroom Mode")]:
        if st.button(label,key=f"nav_{page}",use_container_width=True): st.session_state.page=page; st.rerun()
    st.markdown('<div class="side-label">API configuration</div>',unsafe_allow_html=True)
    env_key=os.getenv("GROQ_API_KEY","")
    api_key=st.text_input("🔑 Groq API Key",value=env_key,type="password",placeholder="Paste your Groq API key",help="Kept in the Streamlit session; not intentionally written to disk by SATARK.")
    if api_key:
        if st.button("Check AI connection",key="check_ai",use_container_width=True):
            try:
                client=get_client(api_key); available=discover_models(client)
                st.session_state.available_models=available
                st.session_state.text_model=choose_model(available,TEXT_MODEL_PREFERENCES)
                st.session_state.vision_model=choose_model(available,VISION_MODEL_PREFERENCES)
                if st.session_state.text_model and st.session_state.vision_model: st.success("AI connected • text + vision available")
                elif st.session_state.text_model: st.warning("AI connected • text available, no vision model exposed to this key")
                else: st.error("API key is accepted but no supported SATARK text model was found.")
            except Exception as exc: st.error(f"Could not check Groq: {exc}")
    st.markdown('<div class="side-label">Personalization</div>',unsafe_allow_html=True)
    role=st.selectbox("👤 Who are you?",["Student","Teacher","Working professional","Parent / Guardian","Senior user","Security learner"],index=0)
    st.markdown('<div class="privacy"><strong>🔒 Privacy first</strong><br>SATARK keeps history only in this Streamlit session. Submitted content is not intentionally saved to disk by this app. Content is sent to Groq only when you analyze it. Avoid passwords, private keys and secrets.</div>',unsafe_allow_html=True)

# ---------------------------- Hero -----------------------------
st.markdown('<section class="hero"><div class="pill">AI SECURITY • EXPLAIN • LEARN • PROTECT</div><h1><span class="hero-primary">Think it’s a scam?</span><br><span class="hero-secondary">Let <span class="hero-brand">SATARK</span> check it.</span></h1><p><strong>Paste a message, inspect a link, upload a screenshot or analyze a PDF.</strong><br>SATARK explains the risk in simple language and shows the evidence behind its assessment.</p></section>',unsafe_allow_html=True)

# --------------------------- Pages -----------------------------
if st.session_state.page == "Analyze":
    st.markdown('<div class="section-title">What do you want to check?</div><div class="section-copy">Choose a scanner. Your original six SATARK modes remain available.</div>',unsafe_allow_html=True)
    scanner_rows=[[('Text','💬','Messages, posts and suspicious text'),('URL','🔗','Websites and suspicious links'),('Image','🖼️','Screenshots and images')],[('Email','📧','Phishing and fraudulent emails'),('PDF','📄','Text-based documents'),('QR','▣','QR screenshots and QR-related images')]]
    for row in scanner_rows:
        cols=st.columns(3)
        for col,(name,icon,copy) in zip(cols,row):
            with col:
                active=st.session_state.mode==name
                st.markdown(f'<div class="scanner {"active" if active else ""}"><div class="scanner-icon">{icon}</div><div class="scanner-title">{name}</div><div class="scanner-copy">{copy}</div></div>',unsafe_allow_html=True)
                if st.button(f"Use {name}",key=f"scanner_{name}",use_container_width=True):
                    st.session_state.mode=name; st.session_state.result=None; st.session_state.last_input_fingerprint=""; st.session_state.analysis_request_id=""; st.rerun()

    mode=st.session_state.mode
    st.markdown(f'<div class="section-title">🔎 Security Analysis</div><div class="section-copy">Selected: <strong>{mode}</strong></div>',unsafe_allow_html=True)
    uploaded=None; image_data_urls=[]
    if mode in {"Text","Email"}:
        placeholder="Paste the email body, sender message, subject, or suspicious email here..." if mode=="Email" else "Paste any message, post, SMS, social-media content or suspicious text here..."
        content=st.text_area("Enter content",height=230,placeholder=placeholder,key=f"text_input_{mode}")
    elif mode=="URL":
        content=st.text_input("Website URL",placeholder="https://example.com",key="url_input")
    elif mode=="PDF":
        uploaded=st.file_uploader("Upload PDF",type=["pdf"],help="Best results come from text-based PDFs.",key="pdf_input"); content=""
    else:
        uploaded=st.file_uploader(
            "Upload image",
            type=["png","jpg","jpeg","webp"],
            accept_multiple_files=True,
            help="Upload one or more screenshots, QR images, email screenshots or suspicious images. SATARK will analyze the selected images together.",
            key=f"image_input_{mode}"
        )
        content="Analyze all supplied images together. Inspect visible text, links, logos, QR-related content, suspicious instructions, impersonation and social-engineering signals, and cross-image evidence."
        if uploaded and len(uploaded) > 5:
            st.info("SATARK will analyze the first 5 selected images together to keep the request reliable.")

    current_input_fingerprint = uploaded_fingerprint(uploaded) if mode in {"Image", "QR"} else ""
    if mode in {"Image", "QR"} and current_input_fingerprint != st.session_state.get("last_input_fingerprint", ""):
        st.session_state.last_input_fingerprint = current_input_fingerprint
        if current_input_fingerprint:
            st.session_state.result = None

    st.markdown('<div class="analyze">',unsafe_allow_html=True)
    analyze_clicked=st.button("🔍 Analyze with SATARK",use_container_width=True,type="primary",key="analyze_button")
    st.markdown('</div>',unsafe_allow_html=True)

    if analyze_clicked:
        if not safe_text(api_key): st.error("🔑 Enter your Groq API key in the sidebar first."); st.stop()
        try:
            # Each analysis receives a fresh request id and fresh model discovery.
            # This prevents a previous image scan from contaminating the next one.
            st.session_state.analysis_request_id = hashlib.sha256(
                f"{datetime.now().isoformat()}|{mode}".encode("utf-8")
            ).hexdigest()[:16]
            st.session_state.result = None
            st.session_state.vision_model = None
            client=get_client(api_key)
            st.markdown('<div class="analysis-loader" aria-label="SATARK is analyzing"><span></span></div>', unsafe_allow_html=True)
            with st.spinner("SATARK is reading the content, evaluating threat patterns and building your report…"):
                available=discover_models(client)
                st.session_state.available_models=available
                # Do not block analysis based on the model-list endpoint. Some
                # Groq accounts can successfully call a model even when the
                # listing response is incomplete, and vice versa. The actual
                # completion request in analyze_with_groq is the source of truth.
                if mode in {"Text","Email"}:
                    if not safe_text(content): raise ValueError("Please enter some content to analyze.")
                    prepared=content[:50000]
                elif mode=="URL":
                    if not safe_text(content): raise ValueError("Please enter a URL.")
                    prepared=fetch_url_text(content)
                    if not prepared.strip(): raise ValueError("The URL returned no readable content.")
                elif mode=="PDF":
                    if uploaded is None: raise ValueError("Please upload a PDF.")
                    prepared=extract_pdf_text(uploaded)
                else:
                    if not uploaded: raise ValueError("Please upload at least one image.")
                    # Fresh conversion for every click prevents stale image/model state
                    # from a previous scan from leaking into the new request.
                    image_data_urls=images_to_data_urls(uploaded[:5], max_images=5)
                    if not image_data_urls: raise ValueError("The selected image(s) could not be read.")
                    prepared=f"{content}\nNumber of images in this investigation: {len(image_data_urls)}"
                prompt=f"User profile: {role}\nScanner mode: {mode}\n\n{prepared}"
                result=analyze_with_groq(client,prompt,mode,role,image_data_urls,available)
            st.session_state.result=result
            add_history(result,mode)
            st.session_state.page="Analyze"
            st.success("SATARK analysis complete.")
        except (ValueError,RuntimeError) as exc: st.error(f"⚠️ {exc}")
        except (HTTPError,URLError) as exc: st.error(f"⚠️ Could not fetch that URL safely: {exc}")
        except Exception as exc:
            st.error("⚠️ SATARK could not complete the analysis. Check your API key, internet connection, input and model access.")
            with st.expander("Technical details"): st.code(str(exc))

    if st.session_state.result:
        render_result(st.session_state.result)
        st.download_button("📄 Download PDF report",make_pdf_report(st.session_state.result,mode),file_name="SATARK_security_report.pdf",mime="application/pdf",use_container_width=True)

elif st.session_state.page == "History":
    st.markdown('<div class="section-title">🕘 Scan History</div><div class="section-copy">Session-only history. Original submitted content is not stored here; only analysis results and metadata are retained.</div>',unsafe_allow_html=True)
    if st.session_state.history:
        if st.button("Clear session history",key="clear_history"): st.session_state.history=[]; st.session_state.result=None; st.rerun()
        for i,entry in enumerate(st.session_state.history):
            score=entry["score"]; label,css=risk_label(score, entry.get("category", ""))
            with st.expander(f"{entry['mode']} • {entry['category']} • {score}/100 • {entry['time']}"):
                st.markdown(f'<span class="badge">{label}</span> <span class="badge">{html.escape(entry["category"])}</span>',unsafe_allow_html=True)
                st.write(entry["verdict"])
                c1,c2=st.columns(2)
                with c1:
                    if st.button("Open result",key=f"history_open_{i}"): st.session_state.result=entry["result"]; st.session_state.mode=entry["mode"]; st.session_state.page="Analyze"; st.rerun()
                with c2:
                    st.download_button("📄 Export PDF",make_pdf_report(entry["result"],entry["mode"]),file_name=f"SATARK_report_{i+1}.pdf",mime="application/pdf",key=f"history_dl_{i}")
    else: st.info("No scans yet. Analyze something suspicious and it will appear here for this session.")

elif st.session_state.page == "Challenge":
    st.markdown('<div class="section-title">🎯 Scam Challenge</div><div class="section-copy">Can you spot the scam before SATARK does? Great for students and classroom practice.</div>',unsafe_allow_html=True)
    questions=[
        {"q":"“URGENT: Your bank account will be blocked today. Verify immediately at this link.” What is the strongest warning sign?","options":["Urgency + account threat","A normal greeting","A long message","A company logo"],"answer":0,"why":"Attackers often create panic so you act before verifying. Urgency plus an account threat is a classic social-engineering pattern."},
        {"q":"A message says you won ₹50,000 and asks for a small ‘processing fee’. What should you suspect first?","options":["Reward/payment scam","Normal banking","Software update","School notice"],"answer":0,"why":"Unexpected prizes combined with a payment request are a common fraud pattern."},
        {"q":"A login link says it is from a familiar service, but the domain is misspelled. What is the key clue?","options":["Brand impersonation","Good website design","HTTPS alone","A short message"],"answer":0,"why":"Look at the actual domain, not just the logo or page appearance. Impersonation domains are frequently used for credential theft."},
        {"q":"Someone asks for your OTP because they claim to be ‘support’. What is the safest response?","options":["Share it quickly","Never share the OTP; verify independently","Send a screenshot","Ask for their password"],"answer":1,"why":"Legitimate services should not require you to disclose one-time passwords to an unsolicited caller or message sender."},
    ]
    q=questions[st.session_state.challenge_index%len(questions)]
    st.markdown('<div class="challenge-card">',unsafe_allow_html=True)
    st.markdown(f'<div class="badge">Question {(st.session_state.challenge_index%len(questions))+1} / {len(questions)}</div><div class="challenge-q" style="margin-top:14px">{q["q"]}</div>',unsafe_allow_html=True)
    cols=st.columns(2)
    for idx,opt in enumerate(q["options"]):
        with cols[idx%2]:
            if st.button(opt,key=f"challenge_opt_{st.session_state.challenge_index}_{idx}",use_container_width=True):
                if not st.session_state.challenge_answered:
                    if idx==q["answer"]: st.session_state.challenge_score+=1; st.success("Correct! 🎉")
                    else: st.warning("Not quite. Here's the pattern to remember.")
                    st.session_state.challenge_answered=True; st.rerun()
    if st.session_state.challenge_answered:
        st.markdown(f'<div class="challenge-answer"><strong>Why:</strong> {q["why"]}</div>',unsafe_allow_html=True)
        st.write(f"Score: **{st.session_state.challenge_score}/{(st.session_state.challenge_index%len(questions))+1}**")
        if st.button("Next challenge",key="next_challenge",type="primary"): st.session_state.challenge_index+=1; st.session_state.challenge_answered=False; st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    if st.button("Reset challenge score",key="reset_challenge"): st.session_state.challenge_index=0; st.session_state.challenge_score=0; st.session_state.challenge_answered=False; st.rerun()

elif st.session_state.page == "Academy":
    st.markdown('<div class="section-title">🎓 SATARK Academy</div><div class="section-copy">Learn the patterns behind the scams instead of relying on AI forever.</div>',unsafe_allow_html=True)
    lessons=[
        ("🎣","Phishing","Fake messages and pages designed to steal credentials or information."),
        ("⏰","Urgency manipulation","Pressure tactics that make you act before you verify."),
        ("👤","Impersonation","Attackers pretending to be banks, schools, companies, friends or officials."),
        ("🔗","Suspicious links","Look-alike domains, strange paths, redirects and unexpected login pages."),
        ("💳","Payment fraud","Fake fees, refunds, prizes, QR payments and requests for money."),
        ("🔐","Account takeover","Attempts to obtain passwords, OTPs, recovery codes or session access."),
    ]
    cols=st.columns(3)
    for i,(icon,title,copy) in enumerate(lessons):
        with cols[i%3]: st.markdown(f'<div class="feature-card"><div class="feature-icon">{icon}</div><div class="feature-title">{title}</div><div class="feature-copy">{copy}</div></div>',unsafe_allow_html=True)
    st.markdown("### A simple rule to remember")
    st.info("STOP → VERIFY → ACT. If a message creates pressure, asks for secrets, or requests money, pause and verify through an independent official channel.")

elif st.session_state.page == "Classroom":
    st.markdown('<div class="section-title">👨‍🏫 Classroom Mode</div><div class="section-copy">A simple teacher-facing view for using SATARK as a cyber-safety learning tool.</div>',unsafe_allow_html=True)
    history=st.session_state.history
    total=len(history); avg=round(sum(x["score"] for x in history)/total) if total else 0; high=sum(1 for x in history if x["score"]>=70)
    a,b,c=st.columns(3)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Scans this session</div><div class="metric-value">{total}</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Average risk</div><div class="metric-value">{avg}/100</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">High-risk findings</div><div class="metric-value critical">{high}</div></div>',unsafe_allow_html=True)
    st.markdown("### Suggested classroom flow")
    st.markdown("**1.** Give students a suspicious message.  **2.** Ask them to identify warning signs.  **3.** Run it through SATARK.  **4.** Compare the evidence.  **5.** Use Scam Challenge to reinforce the lesson.")
    st.markdown("### Common patterns in this session")
    counts={}
    for item in history:
        key=item["category"]; counts[key]=counts.get(key,0)+1
    if counts:
        for k,v in sorted(counts.items(),key=lambda x:x[1],reverse=True): st.write(f"• **{k}** — {v} scan(s)")
    else: st.info("Run a few example scans to populate classroom statistics.")

# ---------------------------- Footer ---------------------------
st.markdown('<div class="footer">SATARK • Smart AI Threat Analysis & Risk Knowledge<br>AI analysis is advisory. Always verify high-impact security decisions independently.<br>Session history is temporary and does not intentionally preserve submitted source content.</div>',unsafe_allow_html=True)

'''



















# 🧰 CORE PYTHON / SYSTEM
import os
import re
import json
import base64
import hashlib
import socket
import ipaddress
import html
from datetime import datetime

# 🌐 WEB / URL HANDLING
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

# 🤖 AI / WEB APP
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# 📄 FILE & IMAGE PROCESSING
from pypdf import PdfReader
from PIL import Image

# 📑 PDF GENERATION
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether
)

# ============================================================
# SATARK — Smart AI Threat Analysis & Risk Knowledge
# FINAL single-file Streamlit application
#
# Keeps the original SATARK analysis flow, while adding:
# - automatic Groq model discovery
# - resilient vision-model selection (now with fallback chain)
# - improved result presentation
# - session history + report export
# - Scam Challenge
# - SATARK Academy
# - Classroom Mode
# - evidence / confidence / actions
# - privacy-first session storage
#
# CHANGES IN THIS VERSION:
# 1. calibrate_confidence() no longer force-floors confidence to 95-99.99%.
#    It now reports a value that actually reflects model + evidence strength,
#    across the full 0-100 range.
# 2. render_result() color-codes the confidence metric (red/amber/green)
#    so low-confidence results are visually distinct.
# 3. VISION_MODEL_PREFERENCES is now a real fallback chain instead of a
#    single hardcoded model; analyze_with_groq tries each in order instead
#    of giving up after the first failure.
# 4. is_scam_claim / normalize_result_consistency now trust the model's
#    explicit threat_category field first, and only fall back to regex
#    parsing of prose when the category is missing/ambiguous. This makes
#    scam/phishing detection less fragile to wording changes.
# 5. SYSTEM_PROMPT's confidence instruction is now explicit about using the
#    full 0-100 range honestly instead of defaulting high.
# 6. NEW: Video scanner mode. Videos are analyzed by extracting a handful of
#    representative frames (via OpenCV) and, when ffmpeg/moviepy is available,
#    transcribing the audio track (via Groq Whisper) so speech-based scam
#    signals aren't missed. Frames + transcript are fed into the same
#    analyze_with_groq pipeline used for images/text.
# ============================================================

st.set_page_config(
    page_title="SATARK — AI Threat Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS ----------------------------

# 🧰 CORE PYTHON / SYSTEM
import os
import re
import json
import base64
import hashlib
import socket
import ipaddress
import html
from datetime import datetime

# 🌐 WEB / URL HANDLING
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

# 🤖 AI / WEB APP
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# 📄 FILE & IMAGE PROCESSING
from pypdf import PdfReader
from PIL import Image

# 📑 PDF GENERATION
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, KeepTogether
)

# ============================================================
# SATARK — Smart AI Threat Analysis & Risk Knowledge
# FINAL single-file Streamlit application
#
# Keeps the original SATARK analysis flow, while adding:
# - automatic Groq model discovery
# - resilient vision-model selection (now with fallback chain)
# - improved result presentation
# - session history + report export
# - Scam Challenge
# - SATARK Academy
# - Classroom Mode
# - evidence / confidence / actions
# - privacy-first session storage
#
# CHANGES IN THIS VERSION:
# 1. calibrate_confidence() no longer force-floors confidence to 95-99.99%.
#    It now reports a value that actually reflects model + evidence strength,
#    across the full 0-100 range.
# 2. render_result() color-codes the confidence metric (red/amber/green)
#    so low-confidence results are visually distinct.
# 3. VISION_MODEL_PREFERENCES is now a real fallback chain instead of a
#    single hardcoded model; analyze_with_groq tries each in order instead
#    of giving up after the first failure.
# 4. is_scam_claim / normalize_result_consistency now trust the model's
#    explicit threat_category field first, and only fall back to regex
#    parsing of prose when the category is missing/ambiguous. This makes
#    scam/phishing detection less fragile to wording changes.
# 5. SYSTEM_PROMPT's confidence instruction is now explicit about using the
#    full 0-100 range honestly instead of defaulting high.
# 6. NEW: Video scanner mode. Videos are analyzed by extracting a handful of
#    representative frames (via OpenCV) and, when ffmpeg/moviepy is available,
#    transcribing the audio track (via Groq Whisper) so speech-based scam
#    signals aren't missed. Frames + transcript are fed into the same
#    analyze_with_groq pipeline used for images/text.
# ============================================================

st.set_page_config(
    page_title="SATARK — AI Threat Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- CSS ----------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&display=swap');

:root {
    --bg:#050505;
    --surface:#111113;
    --surface2:#18181b;
    --line:rgba(255,255,255,.10);
    --line2:rgba(255,255,255,.16);
    --text:#f7f7f9;
    --soft:#e1e1e6;
    --muted:#b4b4bd;
    --violet:#a99cff;
    --violet2:rgba(155,140,255,.13);
    --safe:#30d158;
    --warn:#ffb340;
    --danger:#ff453a;
}

*{box-sizing:border-box}

html,body,[class*="css"]{
    font-family:"Manrope",sans-serif;
}

/* SCANNER CARD — WHOLE-CARD CLICKABLE OVERLAY */

.scanner-wrap {
    position: relative !important;
}

.scanner-wrap div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 10 !important;
}

.scanner-wrap div[data-testid="stButton"] > button {
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    opacity: 0 !important;
    cursor: pointer !important;
    border: 0 !important;
    background: transparent !important;
}

body{
    background:var(--bg);
    color:var(--text);
}

h1,h2,h3,h4,h5,h6{
    color:#f5f5f7!important;
}

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li{
    color:#e2e2e8!important;
}

div[data-testid="stCaptionContainer"]{
    color:#c8c8d1!important;
}

a{
    color:#a99cff;
}

.stApp{
    min-height:100vh;
    background:
        radial-gradient(circle at 50% -10%,rgba(155,140,255,.09),transparent 30rem),
        radial-gradient(circle at 90% 35%,rgba(255,255,255,.035),transparent 25rem),
        linear-gradient(180deg,#050505 0%,#080809 55%,#050505 100%);
}

.block-container{
    max-width:1480px;
    padding:1.2rem clamp(1rem,3vw,3rem) 4rem;
}

[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#0a0a0b,#060607);
    border-right:1px solid rgba(255,255,255,.08);
}

[data-testid="stSidebar"]>div:first-child{
    padding-top:1.1rem;
}

[data-testid="stSidebar"] label{
    color:#f5f5f7!important;
    font-weight:650!important;
}

[data-testid="stSidebar"] input::placeholder{
    color:#8f8f98!important;
}

.brand{
    padding:8px 4px 24px;
}

.brand-logo{
    font-family:Sora;
    font-weight:900;
    font-size:1.55rem;
    letter-spacing:-.06em;
    color:#ffffff;
    text-shadow:0 0 22px rgba(169,156,255,.22);
}

.brand-dot{
    color:#c9c1ff;
    text-shadow:0 0 10px rgba(169,156,255,.65);
}

.brand-tag{
    margin-top:5px;
    color:var(--muted);
    font-size:.78rem;
    line-height:1.45;
}

.side-label{
    margin:19px 0 8px;
    color:#8f8f98;
    font-size:.67rem;
    font-weight:800;
    letter-spacing:.16em;
    text-transform:uppercase;
}

.privacy{
    padding:14px;
    border:1px solid var(--line);
    border-radius:15px;
    background:rgba(255,255,255,.035);
    color:var(--soft);
    font-size:.78rem;
    line-height:1.55;
}

/* HERO */

.hero{
    position:relative;
    overflow:hidden;
    padding:clamp(2rem,4vw,3.2rem) 1.5rem;
    margin-bottom:1.6rem;
    border:1px solid var(--line);
    border-radius:22px;
    text-align:center;
    background:
        radial-gradient(circle at 50% 0%,rgba(255,255,255,.085),transparent 38%),
        radial-gradient(circle at 82% 70%,rgba(155,140,255,.07),transparent 28%),
        linear-gradient(145deg,rgba(25,25,28,.82),rgba(9,9,10,.92));
    box-shadow:
        0 20px 60px rgba(0,0,0,.4),
        inset 0 1px 0 rgba(255,255,255,.06);
    backdrop-filter:blur(24px);
    -webkit-backdrop-filter:blur(24px);
}

.hero:before{
    content:"";
    position:absolute;
    width:280px;
    height:280px;
    left:50%;
    top:-240px;
    transform:translateX(-50%);
    border-radius:50%;
    background:rgba(255,255,255,.08);
    filter:blur(70px);
    pointer-events:none;
}

.hero:after{
    content:"";
    position:absolute;
    left:15%;
    right:15%;
    bottom:0;
    height:1px;
    background:linear-gradient(
        90deg,
        transparent,
        rgba(214,179,106,.65),
        transparent
    );
}

.pill{
    position:relative;
    display:inline-flex;
    align-items:center;
    min-height:28px;
    padding:5px 12px;
    border:1px solid rgba(214,179,106,.36);
    border-radius:999px;
    color:#e8d5a7;
    background:rgba(214,179,106,.07);
    font-size:.62rem;
    font-weight:800;
    letter-spacing:.13em;
}

.hero h1{
    position:relative;
    margin:14px 0 8px;
    font-family:Sora,"Manrope",sans-serif;
    font-size:clamp(1.6rem,3.2vw,2.35rem);
    line-height:1.08;
    letter-spacing:-.03em;
    color:var(--text);
}

.hero h1 .hero-primary{
    display:inline-block;
    font-weight:500;
    color:#f3f3f6;
    font-size:.9em;
}

.hero h1 .hero-secondary{
    display:inline-block;
    font-weight:500;
    color:#e6e6eb;
    font-size:.9em;
}

.hero h1 .hero-brand{
    font-weight:800;
    color:#ffffff;
    background:linear-gradient(
        105deg,
        #ffffff 8%,
        #e2defe 55%,
        #a99cff 100%
    );
    -webkit-background-clip:text;
    background-clip:text;
    color:transparent;
}

.hero p{
    position:relative;
    max-width:640px;
    margin:0 auto;
    color:#bfc0c8;
    font-size:clamp(.82rem,1.3vw,.92rem);
    line-height:1.55;
}

.hero p strong{
    color:#f0f0f3;
    font-weight:700;
}

.hero-actions{
    margin-top:16px;
}

/* SECTION */

.section-title{
    margin:1.4rem 0 .35rem;
    font-family:Sora;
    font-size:1.3rem;
    font-weight:750;
    color:#f2f2f5;
}

.section-copy{
    margin:0 0 .8rem;
    color:#d0d0d8;
    font-size:.88rem;
}

.section-copy strong{
    color:#f0f0f3;
    font-weight:650;
}

/* BUTTONS */

div[data-testid="stButton"]>button{
    min-height:46px;
    border-radius:13px;
    border:1px solid var(--line);
    background:rgba(255,255,255,.045);
    color:var(--text);
    font-weight:700;
    transition:.2s ease;
}

div[data-testid="stButton"]>button:hover{
    transform:translateY(-2px);
    border-color:rgba(155,140,255,.48);
    background:rgba(155,140,255,.08);
    box-shadow:0 15px 35px rgba(0,0,0,.28);
}

div[data-testid="stButton"]>button[kind="primary"]{
    border-color:rgba(155,140,255,.55);
    background:linear-gradient(135deg,#28233f,#15151a);
}

/* SCANNER / TOOLS */

.scanner{
    min-height:96px;
    padding:12px 10px;
    border:1px solid var(--line);
    border-radius:14px;
    background:rgba(255,255,255,.035);
    text-align:center;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    transition:.2s ease;
    cursor:pointer;
}

.scanner:hover{
    transform:translateY(-3px);
    border-color:rgba(169,156,255,.48);
    background:rgba(155,140,255,.07);
    box-shadow:0 14px 35px rgba(0,0,0,.25);
}

.scanner-icon{
    font-size:1.45rem;
    line-height:1;
    margin-bottom:6px;
}

.scanner-title{
    margin-top:2px;
    font-size:.88rem;
    font-weight:800;
    color:#f4f4f7;
}

.scanner-copy{
    margin-top:4px;
    color:#c9c9d2;
    font-size:.72rem;
    line-height:1.35;
    max-width:135px;
}

.active{
    border-color:rgba(169,156,255,.72);
    background:rgba(155,140,255,.11);
    box-shadow:
        0 0 0 1px rgba(155,140,255,.12),
        0 12px 30px rgba(0,0,0,.22);
}

/* SCANNER CARD — WHOLE-CARD CLICKABLE OVERLAY
   Wraps a .scanner card + an invisible, fully-stretched
   st.button so clicking anywhere on the card triggers it,
   instead of needing a separate visible button underneath. */

.scanner-wrap { position: relative; }

.scanner-wrap div[data-testid="stButton"] {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
}

.scanner-wrap div[data-testid="stButton"] > button {
    width: 100%; height: 100%;
    opacity: 0;
    cursor: pointer;
}

/* INPUTS */

textarea,
[data-testid="stTextInput"] input,
[data-baseweb="select"]>div{
    font-size:16px!important;
    color:var(--text)!important;
    background:#141416!important;
    border:1px solid var(--line)!important;
    border-radius:13px!important;
}

textarea::placeholder,
[data-testid="stTextInput"] input::placeholder{
    color:#9a9aa4!important;
    opacity:1!important;
}

textarea:focus,
[data-testid="stTextInput"] input:focus{
    border-color:rgba(155,140,255,.7)!important;
    box-shadow:0 0 0 3px rgba(155,140,255,.12)!important;
}

[data-baseweb="select"] input{
    caret-color:transparent!important;
}

[data-baseweb="popover"],
[data-baseweb="menu"]{
    background:#19191c!important;
    border:1px solid var(--line)!important;
    border-radius:13px!important;
    color:#fff!important;
}

[data-baseweb="menu"] [role="option"]{
    background:transparent!important;
    color:#fff!important;
    min-height:44px!important;
}

.stFileUploader>div{
    border-radius:14px!important;
}

[data-testid="stFileUploaderDropzone"]{
    min-height:125px!important;
    border:1.5px dashed rgba(155,140,255,.42)!important;
    border-radius:15px!important;
    background:rgba(155,140,255,.035)!important;
}

[data-testid="stFileUploader"] *{
    color:#e1e1e6!important;
}

/* ANALYZE BUTTON */

.analyze{
    margin-top:10px;
}

.analyze div[data-testid="stButton"]>button{
    min-height:53px;
    border-radius:999px;
    font-size:1rem;
    background:linear-gradient(135deg,#2a2443,#151519);
}

/* RESULT */

.result{
    padding:24px;
    margin-top:20px;
    border:1px solid var(--line);
    border-radius:22px;
    background:linear-gradient(
        145deg,
        rgba(255,255,255,.055),
        rgba(255,255,255,.018)
    );
    box-shadow:0 25px 65px rgba(0,0,0,.25);
}

.result-head{
    font-family:Sora;
    font-size:1.3rem;
    font-weight:800;
    color:#f5f5f7;
}

.eyebrow{
    color:#c9c9d2;
    font-size:.75rem;
    margin-top:4px;
}

.metric{
    min-height:96px;
    padding:13px;
    border:1px solid var(--line);
    border-radius:13px;
    background:rgba(255,255,255,.03);
}

.metric-label{
    color:#d0d0d8;
    font-size:.68rem;
    font-weight:800;
    letter-spacing:.1em;
    text-transform:uppercase;
}

.metric-value{
    margin-top:7px;
    font-family:Sora;
    font-size:1.4rem;
    font-weight:800;
    color:#f5f5f7;
}

.safe{
    color:var(--safe);
}

.caution{
    color:var(--warn);
}

.critical{
    color:var(--danger);
}

.bar{
    height:10px;
    margin:12px 0;
    border-radius:999px;
    background:#252528;
    overflow:hidden;
}

.bar>div{
    height:100%;
    background:linear-gradient(
        90deg,
        var(--safe),
        var(--warn),
        var(--danger)
    );
    border-radius:inherit;
}

.verdict{
    padding:17px;
    margin-top:14px;
    border-left:3px solid var(--violet);
    border-radius:12px;
    background:var(--violet2);
    line-height:1.65;
    color:#e1e1e6;
}

.verdict strong{
    color:#ffffff;
}

.evidence,
.action,
.info-card,
.challenge-card{
    height:100%;
    padding:17px;
    border:1px solid var(--line);
    border-radius:16px;
    background:rgba(255,255,255,.03);
}

.evidence>strong,
.action>strong{
    color:#f4f4f7;
}

.evidence-item{
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,.08);
    color:#e0e0e5;
}

.evidence-item:last-child{
    border-bottom:0;
}

.action-item{
    display:flex;
    gap:10px;
    padding:9px 0;
    color:#e0e0e5;
}

.badge{
    display:inline-block;
    padding:5px 9px;
    border-radius:999px;
    background:rgba(155,140,255,.1);
    border:1px solid rgba(155,140,255,.2);
    color:#cfc9ff;
    font-size:.7rem;
    font-weight:800;
}

.confidence{
    font-size:.82rem;
    color:#bdbdc5;
}


/* COMPACT + SYMMETRIC CARDS */
[data-testid="stHorizontalBlock"]{
    align-items:stretch!important;
    gap:0.7rem!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]{
    display:flex!important;
    flex-direction:column!important;
    align-items:stretch!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div{
    display:flex!important;
    flex-direction:column!important;
    flex:1 1 auto!important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"] div[data-testid="stMarkdownContainer"]{
    display:flex!important;
    flex-direction:column!important;
    flex:1 1 auto!important;
}
.scanner,
.feature-card,
.metric,
.evidence,
.action,
.info-card,
.challenge-card{
    width:100%!important;
    height:100%!important;
    flex:1 1 auto!important;
    margin:0!important;
    justify-content:center!important;
}
.scanner-title{
    line-height:1.2;
}
.scanner-copy{
    line-height:1.25;
}

/* FEATURE CARDS */

.feature-card{
    padding:15px;
    border:1px solid var(--line);
    border-radius:14px;
    background:rgba(255,255,255,.03);
    height:100%;
}

.feature-icon{
    font-size:1.4rem;
}

.feature-title{
    margin-top:8px;
    font-weight:800;
    color:#f1f1f4;
}

.feature-copy{
    margin-top:5px;
    color:#d0d0d8;
    font-size:.78rem;
    line-height:1.5;
}

/* CHALLENGE */

.challenge-q{
    font-family:Sora;
    font-size:1.15rem;
    font-weight:750;
    line-height:1.45;
    color:#f1f1f4;
}

.challenge-answer{
    padding:13px;
    border-radius:12px;
    background:rgba(255,255,255,.04);
    border:1px solid var(--line);
    color:#f0f0f3;
    line-height:1.55;
}

/* REPORT */

.report-section{
    margin-top:24px;
    padding:22px;
    border:1px solid rgba(255,255,255,.12);
    border-radius:20px;
    background:linear-gradient(
        145deg,
        rgba(255,255,255,.055),
        rgba(255,255,255,.018)
    );
    box-shadow:0 18px 45px rgba(0,0,0,.18);
}

.report-section h3{
    margin:0 0 14px;
    font-family:Sora,sans-serif;
    color:#ffffff;
    font-size:1.15rem;
    font-weight:800;
    letter-spacing:-.02em;
}

.report-section p{
    color:#e4e4ea;
    line-height:1.75;
    margin:.45rem 0;
}

.report-table{
    width:100%;
    border-collapse:collapse;
    overflow:hidden;
    border-radius:12px;
    border:1px solid rgba(255,255,255,.11);
}

.report-table th{
    padding:12px 13px;
    text-align:left;
    color:#ffffff;
    background:rgba(169,156,255,.13);
    font-size:.78rem;
    letter-spacing:.04em;
}

.report-table td{
    padding:11px 13px;
    color:#ededf2;
    border-top:1px solid rgba(255,255,255,.09);
    vertical-align:top;
    font-size:.84rem;
}

.report-table tr:nth-child(even) td{
    background:rgba(255,255,255,.025);
}

.check-detected{
    color:#4dff88;
    font-weight:850;
}

.check-clear{
    color:#ff526b;
    font-weight:850;
}

.check-low{
    color:#ffd34d;
    font-weight:850;
}

.check-review{
    color:#ffd34d;
    font-weight:850;
}

.status-legend{
    margin-top:14px;
    padding:13px 15px;
    border:1px solid rgba(255,255,255,.10);
    border-radius:13px;
    background:rgba(255,255,255,.025);
    color:#e7e7ed;
    font-size:.78rem;
    line-height:1.65;
}

.status-legend-title{
    font-weight:800;
    color:#ffffff;
    margin-bottom:5px;
}

.status-item{
    display:inline-block;
    margin-right:18px;
    margin-top:3px;
}

.status-detected{
    color:#4dff88;
    font-weight:850;
}

.status-review{
    color:#ffd34d;
    font-weight:850;
}

.status-clear{
    color:#ff526b;
    font-weight:850;
}

.source-link{
    color:#a99cff!important;
    text-decoration:underline!important;
    text-decoration-thickness:1px!important;
    text-underline-offset:3px;
}

.conclusion-card{
    padding:18px 20px;
    border-left:3px solid #a99cff;
    border-radius:14px;
    background:linear-gradient(
        135deg,
        rgba(169,156,255,.14),
        rgba(169,156,255,.05)
    );
    color:#f0f0f4;
    line-height:1.75;
}

/* LOADER */

.analysis-loader{
    height:5px;
    border-radius:999px;
    margin:10px 0 4px;
    overflow:hidden;
    background:rgba(255,255,255,.10);
    box-shadow:0 0 0 1px rgba(255,255,255,.06);
}

.analysis-loader span{
    display:block;
    width:42%;
    height:100%;
    border-radius:999px;
    background:linear-gradient(
        90deg,
        #a99cff,
        #e7e1ff,
        #a99cff
    );
    box-shadow:0 0 18px rgba(169,156,255,.9);
    animation:satark-loader 1.25s ease-in-out infinite;
}

@keyframes satark-loader{
    0%{
        transform:translateX(-120%);
    }
    100%{
        transform:translateX(270%);
    }
}

/* FOOTER */

.footer{
    margin-top:4rem;
    padding-top:1.2rem;
    border-top:1px solid var(--line);
    text-align:center;
    color:#64646b;
    font-size:.74rem;
    line-height:1.6;
}

.stAlert{
    border-radius:13px!important;
}

[data-testid="stDownloadButton"] button{
    background:#ffffff!important;
    color:#17171a!important;
    border:1px solid #ffffff!important;
    font-weight:800!important;
    min-height:50px!important;
}

[data-testid="stDownloadButton"] button:hover{
    background:#f1efff!important;
    color:#17171a!important;
    border-color:#c8c0ff!important;
}

[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button span{
    color:#17171a!important;
    font-weight:800!important;
}

[data-testid="stFileUploaderDropzoneInstructions"] div{
    color:#e9e9ef!important;
}

/* MOBILE */

@media(max-width:768px){

    .block-container{
        padding:.7rem .65rem 3rem;
    }

    .hero{
        padding:2.2rem .85rem;
        border-radius:18px;
    }

    .hero h1{
        font-size:clamp(1.5rem,7vw,2rem);
        line-height:1.1;
    }

    .hero p{
        font-size:.8rem;
    }

    .scanner{
        min-height:88px;
        padding:10px 8px;
    }

    .scanner-icon{
        font-size:1.3rem;
    }

    .scanner-title{
        font-size:.9rem;
    }

    .scanner-copy{
        font-size:.68rem;
    }

    div[data-testid="stButton"]>button{
        width:100%;
    }

    .result{
        padding:17px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)
# --------------------------- Helpers --------------------------

def safe_text(value, default=""):  # cleans the text
    if value is None:
        return default
    return str(value).strip()




def clamp_score(value):
    try:
        return max(0, min(100, int(float(value))))  # limits score to 0–100
    except (TypeError, ValueError):
        st.warning(
            "⚠️ Threat score unavailable: Insufficient security indicators "
            "were found to make a reliable assessment. Please provide more "
            "complete information and try again."
        )
        return 50




def is_scam_claim(category, verdict, summary=""):
    """Detect a scam claim, trusting the model's explicit threat_category field first.

    The category field is a constrained enum the model was explicitly asked to
    fill in, so it is a far more reliable signal than re-deriving "is this a
    scam" from free-text prose. Regex parsing of the verdict/summary is now
    only a fallback for when the category is missing or ambiguous (e.g. still
    "Needs review"), rather than the primary signal.
    """
    category_text = safe_text(category).strip().lower()

    if category_text == "scam":
        return True

    if category_text and category_text not in {"needs review", ""}:
        # The model gave a specific, non-scam category (e.g. "Safe", "Phishing",
        # "Malware"). Trust it instead of re-scanning prose that might mention
        # the word "scam" in a hedged, comparative, or negated sentence.
        return False

    text = " ".join(
        safe_text(v) for v in (category, verdict, summary)
    ).lower()

    negative_patterns = (
        r"\bnot\s+(?:necessarily\s+)?(?:a\s+)?scam\b",
        r"\bno\s+(?:evidence\s+of\s+)?(?:a\s+)?scam\b",
        r"\b(?:does|do)\s+not\s+(?:appear|seem)\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\bunlikely\s+to\s+be\s+(?:a\s+)?scam\b",
        r"\b(?:cannot|can't)\s+(?:confirm|verify)\s+(?:that\s+it\s+is\s+)?(?:a\s+)?scam\b",
        r"\bno\s+clear\s+indication\s+of\s+(?:a\s+)?scam\b",
    )

    if any(re.search(pattern, text) for pattern in negative_patterns):
        return False

    return bool(re.search(r"\bscam\b", text))




def normalize_result_consistency(result):
    """Keep scam/phishing category, risk score and displayed verdict consistent."""
    category = safe_text(
        result.get("threat_category", "Needs review"),
        "Needs review"
    )
    verdict = safe_text(
        result.get("verdict", "Manual review recommended."),
        "Manual review recommended."
    )
    summary = safe_text(result.get("summary", ""))

    category_lower = category.lower()
    combined_text = f"{category} {verdict} {summary}".lower()

    is_scam = is_scam_claim(category, verdict, summary)

    # Prefer the explicit category for phishing too; fall back to phrase
    # matching only when the category doesn't already say "Phishing".
    is_phishing = category_lower == "phishing" or bool(re.search(
        r"\b(phishing attempt|phishing attack|phishing link|phishing message|is phishing|appears to be phishing)\b",
        combined_text
    ))

    if is_scam or is_phishing:
        if is_scam:
            result["threat_category"] = "Scam"

        result["risk_score"] = max(
            70,
            clamp_score(result.get("risk_score", 50))
        )

        if is_scam and not re.search(r"\bscam\b", verdict.lower()):
            result["verdict"] = "This message is a scam and should not be trusted."

    else:
        result["risk_score"] = clamp_score(
            result.get("risk_score", 50)
        )

    return result

#-------------------------------------------------------------------------------------------------















def risk_label(score, category=""):
    score = clamp_score(score)
    if safe_text(category).lower() == "scam":
        return "SCAM", "critical"
    if score < 35:
        return "SAFE", "safe"
    if score < 70:
        return "CAUTION", "caution"
    return "CRITICAL THREAT", "critical"


def clean_json_text(text):
    text = safe_text(text)
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.I)
    start = text.find("{")
    end = text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text




THREAT_CHECKS = [
    "Scam Indicators",
    "Phishing Signs",
    "Deepfake Risk",
    "Fake Information",
    "Suspicious Links",
    "Impersonation",
    "Malware Indicators",
    "Social Engineering",
]




OFFICIAL_VERIFICATION_SOURCES = [
    {
        "source": "National Cyber Crime Reporting Portal (NCRP)",
        "purpose": "Report cybercrime and financial fraud, and check or report suspicious identifiers such as phone numbers, email IDs, URLs and social-media accounts.",
        "website": "https://www.cybercrime.gov.in/",
    },
    {
        "source": "Indian Cybercrime Coordination Centre (I4C)",
        "purpose": "Government of India initiative coordinating cybercrime prevention, analysis, reporting and response.",
        "website": "https://i4c.mha.gov.in/",
    },
    {
        "source": "CERT-In",
        "purpose": "India's national agency for cybersecurity incident response, alerts, advisories and security guidance.",
        "website": "https://www.cert-in.org.in/",
    },
    {
        "source": "Reserve Bank of India (RBI)",
        "purpose": "Official guidance on banking, digital payments, OTP/PIN safety and prevention of financial and payment fraud.",
        "website": "https://www.rbi.org.in/",
    },
    {
        "source": "National Payments Corporation of India (NPCI)",
        "purpose": "Official information and safety guidance for UPI and India's retail payment systems.",
        "website": "https://www.npci.org.in/",
    },
    {
        "source": "Securities and Exchange Board of India (SEBI)",
        "purpose": "Official investor-protection resources for identifying investment scams, unregistered entities and fraudulent schemes.",
        "website": "https://www.sebi.gov.in/",
    },
    {
        "source": "Sanchar Saathi — Department of Telecommunications",
        "purpose": "Report suspected fraudulent calls, SMS and WhatsApp communications and check mobile connections and handset information.",
        "website": "https://www.sancharsaathi.gov.in/",
    },
    {
        "source": "UIDAI",
        "purpose": "Official Aadhaar services and security guidance for protecting Aadhaar-related identity information.",
        "website": "https://uidai.gov.in/",
    },
    {
        "source": "IRDAI",
        "purpose": "Official insurance-sector guidance and consumer awareness regarding insurance fraud and cybersecurity risks.",
        "website": "https://irdai.gov.in/",
    },
    {
        "source": "National Consumer Helpline (NCH)",
        "purpose": "Government consumer grievance platform for consumer fraud and complaint-related support.",
        "website": "https://consumerhelpline.gov.in/",
    },
    {
        "source": "Employees' Provident Fund Organisation (EPFO)",
        "purpose": "Official guidance for protecting EPFO, UAN and pension-related information from impersonation and fraud.",
        "website": "https://www.epfindia.gov.in/",
    },
    {
        "source": "Income Tax Department",
        "purpose": "Official tax-related services and guidance for identifying fraudulent tax, PAN and income-tax communications.",
        "website": "https://www.incometax.gov.in/",
    },
    {
        "source": "Ministry of Corporate Affairs (MCA)",
        "purpose": "Official company and corporate information for cross-checking registered businesses and corporate identities.",
        "website": "https://www.mca.gov.in/",
    },
]



def normalize_check_value(value):
    if isinstance(value, bool):
        return "Detected" if value else "Not detected"
    if isinstance(value, (int, float)):
        if value >= 70:
            return "High"
        if value >= 35:
            return "Medium"
        return "Low"
    text = safe_text(value)
    if not text:
        return "Needs review"
    return text[:80]


def check_class(value):
    text = safe_text(value).lower()

    if any(x in text for x in (
        "not detected", "none", "no sign", "clear", "false", "absent"
    )):
        return "check-clear"

    if "low" in text:
        return "check-low"

    if any(x in text for x in (
        "detected", "present", "high", "yes", "true", "strong"
    )):
        return "check-detected"

    return "check-review"







#-------------------------------------------------------------------------------------------


def build_fallback_threat_analysis(result):
    category = safe_text(result.get("threat_category", "")).lower()
    indicators = " ".join(result.get("key_indicators", [])).lower()
    summary = safe_text(result.get("summary", "")).lower()
    verdict = safe_text(result.get("verdict", "")).lower()

    text = category + " " + indicators + " " + summary + " " + verdict

    def has(*terms):
        return any(term in text for term in terms)

    public_figure_claim = has(
        "public figure", "celebrity", "politician",
        "brand ambassador", "endorsement", "endorses",
        "celebrity endorsement", "public figure endorsement"
    )

    deepfake = has(
        "deepfake", "deep fake", "synthetic media",
        "ai-generated", "ai generated", "manipulated image",
        "face manipulation", "digitally manipulated"
    )

    fake_claim = has(
        "fake", "false", "fabricat", "misinformation",
        "misleading", "unverified", "unsupported claim",
        "false claim", "deceptive"
    )

    return {
        "Scam Indicators": "Detected" if has(
            "scam", "fraud", "prize", "fee"
        ) else "Needs review",

        "Phishing Signs": "Detected" if has(
            "phishing", "credential", "login", "password", "otp"
        ) else "Needs review",

        "Deepfake Risk": (
            "High" if deepfake
            else "Medium" if public_figure_claim
            else "Low"
        ),

        "Fake Information": "Detected" if fake_claim else "Needs review",

        "Suspicious Links": "Detected" if has(
            "suspicious link", "malicious link", "url", "domain"
        ) else "Needs review",

        "Impersonation": "Detected" if (
            public_figure_claim or has(
                "impersonation", "impersonat",
                "pretend", "fake authority"
            )
        ) else "Needs review",

        "Malware Indicators": "Detected" if has(
            "malware", "trojan", "ransomware", "apk", "virus"
        ) else "Not detected",

        "Social Engineering": "Detected" if has(
            "social engineering", "urgency", "pressure", "manipulation"
        ) else "Needs review",
    }




def build_final_conclusion(result):
    existing = safe_text(result.get("final_conclusion", ""))
    if existing:
        return existing
    label, _ = risk_label(result.get("risk_score", 50), result.get("threat_category", ""))
    summary = safe_text(result.get("summary", ""))
    verdict = safe_text(result.get("verdict", "Manual review recommended."))
    if summary:
        return f"SATARK assessed this item as {label.lower()} based on the evidence identified during analysis. {summary} {verdict} Verify the source independently before taking any high-impact action."
    return f"SATARK assessed this item as {label.lower()}. {verdict} Verify the source independently before taking any high-impact action."


def calibrate_confidence(data, result):
    """Report a SATARK confidence value that reflects real evidence strength.

    Unlike the previous implementation, this does NOT force the value into a
    fixed high band. The raw model confidence is kept as ``model_confidence``
    for auditability, and the user-facing ``confidence`` is the raw value
    adjusted only slightly by how complete/ambiguous the supporting evidence
    is. Weak or ambiguous evidence can and should produce a low confidence
    score — that is the whole point of showing it.
    """
    try:
        raw_conf = float(data.get("confidence", result.get("confidence", 70)))
    except (TypeError, ValueError):
        raw_conf = 70.0
    raw_conf = max(0.0, min(100.0, raw_conf))
    result["model_confidence"] = round(raw_conf, 2)

    checks = result.get("threat_analysis", {}) or {}
    review_count = sum(1 for value in checks.values() if check_class(value) == "check-review")
    evidence_count = len(result.get("key_indicators", []))

    # Ambiguous/unresolved checks should pull confidence down, not up.
    ambiguity_penalty = (review_count / max(1, len(THREAT_CHECKS))) * 20.0

    # Well-evidenced findings get a small, capped bonus — not a floor.
    evidence_bonus = min(5.0, evidence_count * 1.0)

    calibrated = raw_conf - ambiguity_penalty + evidence_bonus
    result["confidence"] = round(max(0.0, min(100.0, calibrated)), 2)
    return result


def normalize_result(data, raw="", model_used=""):
    if not isinstance(data, dict):
        data = {}
    indicators = data.get("key_indicators", data.get("indicators", []))
    recommendations = data.get("recommendations", data.get("safety_recommendations", []))
    if isinstance(indicators, str): indicators = [indicators]
    if isinstance(recommendations, str): recommendations = [recommendations]
    if not isinstance(indicators, list): indicators = []
    if not isinstance(recommendations, list): recommendations = []

    raw_checks = data.get("threat_analysis", {})
    if not isinstance(raw_checks, dict):
        raw_checks = {}
    threat_analysis = {
        check: normalize_check_value(raw_checks.get(check, ""))
        for check in THREAT_CHECKS
    }

    result = {
        "risk_score": clamp_score(data.get("risk_score", data.get("threat_score", 50))),
        "threat_category": safe_text(data.get("threat_category", data.get("category", "Needs review")), "Needs review"),
        "verdict": safe_text(data.get("verdict", data.get("final_verdict", "Manual review recommended.")), "Manual review recommended."),
        "summary": safe_text(data.get("summary", data.get("executive_summary", ""))),
        "key_indicators": [safe_text(x) for x in indicators if safe_text(x)][:8],
        "recommendations": [safe_text(x) for x in recommendations if safe_text(x)][:8],
        "confidence": clamp_score(data.get("confidence", 70)),
        "model_used": model_used or safe_text(data.get("model_used", "")),
        "scam_pattern": safe_text(data.get("scam_pattern", data.get("pattern", ""))),
        "threat_analysis": threat_analysis,
        "final_conclusion": safe_text(data.get("final_conclusion", data.get("conclusion", ""))),
        "verification_sources": OFFICIAL_VERIFICATION_SOURCES,
        "raw": raw,
    }
    result = normalize_result_consistency(result)
    if not result["scam_pattern"]:
        result["scam_pattern"] = result["threat_category"]
    fallback = build_fallback_threat_analysis(result)
    for check in THREAT_CHECKS:
        if result["threat_analysis"][check] == "Needs review":
            result["threat_analysis"][check] = fallback[check]
    result["final_conclusion"] = build_final_conclusion(result)
    result = calibrate_confidence(data, result)
    return result


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return "\n".join(self.parts)


def is_public_url(url):
    parsed = urlparse(safe_text(url))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = socket.getaddrinfo(host, None)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError, OSError):
        return True
    return True


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_public_url(newurl):
            raise ValueError("The URL redirects to a private or unsafe network address.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url):
    url = safe_text(url)
    if not is_public_url(url):
        raise ValueError("For safety, only public HTTP/HTTPS URLs can be fetched.")
    request = Request(url, headers={"User-Agent":"SATARK-Security-Analyzer/2.0", "Accept":"text/html,application/xhtml+xml,text/plain"})
    opener = build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        raw = response.read(1_500_000)
        final_url = response.geturl()
    if not is_public_url(final_url):
        raise ValueError("The final URL is not a public address and was blocked.")
    if "text" not in content_type and "html" not in content_type and "xml" not in content_type:
        return raw.decode("utf-8", errors="ignore")[:12000]
    parser = VisibleTextParser()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    text = parser.text() or raw.decode("utf-8", errors="ignore")
    return text[:30000]


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []
    for page in reader.pages[:30]:
        try:
            text = page.extract_text() or ""
            if text.strip(): pages.append(text)
        except Exception:
            pass
    text = "\n\n".join(pages).strip()
    if not text:
        raise ValueError("No readable text was found in this PDF. It may be scanned/image-only. Please use a screenshot/image of the relevant page for vision analysis.")
    return text[:50000]


def image_to_data_url(uploaded_file):
    """Convert one uploaded image to a compact JPEG data URL.

    Kept modest in size (max_side=900, moderate JPEG quality) so a small
    number of images stays well under Groq's on-demand tokens-per-minute
    budget for vision models — full-resolution uploads were previously
    large enough on their own to trip the TPM rate limit."""
    from io import BytesIO
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    image = Image.open(uploaded_file).convert("RGB")
    max_side = 900
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    for quality in (75, 62, 50, 40):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        if len(encoded) <= 900_000 or quality == 40:
            return f"data:image/jpeg;base64,{encoded}"
    return f"data:image/jpeg;base64,{encoded}"


def images_to_data_urls(uploaded_files, max_images=5):
    """Convert multiple uploaded images while keeping the request manageable."""
    if not uploaded_files:
        return []
    urls = []
    for uploaded_file in list(uploaded_files)[:max_images]:
        urls.append(image_to_data_url(uploaded_file))
    return urls


def uploaded_fingerprint(uploaded_files):
    """Return a content fingerprint so a new scan cannot reuse stale image state."""
    if not uploaded_files:
        return ""
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        try:
            data = uploaded_file.getvalue()
        except Exception:
            data = b""
        digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
        digest.update(str(len(data)).encode("ascii"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def single_file_fingerprint(uploaded_file):
    """Fingerprint a single uploaded file (used for video scanning)."""
    if not uploaded_file:
        return ""
    try:
        data = uploaded_file.getvalue()
    except Exception:
        data = b""
    digest = hashlib.sha256()
    digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
    digest.update(str(len(data)).encode("ascii"))
    digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


# ------------------- Video: frame + audio extraction -------------------
# Videos are not sent to the vision model directly. Instead SATARK pulls a
# handful of representative frames (evenly spaced through the clip) with
# OpenCV and treats them exactly like an "Image" scan. If OpenCV or an
# audio-transcription path is unavailable in this environment, SATARK
# degrades gracefully and explains what could not be analyzed rather than
# crashing the whole scan.
MAX_VIDEO_FRAMES = 2  # kept minimal — every extra frame competes with the
# transcript and system prompt for the same tight tokens-per-minute budget
MAX_VIDEO_BYTES = 200 * 1024 * 1024  # 200 MB safety cap for in-memory handling


def _video_dependencies_available():
    try:
        import cv2  # noqa: F401
        return True
    except Exception:
        return False


def extract_video_frames(uploaded_file, max_frames=MAX_VIDEO_FRAMES):
    """Extract up to `max_frames` evenly spaced frames from an uploaded video
    as PIL Images. Returns (frames, duration_seconds, warnings)."""
    import tempfile

    try:
        import cv2
    except Exception as exc:
        raise RuntimeError(
            "Video frame extraction requires OpenCV (opencv-python-headless), "
            "which is not installed in this environment. Run "
            "`pip install opencv-python-headless --break-system-packages` and restart the app."
        ) from exc

    warnings = []
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    data = uploaded_file.read()
    if len(data) > MAX_VIDEO_BYTES:
        raise ValueError("This video is larger than the 200 MB limit SATARK can safely process in-session.")
    if not data:
        raise ValueError("The uploaded video appears to be empty or unreadable.")

    suffix = os.path.splitext(safe_text(getattr(uploaded_file, "name", "")))[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    frames = []
    duration = 0.0
    try:
        capture = cv2.VideoCapture(tmp_path)
        if not capture.isOpened():
            raise ValueError("SATARK could not open this video file. It may be corrupted or in an unsupported codec.")

        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = (frame_count / fps) if fps > 0 else 0.0

        if frame_count <= 0:
            # Fall back to sequential reads if metadata is unreliable.
            count = 0
            while True:
                ok, frame_bgr = capture.read()
                if not ok:
                    break
                count += 1
                if count % 30 == 0 and len(frames) < max_frames:
                    frames.append(_bgr_to_pil(frame_bgr))
                if len(frames) >= max_frames:
                    break
            if not frames:
                raise ValueError("SATARK could not read any frames from this video.")
        else:
            target_frames = min(max_frames, frame_count)
            indices = [int(i * (frame_count - 1) / max(1, target_frames - 1)) for i in range(target_frames)] if target_frames > 1 else [0]
            for idx in indices:
                capture.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame_bgr = capture.read()
                if ok:
                    frames.append(_bgr_to_pil(frame_bgr))
            if not frames:
                raise ValueError("SATARK could not extract readable frames from this video.")

        capture.release()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    return frames, duration, warnings


def _bgr_to_pil(frame_bgr):
    import cv2
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def pil_frames_to_data_urls(frames, max_side=512):
    """Convert extracted PIL frames into compact JPEG data URLs for the vision
    model. Kept small (512px, low JPEG quality) because Groq's on-demand tier
    has a tight tokens-per-minute budget shared across every frame AND the
    audio transcript AND the system prompt in the same request."""
    from io import BytesIO
    urls = []
    for image in frames:
        image = image.convert("RGB")
        if max(image.size) > max_side:
            scale = max_side / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
        for quality in (55, 42, 30):
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            if len(encoded) <= 400_000 or quality == 30:
                urls.append(f"data:image/jpeg;base64,{encoded}")
                break
    return urls


def transcribe_video_audio(uploaded_file, client):
    """Best-effort audio transcription via Groq Whisper. Returns "" if audio
    extraction isn't available in this environment rather than failing the
    whole video scan — frame analysis can still proceed without it."""
    import tempfile

    try:
        import cv2  # noqa: F401
    except Exception:
        return ""

    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
    except Exception:
        return ""

    suffix = os.path.splitext(safe_text(getattr(uploaded_file, "name", "")))[1] or ".mp4"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )
        text = transcript if isinstance(transcript, str) else safe_text(getattr(transcript, "text", ""))
        # Kept short: on Groq's on-demand tier the tokens-per-minute budget is
        # shared across the transcript, the system prompt, and every video
        # frame in the same request, so a long transcript alone can blow the
        # limit even with small images.
        return text.strip()[:3000]
    except Exception:
        # Audio may be silent, absent, or the account may lack Whisper access.
        # Frame-only analysis is still useful, so don't raise here.
        return ""
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def get_client(api_key):
    key = safe_text(api_key)
    return Groq(api_key=key) if key else None


# ---------------------- Model discovery ------------------------
TEXT_MODEL_PREFERENCES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]
# Vision model fallback chain. Previously this was a single hardcoded model
# (qwen/qwen3.6-27b), which meant image/QR analysis broke entirely the moment
# that one model became unavailable or the API key lost access to it.
# analyze_with_groq now tries each of these in order and only reports failure
# once every candidate has been exhausted.
VISION_MODEL_PREFERENCES = [
    "qwen/qwen3.6-27b",
]

# Some vision models cap how many images can be sent in one request (e.g. Qwen
# allows only 3). Keyed by model id; models not listed here use the default
# cap applied in analyze_with_groq.
VISION_MODEL_IMAGE_LIMITS = {
    "qwen/qwen3.6-27b": 3,
}


def discover_models(client):
    """Ask Groq which models this exact API key can access."""
    try:
        listing = client.models.list()
        items = getattr(listing, "data", listing)
        ids = set()
        for item in items or []:
            mid = getattr(item, "id", None)
            if mid:
                ids.add(str(mid))
            elif isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
        return ids
    except Exception:
        return set()


def choose_model(available, preferences):
    if not available:
        return preferences[0]
    for model in preferences:
        if model in available:
            return model
    return None


def model_status(client):
    available = discover_models(client)
    text_model = choose_model(available, TEXT_MODEL_PREFERENCES)
    vision_model = choose_model(available, VISION_MODEL_PREFERENCES)
    return available, text_model, vision_model


# ------------------------- AI analysis --------------------------
SYSTEM_PROMPT = """
You are SATARK, a careful digital-threat and content-authenticity analysis assistant.

Analyze the content for scams, phishing, social engineering, malware, impersonation,
suspicious links, credential theft, fraud, payment fraud, account takeover, malicious
QR codes, deepfakes, AI-generated/manipulated media, and fabricated or misleading claims.

Rules:
- Never claim certainty when evidence is weak. Distinguish evidence from inference.
- Confidence must reflect evidence strength: weak/ambiguous evidence → below 50; only
  strong, unambiguous evidence → above 85. Do not default high.
- Do not invent URLs, organizations, sender details, or facts not visible in the input.
- CRITICAL: Professional visual quality (clean logo, good typography, polished layout)
  is NOT evidence of truthfulness. A fabricated or AI-generated endorsement can look just
  as polished as a real one. Never let visual/production quality lower your Fake
  Information, Impersonation, or Deepfake Risk scores — judge those on the plausibility
  of the underlying claim, not the graphic design.
- For any image that asserts a specific named real person did/said/endorsed something,
  treat this as an unverified factual claim requiring scrutiny, not just a design
  element. Explicitly reason about real-world plausibility given who the person is and
  what role or position they are commonly known for (e.g. a person widely known to hold
  a government office, judicial role, regulatory position, or similar public-trust role
  making a commercial product endorsement is unusual and often against normal conduct
  norms — flag this tension). This applies generally to any named real person, not only
  political figures — also apply it to claimed celebrity, executive, or institutional
  endorsements that seem inconsistent with what is publicly known about that person or
  organization. Raise Fake Information / Impersonation to at least Medium when such a
  claim cannot be corroborated from the image alone.
- For images/video frames: inspect visible text, URLs, QR content, logos, layout,
  instructions, and whether content may be AI-generated, manipulated, or a deepfake.
  Identify factual claims (quotes, endorsements, identities, affiliations) that may need
  verification. Do NOT classify as Safe merely because it looks like a normal/professional
  graphic — cybersecurity safety and content authenticity are separate axes, and a "Safe"
  cybersecurity verdict must not imply the claims shown are true.
- If the image depicts a real, named person making an endorsement/claim that you cannot
  verify from the image alone, the verdict and summary MUST state plainly that this
  cannot be confirmed as genuine and should be independently verified before belief or
  sharing — do not phrase this as an optional suggestion buried only in recommendations.
- For URLs: consider domain mismatch, redirects, credential requests, urgency, impersonation.

Return ONLY valid JSON, no markdown, no code fences. Required schema:
{
  "risk_score": 0,
  "confidence": 0,
  "threat_category": "Safe / Phishing / Scam / Malware / Impersonation / Suspicious Link / Payment Fraud / Account Takeover / Unverified Claim / Other",
  "verdict": "one short sentence",
  "summary": "2-4 sentence plain-English explanation",
  "key_indicators": ["indicator 1", "indicator 2"],
  "recommendations": ["action 1", "action 2"],
  "scam_pattern": "one short pattern name",
  "threat_analysis": {
    "Scam Indicators": "Detected / Not detected / Low / Medium / High",
    "Phishing Signs": "Detected / Not detected / Low / Medium / High",
    "Deepfake Risk": "Detected / Not detected / Low / Medium / High",
    "Fake Information": "Detected / Not detected / Low / Medium / High",
    "Suspicious Links": "Detected / Not detected / Low / Medium / High",
    "Impersonation": "Detected / Not detected / Low / Medium / High",
    "Malware Indicators": "Detected / Not detected / Low / Medium / High",
    "Social Engineering": "Detected / Not detected / Low / Medium / High"
  },
  "final_conclusion": "2-4 sentence final conclusion explaining why the assessment was reached"
}
"""


def analyze_with_groq(client, content, mode, role, image_data_urls=None, available_models=None):
    """Run a SATARK analysis using an appropriate Groq model.

    Vision requests now try each model in VISION_MODEL_PREFERENCES in order
    instead of a single hardcoded model, so a deprecated/inaccessible vision
    model no longer breaks image/QR/video analysis entirely. Text scans keep
    the existing SATARK text-model fallback chain. Video mode reuses the
    vision pipeline: frames are converted to data URLs before this function
    is called, exactly like the Image mode.

    The model-list endpoint is treated as a hint only: if the key can call the
    model successfully, SATARK proceeds even when model discovery is incomplete.
    """
    available_models = available_models or set()
    image_data_urls = list(image_data_urls or [])

    if len(image_data_urls) > 6:
        image_data_urls = image_data_urls[:6]

    user_prompt = f"""
Analysis type: {mode}
User profile: {role}

Analyze this content carefully:
{content}

Return a complete SATARK result using the required JSON schema. Do not omit
fields. For threat_analysis, use exactly one of: Detected, Needs review,
Not detected, Low, Medium, High.
"""

    def call(model, repair=False):
        common = {
            "model": model,
            "temperature": 0 if repair else 0.1,
            "max_tokens": 900 if not repair else 800,
            "response_format": {"type": "json_object"},
        }

        if image_data_urls:
            # Respect per-model image-count limits (e.g. Qwen accepts at most
            # 3 images per request) instead of sending every frame/image and
            # letting the API reject the whole call.
            per_model_limit = VISION_MODEL_IMAGE_LIMITS.get(model, len(image_data_urls))
            urls_for_model = image_data_urls[:per_model_limit]
            multimodal_content = [{"type": "text", "text": user_prompt}]
            for image_url in urls_for_model:
                multimodal_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": multimodal_content},
            ]
            common["reasoning_effort"] = "none"
        else:
            common["messages"] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

        return client.chat.completions.create(**common)

    if image_data_urls:
        # Try every configured vision model in order rather than only the
        # first one. This is the fallback chain fix — previously the loop
        # below would `break` after a single failure for image requests.
        discovered_first = [m for m in VISION_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in VISION_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks
    else:
        discovered_first = [m for m in TEXT_MODEL_PREFERENCES if m in available_models]
        undiscovered_fallbacks = [m for m in TEXT_MODEL_PREFERENCES if m not in available_models]
        candidates = discovered_first + undiscovered_fallbacks

    errors = []

    for model in candidates:
        try:
            response = call(model)
            raw = response.choices[0].message.content or ""

            # Groq normally returns a string. Be defensive if an SDK version
            # exposes structured content instead.
            if not isinstance(raw, str):
                if isinstance(raw, list):
                    raw = "".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in raw
                    )
                else:
                    raw = str(raw)

            raw = raw.strip()
            if not raw:
                raise RuntimeError("The AI model returned an empty response.")

            try:
                parsed = json.loads(clean_json_text(raw))
            except (json.JSONDecodeError, TypeError, ValueError) as parse_error:
                # JSON mode should make this uncommon. If a provider/SDK still
                # returns malformed content, perform one controlled repair call
                # with JSON mode enabled instead of falling through to another
                # unrelated model.
                repair_prompt = (
                    "Convert the following SATARK analysis into one valid JSON object. "
                    "Return ONLY JSON. Use exactly these top-level keys: "
                    "risk_score, confidence, threat_category, verdict, summary, "
                    "key_indicators, recommendations, scam_pattern, threat_analysis, "
                    "final_conclusion.\n\n"
                    + raw
                )
                original_prompt = user_prompt
                user_prompt = repair_prompt
                try:
                    repair_response = call(model, repair=True)
                finally:
                    user_prompt = original_prompt

                repaired = repair_response.choices[0].message.content or ""
                if not isinstance(repaired, str):
                    repaired = str(repaired)
                repaired = repaired.strip()
                if not repaired:
                    raise RuntimeError("The AI model returned an empty JSON repair response.")
                parsed = json.loads(clean_json_text(repaired))
                raw = repaired

            if not isinstance(parsed, dict):
                raise RuntimeError("The AI model returned JSON, but it was not a JSON object.")

            result = normalize_result(parsed, raw, model)
            result["scam_pattern"] = safe_text(
                parsed.get("scam_pattern", result.get("threat_category", "Needs review")),
                result.get("threat_category", "Needs review"),
            )
            return normalize_result_consistency(result)

        except Exception as exc:
            errors.append(f"{model}: {exc}")
            # Move on to the next candidate model instead of giving up
            # immediately — this applies to text, image and video requests now.
            continue

    detail = "\n".join(errors[-4:])
    kind = "image/QR/video" if image_data_urls else "text"
    rate_limited = any("rate_limit_exceeded" in e or "Request too large" in e for e in errors)

    if image_data_urls:
        hint = (
            "\n\nThis looks like a Groq rate-limit (tokens-per-minute) issue on the free/on-demand "
            "tier rather than a broken model. Wait a minute and try again with fewer or smaller "
            "images, or upgrade the Groq account tier."
        ) if rate_limited else ""
        raise RuntimeError(
            "SATARK could not complete the visual analysis with any configured "
            "vision model (tried: " + ", ".join(candidates) + "). Please verify "
            "that this Groq API key/project has access to at least one supported "
            "vision model and try again.\n" + detail + hint
        )

    raise RuntimeError(
        f"SATARK could not complete the {kind} analysis with any configured Groq model.\n{detail}"
    )


# ---------------------- UI/result helpers ----------------------
def render_threat_analysis(result):
    rows = []
    for check in THREAT_CHECKS:
        value = safe_text(result.get("threat_analysis", {}).get(check, "Needs review"), "Needs review")
        cls = check_class(value)
        icon = "✖" if cls == "check-clear" else "✓" if cls == "check-detected" else "•"
        rows.append(f'<tr><td>{html.escape(check)}</td><td class="{cls}">{icon} {html.escape(value)}</td></tr>')
    table = (
        '<table class="report-table"><thead><tr><th>Security Check</th><th>Result</th></tr></thead>'
        '<tbody>' + ''.join(rows) + '</tbody></table>'
    )
    legend = (
        '<div class="status-legend">'
        '<div class="status-legend-title">How to read the results</div>'
        '<span class="status-item"><span class="status-detected">✓ Detected</span> — sufficient evidence that the indicator is present.</span>'
        '<span class="status-item"><span class="status-review">• Needs review</span> — evidence is ambiguous or insufficient; verify it manually.</span>'
        '<span class="status-item"><span class="status-clear">✖ Not detected</span> — no meaningful evidence of that indicator was found.</span>'
        '</div>'
    )
    st.markdown(f'<section class="report-section"><h3>🔎 Threat Analysis</h3>{table}{legend}</section>', unsafe_allow_html=True)


def render_verification_sources(result):
    rows=[]
    for item in result.get("verification_sources", OFFICIAL_VERIFICATION_SOURCES):
        source=html.escape(safe_text(item.get("source")))
        purpose=html.escape(safe_text(item.get("purpose")))
        website=safe_text(item.get("website"))
        safe_href=html.escape(website, quote=True)
        safe_label=html.escape(website)
        rows.append(f'<tr><td>{source}</td><td>{purpose}</td><td><a class="source-link" href="{safe_href}" target="_blank">{safe_label}</a></td></tr>')
    table=(
        '<table class="report-table"><thead><tr><th>Source</th><th>Purpose</th><th>Official Website</th></tr></thead>'
        '<tbody>'+''.join(rows)+'</tbody></table>'
    )
    st.markdown(f'<section class="report-section"><h3>📚 Official Verification Sources</h3>{table}</section>', unsafe_allow_html=True)


def confidence_css_class(confidence):
    """Color-code the confidence metric so low-confidence results are visually
    distinct instead of looking identical to high-confidence ones."""
    if confidence >= 85:
        return "safe"
    if confidence >= 50:
        return "caution"
    return "critical"


def render_result(result):
    score = clamp_score(result.get("risk_score",50))
    label, css = risk_label(score, result.get("threat_category", ""))
    indicators = result.get("key_indicators", [])
    recs = result.get("recommendations", [])
    confidence = float(result.get("confidence",70.0))
    conf_css = confidence_css_class(confidence)
    category = html.escape(result.get("threat_category","Needs review"))
    verdict = html.escape(result.get("verdict","Manual review recommended."))
    pattern = html.escape(result.get("scam_pattern", category))

    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown('<div class="result-head">🛡️ SATARK Security Report</div><div class="eyebrow">Evidence-first AI assessment • advisory, not a guarantee</div>', unsafe_allow_html=True)
    a,b,c,d = st.columns(4)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Threat level</div><div class="metric-value {css}">{label}</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Risk score</div><div class="metric-value">{score}/100</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">Pattern</div><div class="metric-value" style="font-size:1rem">{pattern}</div></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="metric"><div class="metric-label">AI confidence</div><div class="metric-value {conf_css}">{confidence:.2f}%</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="bar"><div style="width:{score}%"></div></div>',unsafe_allow_html=True)
    if confidence < 50:
        st.info("ℹ️ Confidence is low — the evidence found was limited or ambiguous. Treat this result as a starting point, not a final answer, and verify manually.")
    st.markdown(f'<div class="verdict"><strong>Final verdict</strong><br>{verdict}</div>',unsafe_allow_html=True)

    if result.get("summary"):
        st.markdown("### 🔎 What SATARK found")
        st.markdown(f'<p style="color:#e4e4ea;line-height:1.8">{html.escape(result["summary"])}</p>', unsafe_allow_html=True)

    left,right = st.columns(2)
    with left:
        st.markdown('<div class="evidence"><strong>🧩 Evidence detected</strong>',unsafe_allow_html=True)
        if indicators:
            for item in indicators:
                st.markdown(f'<div class="evidence-item">⚠️ {html.escape(item)}</div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="evidence-item">No specific indicators were returned.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="evidence"><strong>🧭 What to do now</strong>',unsafe_allow_html=True)
        if recs:
            for item in recs:
                st.markdown(f'<div class="action-item"><span>✓</span><span>{html.escape(item)}</span></div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="action-item">Review the content manually before acting.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    render_threat_analysis(result)
    render_verification_sources(result)

    conclusion = html.escape(build_final_conclusion(result))
    st.markdown(f'<section class="report-section"><h3>💡 Final Conclusion</h3><div class="conclusion-card">{conclusion}</div></section>', unsafe_allow_html=True)


def pdf_escape(text):
    return html.escape(safe_text(text)).replace("\n", "<br/>")


def make_pdf_report(result, mode):
    """Create a polished, readable PDF version of the complete SATARK report."""
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm, title="SATARK Security Report"
    )
    styles = getSampleStyleSheet()
    dark = colors.HexColor("#111113")
    muted = colors.HexColor("#5f6270")
    violet = colors.HexColor("#6656d9")
    light_violet = colors.HexColor("#f0edff")
    line = colors.HexColor("#d9d9e2")
    green = colors.HexColor("#188a4b")
    red = colors.HexColor("#c92a4d")
    amber = colors.HexColor("#9a6500")

    title = ParagraphStyle("SATARKTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=dark, spaceAfter=5)
    subtitle = ParagraphStyle("SATARKSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=muted, spaceAfter=12)
    h2 = ParagraphStyle("SATARKH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=dark, spaceBefore=12, spaceAfter=8)
    body = ParagraphStyle("SATARKBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=14, textColor=dark, spaceAfter=6)
    small = ParagraphStyle("SATARKSmall", parent=body, fontSize=8, leading=11, textColor=muted)
    verdict_style = ParagraphStyle("SATARKVerdict", parent=body, fontName="Helvetica-Bold", fontSize=10, leading=15, textColor=dark)
    centered = ParagraphStyle("SATARKCentered", parent=body, alignment=TA_CENTER, fontSize=8, textColor=muted)

    score=clamp_score(result.get("risk_score",50)); label,_=risk_label(score,result.get("threat_category",""))
    confidence_value = float(result.get('confidence',70.0))
    confidence_color = green if confidence_value >= 85 else (amber if confidence_value >= 50 else red)
    story=[]
    story.append(Paragraph("SATARK", title))
    story.append(Paragraph("Smart AI Threat Analysis & Risk Knowledge", subtitle))
    conf_cell_style = ParagraphStyle("SATARKConfCell", parent=body, textColor=confidence_color, fontName="Helvetica-Bold")
    meta=[[Paragraph("Scanner", body), Paragraph(pdf_escape(mode), body), Paragraph("Generated", body), Paragraph(datetime.now().strftime('%d %b %Y, %I:%M %p'), body)],
          [Paragraph("Threat level", body), Paragraph(pdf_escape(label), body), Paragraph("Risk score", body), Paragraph(f"{score}/100", body)],
          [Paragraph("Pattern", body), Paragraph(pdf_escape(result.get('scam_pattern','Needs review')), body), Paragraph("AI confidence", body), Paragraph(f"{confidence_value:.2f}%", conf_cell_style)]]
    meta_table=Table(meta,colWidths=[25*mm,60*mm,30*mm,60*mm],hAlign='LEFT')
    meta_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f7f6fb')),('BOX',(0,0),(-1,-1),0.7,line),('INNERGRID',(0,0),(-1,-1),0.4,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(meta_table)

    story.append(Paragraph("Final Verdict", h2))
    verdict_data=[[Paragraph(pdf_escape(result.get('verdict','Manual review recommended.')), verdict_style)]]
    vt=Table(verdict_data,colWidths=[175*mm])
    vt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_violet),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#b6adff')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(vt)

    story.append(Paragraph("What SATARK Found", h2))
    story.append(Paragraph(pdf_escape(result.get('summary','No summary was returned.')), body))

    story.append(Paragraph("Evidence Detected", h2))
    evidence=result.get('key_indicators',[]) or ['No specific indicators were returned.']
    story.append(Paragraph('<br/>'.join('• '+pdf_escape(x) for x in evidence), body))

    story.append(Paragraph("What To Do Now", h2))
    recs=result.get('recommendations',[]) or ['Review the content manually before acting.']
    story.append(Paragraph('<br/>'.join('• '+pdf_escape(x) for x in recs), body))

    story.append(Paragraph("Threat Analysis", h2))
    threat_data=[[Paragraph('<b>Security Check</b>',body),Paragraph('<b>Result</b>',body)]]
    for check in THREAT_CHECKS:
        value=safe_text(result.get('threat_analysis',{}).get(check,'Needs review'),'Needs review')
        threat_data.append([Paragraph(pdf_escape(check),body),Paragraph(pdf_escape(value),body)])
    tt=Table(threat_data,colWidths=[95*mm,80*mm],repeatRows=1)
    ts=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeaff')),('TEXTCOLOR',(0,0),(-1,0),dark),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
    for row_idx in range(1,len(threat_data)):
        value=safe_text(result.get('threat_analysis',{}).get(THREAT_CHECKS[row_idx-1],''))
        cls=check_class(value)
        text_color=green if cls=='check-detected' else red if cls=='check-clear' else amber
        ts.append(('TEXTCOLOR',(1,row_idx),(1,row_idx),text_color))
    tt.setStyle(TableStyle(ts))
    story.append(tt)
    legend_style = ParagraphStyle("SATARKLegend", parent=small, fontSize=8, leading=11, textColor=dark, spaceBefore=5)
    story.append(Paragraph(
        '<b>Status guide:</b> '
        '<font color="#188a4b"><b>Detected</b></font> — sufficient evidence that the indicator is present. '
        '<font color="#b07a00"><b>Needs review</b></font> — evidence is ambiguous or insufficient; verify it manually. '
        '<font color="#c92a4d"><b>Not detected</b></font> — no meaningful evidence of that indicator was found.',
        legend_style
    ))

    story.append(Paragraph("Official Verification Sources", h2))
    source_data=[[Paragraph('<b>Source</b>',body),Paragraph('<b>Purpose</b>',body),Paragraph('<b>Official Website</b>',body)]]
    for item in result.get('verification_sources',OFFICIAL_VERIFICATION_SOURCES):
        website=safe_text(item.get('website'))
        source_data.append([Paragraph(pdf_escape(item.get('source')),body),Paragraph(pdf_escape(item.get('purpose')),body),Paragraph(f'<link href="{html.escape(website,quote=True)}" color="#4d3dcc"><u>{pdf_escape(website)}</u></link>',body)])
    stbl=Table(source_data,colWidths=[42*mm,75*mm,58*mm],repeatRows=1)
    stbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeaff')),('GRID',(0,0),(-1,-1),0.5,line),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.append(stbl)

    story.append(Paragraph("Final Conclusion", h2))
    conclusion=Paragraph(pdf_escape(build_final_conclusion(result)),body)
    ct=Table([[conclusion]],colWidths=[175*mm])
    ct.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),light_violet),('BOX',(0,0),(-1,-1),0.7,colors.HexColor('#b6adff')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    story.append(ct)
    story.append(Spacer(1,8))
    story.append(Paragraph("SATARK is an AI-assisted advisory tool. Verify high-impact security decisions independently.", centered))

    def add_page(canvas, doc):
        canvas.saveState()
        width,height=A4
        canvas.setFillColor(violet)
        canvas.rect(0,height-5*mm,width,5*mm,fill=1,stroke=0)
        canvas.setFillColor(muted)
        canvas.setFont('Helvetica',7.5)
        canvas.drawString(15*mm,8*mm,'SATARK • Smart AI Threat Analysis & Risk Knowledge')
        canvas.drawRightString(width-15*mm,8*mm,f'Page {doc.page}')
        canvas.restoreState()

    doc.build(story,onFirstPage=add_page,onLaterPages=add_page)
    return buffer.getvalue()


def add_history(result, mode):
    if "history" not in st.session_state: st.session_state.history=[]
    entry = {
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "mode": mode,
        "score": clamp_score(result.get("risk_score",50)),
        "category": result.get("threat_category","Needs review"),
        "verdict": result.get("verdict",""),
        "result": result,
    }
    st.session_state.history.insert(0,entry)
    st.session_state.history=st.session_state.history[:20]



# ----------------------- Session state -------------------------
def init_state():
    defaults={
        "mode":"Text","result":None,"history":[],"page":"Home",
        "challenge_index":0,"challenge_score":0,"challenge_answered":False,
        "available_models":set(),"text_model":None,"vision_model":None,
        "last_input_fingerprint":"","analysis_request_id":"",
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v
init_state()

# --------------------------- Sidebar ---------------------------
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-logo">SATARK <span class="brand-dot">◦</span></div><div class="brand-tag">Smart AI Threat Analysis & Risk Knowledge</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="side-label">Navigate</div>',unsafe_allow_html=True)
    for page,label in [("Home","🏠 Home"),("Analyze","🔎 Check something"),("History","🕘 History"),("Challenge","🎯 Scam Challenge"),("Academy","🎓 SATARK Academy"),("Classroom","👨‍🏫 Classroom Mode")]:
        if st.button(label,key=f"nav_{page}",use_container_width=True): st.session_state.page=page; st.rerun()
    st.markdown('<div class="side-label">API configuration</div>',unsafe_allow_html=True)
    env_key=os.getenv("GROQ_API_KEY","")
    api_key=st.text_input("🔑 Groq API Key",value=env_key,type="password",placeholder="Paste your Groq API key",help="Kept in the Streamlit session; not intentionally written to disk by SATARK.")
    if api_key:
        if st.button("Check AI connection",key="check_ai",use_container_width=True):
            try:
                client=get_client(api_key); available=discover_models(client)
                st.session_state.available_models=available
                st.session_state.text_model=choose_model(available,TEXT_MODEL_PREFERENCES)
                st.session_state.vision_model=choose_model(available,VISION_MODEL_PREFERENCES)
                if st.session_state.text_model and st.session_state.vision_model: st.success("AI connected • text + vision available")
                elif st.session_state.text_model: st.warning("AI connected • text available, no vision model exposed to this key")
                else: st.error("API key is accepted but no supported SATARK text model was found.")
            except Exception as exc: st.error(f"Could not check Groq: {exc}")
    st.markdown('<div class="side-label">Personalization</div>',unsafe_allow_html=True)
    role=st.selectbox("👤 Who are you?",["Student","Teacher","Working professional","Parent / Guardian","Senior user","Security learner"],index=0)
    st.markdown('<div class="privacy"><strong>🔒 Privacy first</strong><br>SATARK keeps history only in this Streamlit session. Submitted content is not intentionally saved to disk by this app. Content is sent to Groq only when you analyze it. Avoid passwords, private keys and secrets.</div>',unsafe_allow_html=True)

# ---------------------------- Hero -----------------------------
st.markdown('<section class="hero"><div class="pill">AI SECURITY • EXPLAIN • LEARN • PROTECT</div><h1><span class="hero-primary">Think it’s a scam?</span><br><span class="hero-secondary">Let <span class="hero-brand">SATARK</span> check it.</span></h1><p><strong>Paste a message, inspect a link, upload a screenshot, video, or analyze a PDF.</strong><br>SATARK explains the risk in simple language and shows the evidence behind its assessment.</p></section>',unsafe_allow_html=True)

# --------------------------- Pages -----------------------------
 
if st.session_state.page == "Home":
 
    st.markdown('<div class="analyze">', unsafe_allow_html=True)
 
    if st.button(
        "Let SATARK Check It",
        use_container_width=True,
        type="primary",
        key="goto_analyze"
    ):
        st.session_state.page = "Analyze"
        st.session_state.scroll_to_scanners = True
        st.rerun()
 
    st.markdown('</div>', unsafe_allow_html=True)
 
 
elif st.session_state.page == "Analyze":
 
    # ==========================================================
    # AUTO-SCROLL TO SCANNER SECTION
    # ==========================================================
 
    # Invisible anchor placed immediately before scanner cards
    st.markdown(
        '<div id="satark-scanner-anchor"></div>',
        unsafe_allow_html=True
    )
 
    # Scroll to scanner section only after clicking
    # "Let SATARK Check It" from the Home page.
    if st.session_state.get("scroll_to_scanners", False):
 
        import streamlit.components.v1 as components
 
        components.html(
            """
            <script>
            setTimeout(function() {
 
                const el =
                    window.parent.document.getElementById(
                        'satark-scanner-anchor'
                    );
 
                if (el) {
                    el.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
 
            }, 300);
            </script>
            """,
            height=0,
        )
 
        st.session_state.scroll_to_scanners = False
 
 
    # ==========================================================
    # SCANNER SELECTION
    # ==========================================================
 
    st.markdown(
        '<div class="section-title">What do you want to check?</div>'
        '<div class="section-copy">'
        'Choose a scanner. Your original six SATARK modes remain available, plus Video.'
        '</div>',
        unsafe_allow_html=True
    )
 
    scanner_rows = [
        [
            ("Text", "💬", "Messages, posts and suspicious text"),
            ("URL", "🔗", "Websites and suspicious links"),
            ("Image", "🖼️", "Suspicious Screenshots and images")
        ],
        [
            ("PDF", "📄", "Fraudlent Text-based documents"),
            ("QR", "▣", "QR screenshots and QR-related images"),
            ("Video", "🎬", "Suspicious clips, reels and voice-call recordings")
        ]
    ]
 
    for row in scanner_rows:
 
        cols = st.columns(3)
 
        for col, (name, icon, copy) in zip(cols, row):
 
            with col:
 
                active = st.session_state.mode == name
 
                # Whole card is now clickable: card markup + an
                # invisible, fully-stretched button layered on top
                # via the .scanner-wrap CSS defined above.
                st.markdown('<div class="scanner-wrap">', unsafe_allow_html=True)
 
                st.markdown(
                    f'''
                    <div class="scanner {"active" if active else ""}">
                        <div class="scanner-icon">{icon}</div>
                        <div class="scanner-title">{name}</div>
                        <div class="scanner-copy">{copy}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )
 
                clicked = st.button(
                    "",
                    key=f"scanner_{name}",
                    use_container_width=True
                )
 
                st.markdown('</div>', unsafe_allow_html=True)
 
                if clicked:
                    st.session_state.mode = name
                    st.session_state.result = None
                    st.session_state.last_input_fingerprint = ""
                    st.session_state.analysis_request_id = ""
 
                    # Unique trigger for EVERY scanner click.
                    # This makes the auto-scroll repeat indefinitely.
                    st.session_state.scroll_to_input_trigger = (
                        st.session_state.get("scroll_to_input_trigger", 0) + 1
                    )
 
                    st.rerun()
 
 
    # ==========================================================
    # SELECTED MODE
    # ==========================================================
 
    mode = st.session_state.mode
 
 
    # ==========================================================
    # AUTO-SCROLL TO INPUT SECTION
    # ==========================================================
 
    # Invisible anchor immediately above Security Analysis
    st.markdown(
        '<div id="satark-input-anchor"></div>',
        unsafe_allow_html=True
    )
 
    # A new number is generated every time one of the scanner
    # buttons is clicked. We only handle each number once, so
    # normal Streamlit reruns (typing/uploading) do not cause
    # unwanted scrolling.
    scroll_trigger = st.session_state.get(
        "scroll_to_input_trigger",
        0
    )
 
    handled_trigger = st.session_state.get(
        "handled_scroll_to_input_trigger",
        0
    )
 
    if scroll_trigger != handled_trigger:
        import streamlit.components.v1 as components
 
        components.html(
            f"""
            <script>
            (function() {{
                const trigger = "{scroll_trigger}";
                let attempts = 0;
 
                function scrollToSATARKInput() {{
                    const parentDoc = window.parent.document;
 
                    const el = parentDoc.getElementById(
                        "satark-input-anchor"
                    );
 
                    if (el) {{
                        el.scrollIntoView({{
                            behavior: "smooth",
                            block: "start"
                        }});
                        return true;
                    }}
 
                    return false;
                }}
 
                // Streamlit renders asynchronously after reruns,
                // so retry briefly until the anchor is available.
                const timer = setInterval(function() {{
                    attempts++;
 
                    if (
                        scrollToSATARKInput() ||
                        attempts >= 20
                    ) {{
                        clearInterval(timer);
                    }}
                }}, 100);
            }})();
            </script>
            """,
            height=0,
        )
 
        # Mark this trigger as handled. The next scanner click
        # creates a new trigger and therefore scrolls again.
        st.session_state.handled_scroll_to_input_trigger = (
            scroll_trigger
        )
 
 
    # ==========================================================
    # SECURITY ANALYSIS INPUT
    # ==========================================================
 
    st.markdown(
        f'<div class="section-title">🔎 Security Analysis</div>'
        f'<div class="section-copy">Selected: <strong>{mode}</strong></div>',
        unsafe_allow_html=True
    )
 
    uploaded = None
    image_data_urls = []
    video_file = None
    transcribe_audio = True
 
 
    # ==========================================================
    # TEXT
    # ==========================================================
 
    if mode == "Text":
 
        content = st.text_area(
            "Enter content",
            height=230,
            placeholder=(
                "Paste any message, post, SMS, "
                "social-media content or suspicious text here..."
            ),
            key=f"text_input_{mode}"
        )
 
 
    # ==========================================================
    # URL
    # ==========================================================
 
    elif mode == "URL":
 
        content = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            key="url_input"
        )
 
 
    # ==========================================================
    # PDF
    # ==========================================================
 
    elif mode == "PDF":
 
        uploaded = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            help="Best results come from text-based PDFs.",
            key="pdf_input"
        )
 
        content = ""
 
 
    # ==========================================================
    # VIDEO
    # ==========================================================
 
    elif mode == "Video":
 
        video_file = st.file_uploader(
            "Upload video",
            type=[
                "mp4",
                "mov",
                "avi",
                "webm",
                "mkv",
                "m4v"
            ],
            accept_multiple_files=False,
            help=(
                "SATARK extracts a handful of representative "
                "frames and, when possible, transcribes the audio. "
                "Max 200 MB."
            ),
            key="video_input"
        )
 
        transcribe_audio = st.checkbox(
            "Also transcribe and analyze the audio track "
            "(recommended for voice-call/scam-call videos)",
            value=True,
            key="video_transcribe_toggle"
        )
 
        content = (
            "Analyze the sampled video frames "
            "(and transcript, if provided) together "
            "as one investigation."
        )
 
        if video_file is not None:
            st.video(video_file)
 
        uploaded = None
 
 
    # ==========================================================
    # IMAGE / QR
    # ==========================================================
 
    else:
 
        uploaded = st.file_uploader(
            "Upload image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            accept_multiple_files=True,
            help=(
                "Upload one or more screenshots, QR images, "
                "email screenshots or suspicious images. "
                "SATARK will analyze the selected images together."
            ),
            key=f"image_input_{mode}"
        )
 
        content = (
            "Analyze all supplied images together. "
            "Inspect visible text, links, logos, QR-related content, "
            "suspicious instructions, impersonation and "
            "social-engineering signals, and cross-image evidence."
        )
 
        if uploaded and len(uploaded) > 5:
 
            st.info(
                "SATARK will analyze the first 5 selected images "
                "together to keep the request reliable."
            )
 
 
    # ==========================================================
    # INPUT FINGERPRINT
    # ==========================================================
 
    if mode in {"Image", "QR"}:
 
        current_input_fingerprint = uploaded_fingerprint(uploaded)
 
    elif mode == "Video":
 
        current_input_fingerprint = single_file_fingerprint(
            video_file
        )
 
    else:
 
        current_input_fingerprint = ""
 
 
    if (
        mode in {"Image", "QR", "Video"}
        and current_input_fingerprint
        != st.session_state.get(
            "last_input_fingerprint",
            ""
        )
    ):
 
        st.session_state.last_input_fingerprint = (
            current_input_fingerprint
        )
 
        if current_input_fingerprint:
 
            st.session_state.result = None
 
 
    # ==========================================================
    # ANALYZE BUTTON
    # ==========================================================
 
    st.markdown(
        '<div class="analyze">',
        unsafe_allow_html=True
    )
 
    analyze_clicked = st.button(
        "🔍 Analyze with SATARK",
        use_container_width=True,
        type="primary",
        key="analyze_button"
    )
 
    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )
 
 
    # ==========================================================
    # RUN ANALYSIS
    # ==========================================================
 
    if analyze_clicked:
 
        if not safe_text(api_key):
 
            st.error(
                "🔑 Enter your Groq API key in the sidebar first."
            )
 
            st.stop()
 
 
        try:
 
            # Fresh request ID for every analysis
            st.session_state.analysis_request_id = (
                hashlib.sha256(
                    f"{datetime.now().isoformat()}|{mode}"
                    .encode("utf-8")
                ).hexdigest()[:16]
            )
 
            st.session_state.result = None
            st.session_state.vision_model = None
 
            client = get_client(api_key)
 
            st.markdown(
                '<div class="analysis-loader" '
                'aria-label="SATARK is analyzing">'
                '<span></span></div>',
                unsafe_allow_html=True
            )
 
 
            with st.spinner(
                "SATARK is reading the content, "
                "evaluating threat patterns and "
                "building your report…"
            ):
 
                available = discover_models(client)
 
                st.session_state.available_models = available
 
 
                # ==================================================
                # PREPARE INPUT
                # ==================================================
 
                if mode == "Text":
 
                    if not safe_text(content):
 
                        raise ValueError(
                            "Please enter some content to analyze."
                        )
 
                    prepared = content[:50000]
 
 
                elif mode == "URL":
 
                    if not safe_text(content):
 
                        raise ValueError(
                            "Please enter a URL."
                        )
 
                    prepared = fetch_url_text(content)
 
                    if not prepared.strip():
 
                        raise ValueError(
                            "The URL returned no readable content."
                        )
 
 
                elif mode == "PDF":
 
                    if uploaded is None:
 
                        raise ValueError(
                            "Please upload a PDF."
                        )
 
                    prepared = extract_pdf_text(uploaded)
 
 
                elif mode == "Video":
 
                    if video_file is None:
 
                        raise ValueError(
                            "Please upload a video."
                        )
 
 
                    if not _video_dependencies_available():
 
                        raise RuntimeError(
                            "Video analysis needs OpenCV installed "
                            "in this environment "
                            "(pip install opencv-python-headless "
                            "--break-system-packages), then restart "
                            "the app."
                        )
 
 
                    # ----------------------------------------------
                    # Extract representative frames
                    # ----------------------------------------------
 
                    frames, duration, warnings = (
                        extract_video_frames(video_file)
                    )
 
                    image_data_urls = (
                        pil_frames_to_data_urls(frames)
                    )
 
 
                    if not image_data_urls:
 
                        raise ValueError(
                            "SATARK could not extract usable "
                            "frames from this video."
                        )
 
 
                    if warnings:
 
                        st.warning(
                            "⚠️ " + " ".join(warnings)
                        )
 
 
                    # ----------------------------------------------
                    # Audio transcription
                    # ----------------------------------------------
 
                    transcript = ""
 
                    if transcribe_audio:
 
                        transcript = transcribe_video_audio(
                            video_file,
                            client
                        )
 
 
                    duration_note = (
                        f"Approx. duration: "
                        f"{duration:.1f} seconds. "
                        if duration
                        else ""
                    )
 
 
                    transcript_note = (
 
                        f"Audio transcript:\n{transcript}"
 
                        if transcript
 
                        else
                        "Audio transcript: not available "
                        "(silent, unsupported audio, or "
                        "transcription unavailable in this "
                        "environment)."
                    )
 
 
                    prepared = (
                        f"{content}\n"
                        f"{duration_note}"
                        f"Number of sampled frames: "
                        f"{len(image_data_urls)}.\n\n"
                        f"{transcript_note}"
                    )
 
 
                else:
 
                    if not uploaded:
 
                        raise ValueError(
                            "Please upload at least one image."
                        )
 
 
                    # ----------------------------------------------
                    # Fresh image conversion
                    # ----------------------------------------------
 
                    image_data_urls = (
                        images_to_data_urls(
                            uploaded[:5],
                            max_images=5
                        )
                    )
 
 
                    if not image_data_urls:
 
                        raise ValueError(
                            "The selected image(s) "
                            "could not be read."
                        )
 
 
                    prepared = (
                        f"{content}\n"
                        f"Number of images in this "
                        f"investigation: "
                        f"{len(image_data_urls)}"
                    )
 
 
                # ==================================================
                # BUILD PROMPT
                # ==================================================
 
                prompt = (
                    f"User profile: {role}\n"
                    f"Scanner mode: {mode}\n\n"
                    f"{prepared}"
                )
 
 
                # ==================================================
                # GROQ ANALYSIS
                # ==================================================
 
                result = analyze_with_groq(
                    client,
                    prompt,
                    mode,
                    role,
                    image_data_urls,
                    available
                )
 
 
            # ======================================================
            # SAVE RESULT
            # ======================================================
 
            st.session_state.result = result
 
            add_history(
                result,
                mode
            )
 
            st.session_state.page = "Analyze"
 
            st.success(
                "SATARK analysis complete."
            )
 
 
        except (ValueError, RuntimeError) as exc:
 
            st.error(
                f"⚠️ {exc}"
            )
 
 
        except (HTTPError, URLError) as exc:
 
            st.error(
                f"⚠️ Could not fetch that URL safely: {exc}"
            )
 
 
        except Exception as exc:
 
            st.error(
                "⚠️ SATARK could not complete the analysis. "
                "Check your API key, internet connection, "
                "input and model access."
            )
 
            with st.expander(
                "Technical details"
            ):
 
                st.code(
                    str(exc)
                )
 
 
    # ==========================================================
    # RESULT
    # ==========================================================
 
    if st.session_state.result:
 
        render_result(
            st.session_state.result
        )
 
        st.download_button(
            "📄 Download PDF report",
            make_pdf_report(
                st.session_state.result,
                mode
            ),
            file_name="SATARK_security_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
 
 
# ==============================================================
# HISTORY
# ==============================================================
 
elif st.session_state.page == "History":
 
    st.markdown(
        '<div class="section-title">🕘 Scan History</div>'
        '<div class="section-copy">'
        'Session-only history. Original submitted content is not '
        'stored here; only analysis results and metadata are retained.'
        '</div>',
        unsafe_allow_html=True
    )
 
    if st.session_state.history:
 
        if st.button(
            "Clear session history",
            key="clear_history"
        ):
 
            st.session_state.history = []
            st.session_state.result = None
            st.rerun()
 
 
        for i, entry in enumerate(
            st.session_state.history
        ):
 
            score = entry["score"]
 
            label, css = risk_label(
                score,
                entry.get("category", "")
            )
 
 
            with st.expander(
                f"{entry['mode']} • "
                f"{entry['category']} • "
                f"{score}/100 • "
                f"{entry['time']}"
            ):
 
                st.markdown(
                    f'<span class="badge">{label}</span> '
                    f'<span class="badge">'
                    f'{html.escape(entry["category"])}'
                    f'</span>',
                    unsafe_allow_html=True
                )
 
                st.write(
                    entry["verdict"]
                )
 
 
                c1, c2 = st.columns(2)
 
 
                with c1:
 
                    if st.button(
                        "Open result",
                        key=f"history_open_{i}"
                    ):
 
                        st.session_state.result = (
                            entry["result"]
                        )
 
                        st.session_state.mode = (
                            entry["mode"]
                        )
 
                        st.session_state.page = (
                            "Analyze"
                        )
 
                        st.rerun()
 
 
                with c2:
 
                    st.download_button(
                        "📄 Export PDF",
                        make_pdf_report(
                            entry["result"],
                            entry["mode"]
                        ),
                        file_name=(
                            f"SATARK_report_{i+1}.pdf"
                        ),
                        mime="application/pdf",
                        key=f"history_dl_{i}"
                    )
 
    else:
 
        st.info(
            "No scans yet. Analyze something suspicious "
            "and it will appear here for this session."
        )
 
 
# ==============================================================
# SCAM CHALLENGE
# ==============================================================
 
elif st.session_state.page == "Challenge":
 
    st.markdown(
        '<div class="section-title">🎯 Scam Challenge</div>'
        '<div class="section-copy">'
        'Can you spot the scam before SATARK does? '
        'Great for students and classroom practice.'
        '</div>',
        unsafe_allow_html=True
    )
 
 
    questions = [
 
        {
            "q":
                "“URGENT: Your bank account will be blocked today. "
                "Verify immediately at this link.” "
                "What is the strongest warning sign?",
 
            "options": [
                "Urgency + account threat",
                "A normal greeting",
                "A long message",
                "A company logo"
            ],
 
            "answer": 0,
 
            "why":
                "Attackers often create panic so you act before "
                "verifying. Urgency plus an account threat is a "
                "classic social-engineering pattern."
        },
 
 
        {
            "q":
                "A message says you won ₹50,000 and asks for a "
                "small ‘processing fee’. What should you suspect first?",
 
            "options": [
                "Reward/payment scam",
                "Normal banking",
                "Software update",
                "School notice"
            ],
 
            "answer": 0,
 
            "why":
                "Unexpected prizes combined with a payment request "
                "are a common fraud pattern."
        },
 
 
        {
            "q":
                "A login link says it is from a familiar service, "
                "but the domain is misspelled. What is the key clue?",
 
            "options": [
                "Brand impersonation",
                "Good website design",
                "HTTPS alone",
                "A short message"
            ],
 
            "answer": 0,
 
            "why":
                "Look at the actual domain, not just the logo or "
                "page appearance. Impersonation domains are frequently "
                "used for credential theft."
        },
 
 
        {
            "q":
                "Someone asks for your OTP because they claim to "
                "be ‘support’. What is the safest response?",
 
            "options": [
                "Share it quickly",
                "Never share the OTP; verify independently",
                "Send a screenshot",
                "Ask for their password"
            ],
 
            "answer": 1,
 
            "why":
                "Legitimate services should not require you to disclose "
                "one-time passwords to an unsolicited caller or message "
                "sender."
        }
 
    ]
 
 
    q = questions[
        st.session_state.challenge_index
        % len(questions)
    ]
 
 
    st.markdown(
        '<div class="challenge-card">',
        unsafe_allow_html=True
    )
 
 
    st.markdown(
        f'''
        <div class="badge">
            Question
            {(st.session_state.challenge_index % len(questions)) + 1}
            / {len(questions)}
        </div>
 
        <div class="challenge-q"
             style="margin-top:14px">
            {q["q"]}
        </div>
        ''',
        unsafe_allow_html=True
    )
 
 
    cols = st.columns(2)
 
 
    for idx, opt in enumerate(
        q["options"]
    ):
 
        with cols[idx % 2]:
 
            if st.button(
                opt,
                key=(
                    f"challenge_opt_"
                    f"{st.session_state.challenge_index}_"
                    f"{idx}"
                ),
                use_container_width=True
            ):
 
                if not st.session_state.challenge_answered:
 
                    if idx == q["answer"]:
 
                        st.session_state.challenge_score += 1
 
                        st.success(
                            "Correct! 🎉"
                        )
 
                    else:
 
                        st.warning(
                            "Not quite. Here's the pattern to remember."
                        )
 
                    st.session_state.challenge_answered = True
 
                    st.rerun()
 
 
    if st.session_state.challenge_answered:
 
        st.markdown(
            f'''
            <div class="challenge-answer">
                <strong>Why:</strong> {q["why"]}
            </div>
            ''',
            unsafe_allow_html=True
        )
 
 
        st.write(
            f"Score: **"
            f"{st.session_state.challenge_score}/"
            f"{(st.session_state.challenge_index % len(questions)) + 1}"
            f"**"
        )
 
 
        if st.button(
            "Next challenge",
            key="next_challenge",
            type="primary"
        ):
 
            st.session_state.challenge_index += 1
            st.session_state.challenge_answered = False
            st.rerun()
 
 
    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )
 
 
    if st.button(
        "Reset challenge score",
        key="reset_challenge"
    ):
 
        st.session_state.challenge_index = 0
        st.session_state.challenge_score = 0
        st.session_state.challenge_answered = False
        st.rerun()
 
 
# ==============================================================
# SATARK ACADEMY
# ==============================================================
 
elif st.session_state.page == "Academy":
 
    st.markdown(
        '<div class="section-title">🎓 SATARK Academy</div>'
        '<div class="section-copy">'
        'Learn the patterns behind the scams instead of relying '
        'on AI forever.'
        '</div>',
        unsafe_allow_html=True
    )
 
 
    lessons = [
 
        (
            "🎣",
            "Phishing",
            "Fake messages and pages designed to steal "
            "credentials or information."
        ),
 
        (
            "⏰",
            "Urgency manipulation",
            "Pressure tactics that make you act before you verify."
        ),
 
        (
            "👤",
            "Impersonation",
            "Attackers pretending to be banks, schools, "
            "companies, friends or officials."
        ),
 
        (
            "🔗",
            "Suspicious links",
            "Look-alike domains, strange paths, redirects "
            "and unexpected login pages."
        ),
 
        (
            "💳",
            "Payment fraud",
            "Fake fees, refunds, prizes, QR payments "
            "and requests for money."
        ),
 
        (
            "🔐",
            "Account takeover",
            "Attempts to obtain passwords, OTPs, recovery "
            "codes or session access."
        )
 
    ]
 
 
    cols = st.columns(3)
 
 
    for i, (icon, title, copy) in enumerate(
        lessons
    ):
 
        with cols[i % 3]:
 
            st.markdown(
                f'''
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-copy">{copy}</div>
                </div>
                ''',
                unsafe_allow_html=True
            )
 
 
    st.markdown(
        "### A simple rule to remember"
    )
 
 
    st.info(
        "STOP → VERIFY → ACT. If a message creates pressure, "
        "asks for secrets, or requests money, pause and verify "
        "through an independent official channel."
    )
 
 
# ==============================================================
# CLASSROOM
# ==============================================================
 
elif st.session_state.page == "Classroom":
 
    st.markdown(
        '<div class="section-title">👨‍🏫 Classroom Mode</div>'
        '<div class="section-copy">'
        'A simple teacher-facing view for using SATARK '
        'as a cyber-safety learning tool.'
        '</div>',
        unsafe_allow_html=True
    )
 
 
    history = st.session_state.history
 
    total = len(history)
 
    avg = (
        round(
            sum(x["score"] for x in history) / total
        )
        if total
        else 0
    )
 
    high = sum(
        1
        for x in history
        if x["score"] >= 70
    )
 
 
    a, b, c = st.columns(3)
 
 
    with a:
 
        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    Scans this session
                </div>
                <div class="metric-value">
                    {total}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
 
 
    with b:
 
        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    Average risk
                </div>
                <div class="metric-value">
                    {avg}/100
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
 
 
    with c:
 
        st.markdown(
            f'''
            <div class="metric">
                <div class="metric-label">
                    High-risk findings
                </div>
                <div class="metric-value critical">
                    {high}
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
 
 
    st.markdown(
        "### Suggested classroom flow"
    )
 
 
    st.markdown(
        "**1.** Give students a suspicious message.  "
        "**2.** Ask them to identify warning signs.  "
        "**3.** Run it through SATARK.  "
        "**4.** Compare the evidence.  "
        "**5.** Use Scam Challenge to reinforce the lesson."
    )
 
 
    st.markdown(
        "### Common patterns in this session"
    )
 
 
    counts = {}
 
 
    for item in history:
 
        key = item["category"]
 
        counts[key] = counts.get(key, 0) + 1
 
 
    if counts:
 
        for k, v in sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):
 
            st.write(
                f"• **{k}** — {v} scan(s)"
            )
 
    else:
 
        st.info(
            "Run a few example scans to populate "
            "classroom statistics."
        )
 
 
# ==============================================================
# FOOTER
# ==============================================================
 
st.markdown(
    '<div class="footer">'
    'SATARK • Smart AI Threat Analysis & Risk Knowledge<br>'
    'AI analysis is advisory. Always verify high-impact security '
    'decisions independently.<br>'
    'Session history is temporary and does not intentionally '
    'preserve submitted source content.'
    '</div>',
    unsafe_allow_html=True
)
 