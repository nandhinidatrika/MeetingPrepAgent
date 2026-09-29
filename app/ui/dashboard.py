"""Dashboard view for Meeting Prep Agent."""
from datetime import datetime
import streamlit as st

from app.database import db
from app.services.meeting_service import get_meeting_service
from app.utils.helpers import format_date_human


def render_dashboard():
    """Render the main executive dashboard."""
    meeting_service = get_meeting_service()
    stats = meeting_service.get_dashboard_stats()

    # --------------------------------------------------------------------------
    # Header & System Status
    # --------------------------------------------------------------------------
    col_title, col_status = st.columns([3, 2])
    with col_title:
        st.title("🎯 Meeting Prep Agent")
        st.caption("AI-powered meeting preparation with persistent long-term memory via Hindsight Cloud & Groq.")

    with col_status:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        h_ok = stats["hindsight_status"]["ok"]
        g_ok = stats["groq_status"]["ok"]

        st.markdown(
            f"""
            <div style="display: flex; gap: 10px; justify-content: flex-end; align-items: center;">
                <span class="status-badge {'status-connected' if h_ok else 'status-disconnected'}">
                    🧠 Hindsight: {'Connected' if h_ok else 'Key Required'}
                </span>
                <span class="status-badge {'status-connected' if g_ok else 'status-disconnected'}">
                    ⚡ Groq: {'Ready' if g_ok else 'Key Required'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # If keys are missing, show quick setup guide
    if not h_ok or not g_ok:
        with st.expander("🔑 API Setup & Configuration Guide", expanded=False):
            st.info(
                """
                **To enable full persistent memory and AI brief generation:**
                1. Copy `.env.example` to `.env` in the project root.
                2. Set your `GROQ_API_KEY` (Get from [Groq Console](https://console.groq.com/keys)).
                3. Set your `HINDSIGHT_API_KEY` and `HINDSIGHT_BANK_ID` (From [Hindsight Cloud](https://hindsight.vectorize.io)).
                4. Restart or refresh the application.
                """
            )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # Metric Cards
    # --------------------------------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">👥 Total Clients</div>
                <div class="metric-value">{stats['total_clients']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Active client relationships</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">📅 Total Meetings</div>
                <div class="metric-value">{stats['total_meetings']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{stats['upcoming_meetings']} upcoming • {stats['completed_meetings']} completed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">📋 Prepared Briefs</div>
                <div class="metric-value">{stats['prepared_briefs']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">AI synthesis generated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">⏳ Pending Follow-ups</div>
                <div class="metric-value">{stats['pending_followups_count']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">Action items awaiting review</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Quick Demo Callout
    # --------------------------------------------------------------------------
    with st.container():
        demo_col1, demo_col2 = st.columns([3, 1])
        with demo_col1:
            st.markdown(
                """
                **🚀 Interactive Hackathon Demo Scenario: ABC Technologies**  
                Experience how Hindsight evolves memory across Meeting 1 (initial requirements), Meeting 2 (scope changes & auth blockers), and Meeting 3 (synthesis of old + new context).
                """
            )
        with demo_col2:
            if st.button("🌱 Seed Demo Scenario", use_container_width=True, type="primary"):
                with st.spinner("Seeding ABC Technologies scenario & populating Hindsight memory..."):
                    result = meeting_service.seed_demo_scenario(retain_to_hindsight=True)
                    st.success(f"Seeded 3-meeting evolution scenario! ({result['total_retained']} memories stored in Hindsight)")
                    st.rerun()

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Main Content Columns: Upcoming Meetings & Follow-ups
    # --------------------------------------------------------------------------
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📅 Meetings Schedule")
        meetings = stats["recent_meetings"]

        if not meetings:
            st.info("No meetings found. Click 'Seed Demo Scenario' above or create a new meeting in the sidebar.")
        else:
            for m in meetings:
                client = db.get_client_by_id(m.client_id)
                client_name = client.name if client else "Unknown Client"
                org_str = f" ({client.organization})" if client and client.organization else ""

                status_color = "#3b82f6" if m.status == "upcoming" else ("#10b981" if m.status == "completed" else "#8b5cf6")
                status_label = m.status.upper()

                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <div style="font-weight: 600; font-size: 1.05rem; color: #f8fafc;">{m.title}</div>
                                    <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 3px;">
                                        👤 <b>{client_name}</b>{org_str} &nbsp;|&nbsp; 🗓️ {format_date_human(m.meeting_date)} at {m.meeting_time}
                                    </div>
                                    <div style="color: #cbd5e1; font-size: 0.85rem; margin-top: 5px;">
                                        📌 <i>{m.topic or 'General Alignment'}</i>
                                    </div>
                                </div>
                                <span style="background: {status_color}22; color: {status_color}; border: 1px solid {status_color}55; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;">
                                    {status_label}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    btn_c1, btn_c2 = st.columns([1, 1])
                    with btn_c1:
                        if st.button(f"🧠 Prepare Meeting", key=f"prep_{m.id}", use_container_width=True):
                            st.session_state["selected_page"] = "Meeting Preparation"
                            st.session_state["prep_client_id"] = m.client_id
                            st.session_state["prep_meeting_id"] = m.id
                            st.rerun()
                    with btn_c2:
                        if st.button(f"📝 Record Notes", key=f"note_{m.id}", use_container_width=True):
                            st.session_state["selected_page"] = "Post-Meeting Memory"
                            st.session_state["post_client_id"] = m.client_id
                            st.session_state["post_meeting_id"] = m.id
                            st.rerun()

    with col_right:
        st.subheader("📌 Pending Follow-ups")
        follow_ups = stats["pending_followups"]

        if not follow_ups:
            st.success("🎉 All follow-up tasks are completed!")
        else:
            for fu in follow_ups:
                client = db.get_client_by_id(fu.client_id)
                client_name = client.name if client else ""
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 0.75rem; margin-bottom: 0.6rem;">
                            <div style="font-size: 0.9rem; color: #f8fafc; font-weight: 500;">{fu.task}</div>
                            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                                👤 Client: {client_name} &nbsp;|&nbsp; 🗓️ Due: {format_date_human(fu.due_date)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("Mark Completed", key=f"fu_{fu.id}", use_container_width=True):
                        db.toggle_follow_up_status(fu.id, completed=True)
                        st.toast("Follow-up marked as completed!")
                        st.rerun()

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.subheader("⚡ Recent Activity")
        recent_actions = stats["recent_actions"]
        if recent_actions:
            for act in recent_actions[:5]:
                act_icon = "🧠" if act.action_type == "retain" else ("🔍" if act.action_type == "recall" else "📋")
                st.markdown(
                    f"""
                    <div style="font-size: 0.8rem; color: #cbd5e1; border-bottom: 1px solid #1e293b; padding: 5px 0;">
                        {act_icon} {act.summary}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
