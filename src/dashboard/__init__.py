
# """Main entry point for the NIFTY 100 Financial Intelligence Dashboard."""

# import sys
# from pathlib import Path

# import streamlit as st


# # Ensure the project root is available for imports.
# ROOT_DIR = Path(__file__).resolve().parents[2]
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))


# st.set_page_config(
#     page_title="Nifty 100 Analytics",
#     page_icon="📊",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )


# st.sidebar.title("📊 NIFTY 100 Analytics")
# st.sidebar.caption("Financial Intelligence Platform")
# st.sidebar.divider()

# pages = [
#     st.Page(
#         "pages/01_home.py",
#         title="Home",
#         icon="🏠",
#         default=True,
#     ),
#     st.Page(
#         "pages/02_profile.py",
#         title="Company Profile",
#         icon="🏢",
#     ),
#     st.Page(
#         "pages/03_screener.py",
#         title="Financial Screener",
#         icon="🔎",
#     ),
#     st.Page(
#         "pages/04_peers.py",
#         title="Peer Comparison",
#         icon="⚖️",
#     ),
#     st.Page(
#         "pages/05_trends.py",
#         title="Trend Analysis",
#         icon="📈",
#     ),
#     st.Page(
#         "pages/06_sectors.py",
#         title="Sector Analysis",
#         icon="🏭",
#     ),
#     st.Page(
#         "pages/07_capital.py",
#         title="Capital Allocation",
#         icon="💰",
#     ),
#     st.Page(
#         "pages/08_reports.py",
#         title="Annual Reports",
#         icon="📄",
#     ),
# ]

# navigation = st.navigation(pages, position="sidebar")

# navigation.run()
