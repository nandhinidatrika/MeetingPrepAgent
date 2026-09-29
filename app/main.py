"""Main Streamlit Application entry point for Meeting Prep Agent."""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for Streamlit execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.config import get_settings
from app.database import db
from app.services.groq_service import get_groq_service
from app.services.hindsight_service import get_hindsight_service
from app.services.meeting_service import get_meeting_service
from app.ui.clients import render_clients
from app.ui.dashboard import render_dashboard
from app.ui.demo_walkthrough import render_demo_walkthrough
from app.ui.memory_explorer import render_memory_explorer
from app.ui.meeting_prep import render_meeting_prep
from app.ui.post_meeting import render_post_meeting
from app.ui.styles import apply_custom_css

# Page configuration
st.set_page_config(
    page_title="Meeting Prep Agent — Hindsight & Groq",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
db.init_db()

# Apply CSS styling
apply_custom_css()


def main():
    """Application main loop and routing."""
    settings = get_settings()
    hindsight = get_hindsight_service()
    groq = get_groq_service()
    meeting_service = get_meeting_service()

    # --------------------------------------------------------------------------
    # Sidebar Navigation & Settings
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("## 🎯 Meeting Prep Agent")
        st.caption("AI Assistant with Hindsight Long-Term Memory & Groq Reasoning")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        pages = [
            "📊 Dashboard",
            "🧠 Meeting Preparation",
            "📝 Post-Meeting Memory",
            "🔍 Memory Explorer",
            "👥 Clients & Contacts",
            "🚀 Demo Walkthrough (Story Mode)",
        ]

        # Sync with session state if set by buttons
        current_page_idx = 0
        if "selected_page" in st.session_state:
            for i, p in enumerate(pages):
                if st.session_state["selected_page"] in p:
                    current_page_idx = i
                    break

        selected_page = st.radio("Navigation", pages, index=current_page_idx, key="nav_radio")
        st.session_state["selected_page"] = selected_page

        st.markdown("---")

        # ----------------------------------------------------------------------
        # Live Connection Indicators
        # ----------------------------------------------------------------------
        st.markdown("#### ⚡ System Status")
        h_ok, h_msg = hindsight.ping()
        g_ok, g_msg = groq.ping()

        if h_ok:
            st.success(f"🧠 Hindsight Cloud: Active")
        else:
            st.warning(f"🧠 Hindsight: Key Needed")

        if g_ok:
            st.success(f"⚡ Groq LLM: Ready")
        else:
            st.warning(f"⚡ Groq: Key Needed")

        # Quick API Key Configuration
        with st.expander("⚙️ API Configuration", expanded=False):
            groq_key_input = st.text_input(
                "Groq API Key",
                value=settings.groq_api_key if settings.has_groq_key else "",
                type="password",
                placeholder="gsk_...",
                help="Get key at console.groq.com",
            )
            hindsight_key_input = st.text_input(
                "Hindsight API Key",
                value=settings.hindsight_api_key if settings.has_hindsight_key else "",
                type="password",
                placeholder="Key from Hindsight Cloud",
                help="Get key at hindsight.vectorize.io",
            )
            bank_id_input = st.text_input(
                "Hindsight Bank ID",
                value=settings.hindsight_bank_id,
            )

            if st.button("Apply API Keys", use_container_width=True):
                if groq_key_input:
                    os.environ["GROQ_API_KEY"] = groq_key_input
                if hindsight_key_input:
                    os.environ["HINDSIGHT_API_KEY"] = hindsight_key_input
                if bank_id_input:
                    os.environ["HINDSIGHT_BANK_ID"] = bank_id_input
                
                settings.reload()
                hindsight._init_client()
                groq._init_client()
                st.toast("Configuration updated!")
                st.rerun()

        st.markdown("---")

        # Demo Reset / Seed shortcuts
        st.markdown("#### 🛠️ Quick Actions")
        if st.button("🌱 Seed ABC Tech Demo", use_container_width=True):
            with st.spinner("Seeding demo scenario..."):
                res = meeting_service.seed_demo_scenario(retain_to_hindsight=True)
                st.toast(f"Demo seeded ({res['total_retained']} memories in Hindsight)!")
                st.rerun()

        if st.button("🗑️ Reset Local Database", use_container_width=True, type="secondary"):
            db.reset_db()
            st.toast("Local database reset.")
            st.rerun()

        st.caption("v1.0.0 • Hackathon Prototype")

    # --------------------------------------------------------------------------
    # Screen Routing
    # --------------------------------------------------------------------------
    if "Dashboard" in selected_page:
        render_dashboard()
    elif "Meeting Preparation" in selected_page:
        render_meeting_prep()
    elif "Post-Meeting" in selected_page:
        render_post_meeting()
    elif "Memory Explorer" in selected_page:
        render_memory_explorer()
    elif "Clients & Contacts" in selected_page:
        render_clients()
    elif "Demo Walkthrough" in selected_page:
        render_demo_walkthrough()


if __name__ == "__main__":
    main()
