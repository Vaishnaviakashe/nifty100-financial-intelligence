
"""Main entry point for the NIFTY 100 Financial Intelligence Dashboard."""

import sys
from pathlib import Path

import streamlit as st


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# --------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="NIFTY 100 | Financial Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# GLOBAL DESIGN SYSTEM
# --------------------------------------------------

NAVY = "#123B69"
DARK_NAVY = "#0D2F54"
ORANGE = "#F28C28"
WHITE = "#FFFFFF"
LIGHT_GREY = "#F5F7FA"
BORDER = "#DCE4ED"
TEXT = "#18324F"
MUTED = "#718096"


# --------------------------------------------------
# GLOBAL CSS
# --------------------------------------------------

st.markdown("""
<style>

/* Typography */
html, body, [class*="css"], [data-testid="stMarkdownContainer"] {
    font-family: "Times New Roman", Times, serif !important;
}

/* Main workspace */
.stApp {
    background: #F7F9FC;
    color: #18324F;
}

[data-testid="stAppViewContainer"] {
    background: #F7F9FC;
}

[data-testid="stHeader"] {
    background: rgba(247, 249, 252, 0.95);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #0B2342 0%,
        #123B69 55%,
        #174878 100%
    );
    border-right: 2px solid #F28C28;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

/* Navigation */
[data-testid="stSidebarNav"] a {
    border-radius: 9px;
    margin: 5px 8px;
    padding: 9px 12px;
    transition: all 0.25s ease;
}

/* Hover */
[data-testid="stSidebarNav"] a:hover {
    background: #F28C28 !important;
    transform: translateX(4px);
    box-shadow: 0 3px 12px rgba(242, 140, 40, 0.3);
}

/* Active navigation */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #F28C28 !important;
    color: #FFFFFF !important;
    font-weight: bold;
    box-shadow: 0 3px 14px rgba(242, 140, 40, 0.25);
}

/* Headings */
h1, h2, h3 {
    color: #123B69 !important;
    font-family: "Times New Roman", Times, serif !important;
    letter-spacing: 0.2px;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E0E8F1;
    border-left: 4px solid #123B69;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 4px 14px rgba(18, 59, 105, 0.07);
    transition: all 0.25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(18, 59, 105, 0.12);
}

[data-testid="stMetricValue"] {
    color: #123B69;
    font-weight: bold;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    background: #123B69;
    color: white;
    border: 1px solid #123B69;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: #F28C28;
    border-color: #F28C28;
    color: white;
    box-shadow: 0 4px 12px rgba(242, 140, 40, 0.25);
}

/* Input fields */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    border-radius: 9px;
    border-color: #DCE4ED;
}

/* Containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
    border-color: #E0E8F1;
    box-shadow: 0 3px 12px rgba(18, 59, 105, 0.04);
}

/* Dividers */
hr {
    border-color: #DCE4ED;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR BRANDING
# --------------------------------------------------

st.sidebar.title("📊 NIFTY 100 Analytics")
st.sidebar.caption("Financial Intelligence Platform")
st.sidebar.divider()


# --------------------------------------------------
# PAGE NAVIGATION
# --------------------------------------------------

pages = [
    st.Page(
        ROOT_DIR / "pages" / "01_home.py",
        title="Home",
        icon="🏠",
        default=True,
    ),
    st.Page(
        ROOT_DIR / "pages" / "02_profile.py",
        title="Company Profile",
        icon="🏢",
    ),
    st.Page(
        ROOT_DIR / "pages" / "03_screener.py",
        title="Financial Screener",
        icon="🔎",
    ),
    st.Page(
        ROOT_DIR / "pages" / "04_peers.py",
        title="Peer Comparison",
        icon="⚖️",
    ),
    st.Page(
        ROOT_DIR / "pages" / "05_trends.py",
        title="Trend Analysis",
        icon="📈",
    ),
    st.Page(
        ROOT_DIR / "pages" / "06_sectors.py",
        title="Sector Analysis",
        icon="🏭",
    ),
    st.Page(
        ROOT_DIR / "pages" / "07_capital.py",
        title="Capital Allocation",
        icon="💰",
    ),
    st.Page(
        ROOT_DIR / "pages" / "08_reports.py",
        title="Annual Reports",
        icon="📄",
    ),
]

navigation = st.navigation(pages, position="sidebar")
navigation.run()
