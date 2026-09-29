"""Meeting Preparation UI view for Meeting Prep Agent."""
import streamlit as st

from app.database import db
from app.models.schemas import MeetingBrief, RecalledMemoryItem
from app.services.meeting_service import get_meeting_service
from app.utils.helpers import format_date_human


def render_meeting_prep():
    """Render the Meeting Preparation screen."""
    meeting_service = get_meeting_service()
    st.title("🧠 AI Meeting Preparation")
    st.caption("Recall persistent memories from Hindsight Cloud and synthesize personalized meeting briefs with Groq.")

    clients = db.get_all_clients()
    if not clients:
        st.warning("No clients found in the database. Please create a client or seed the demo scenario.")
        if st.button("🌱 Seed Demo Scenario"):
            meeting_service.seed_demo_scenario(retain_to_hindsight=True)
            st.rerun()
        return

    # --------------------------------------------------------------------------
    # Client & Meeting Selection
    # --------------------------------------------------------------------------
    col1, col2 = st.columns([1, 1])

    # Client selection
    client_names = [f"{c.name} ({c.organization})" if c.organization else c.name for c in clients]
    client_ids = [c.id for c in clients]

    default_client_idx = 0
    if "prep_client_id" in st.session_state and st.session_state["prep_client_id"] in client_ids:
        default_client_idx = client_ids.index(st.session_state["prep_client_id"])

    with col1:
        selected_client_idx = st.selectbox(
            "👤 Select Client / Contact",
            range(len(clients)),
            format_func=lambda i: client_names[i],
            index=default_client_idx,
            key="prep_client_select",
        )
        selected_client = clients[selected_client_idx]
        st.session_state["prep_client_id"] = selected_client.id

    # Meeting selection for chosen client
    client_meetings = db.get_meetings_by_client(selected_client.id)

    with col2:
        meeting_options = ["➕ Create New Meeting for Preparation"] + [
            f"{m.title} ({format_date_human(m.meeting_date)}) [{m.status.upper()}]" for m in client_meetings
        ]
        
        default_meeting_idx = 0
        if "prep_meeting_id" in st.session_state:
            for idx, m in enumerate(client_meetings):
                if m.id == st.session_state["prep_meeting_id"]:
                    default_meeting_idx = idx + 1
                    break

        selected_meeting_opt_idx = st.selectbox(
            "📅 Select Meeting",
            range(len(meeting_options)),
            format_func=lambda i: meeting_options[i],
            index=default_meeting_idx,
            key="prep_meeting_select",
        )

    # --------------------------------------------------------------------------
    # Meeting Details / Form
    # --------------------------------------------------------------------------
    is_new_meeting = selected_meeting_opt_idx == 0
    
    if is_new_meeting:
        with st.expander("📝 New Meeting Details", expanded=True):
            n_col1, n_col2 = st.columns([2, 1])
            with n_col1:
                new_title = st.text_input("Meeting Title", value=f"Strategy Alignment with {selected_client.name}")
            with n_col2:
                new_date = st.date_input("Meeting Date").isoformat()
            
            new_topic = st.text_area(
                "Meeting Agenda / Topic Context",
                placeholder="E.g., Review sprint progress, resolve auth blocker, discuss timeline adjustments...",
                value="General check-in, project updates, and resolving outstanding blockers.",
            )
            
            if st.button("Create & Continue to Preparation", type="secondary"):
                created_m = db.create_meeting(
                    client_id=selected_client.id,
                    title=new_title,
                    meeting_date=new_date,
                    topic=new_topic,
                    status="upcoming",
                )
                st.session_state["prep_meeting_id"] = created_m.id
                st.rerun()
        selected_meeting = None
    else:
        selected_meeting = client_meetings[selected_meeting_opt_idx - 1]
        st.session_state["prep_meeting_id"] = selected_meeting.id

        # Show meeting topic editor
        st.markdown(
            f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                <div style="font-weight: 600; color: #f8fafc; font-size: 1.1rem;">{selected_meeting.title}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">🗓️ Date: {format_date_human(selected_meeting.meeting_date)} &nbsp;|&nbsp; 🏢 {selected_client.organization or 'N/A'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        agenda_input = st.text_area(
            "🎯 Meeting Agenda / Context for Preparation:",
            value=selected_meeting.topic or f"Follow-up alignment on deliverables and milestones with {selected_client.name}",
            help="Provide any specific topics or questions you plan to cover in this upcoming meeting.",
            key="prep_agenda_input",
        )

        prep_btn_col1, prep_btn_col2 = st.columns([2, 1])
        with prep_btn_col1:
            prep_triggered = st.button("🧠 Prepare Me (Recall Hindsight Memory + Synthesize Brief)", type="primary", use_container_width=True)
        with prep_btn_col2:
            if selected_meeting.brief_cache:
                st.info("Cached brief available below. Click 'Prepare Me' to re-synthesize.")

        # ----------------------------------------------------------------------
        # Execution & Generation
        # ----------------------------------------------------------------------
        if prep_triggered:
            with st.spinner("1/2 Recalling relevant memories from Hindsight Cloud..."):
                with st.spinner("2/2 Synthesizing personalized briefing with Groq LLM..."):
                    ok, msg, brief, memories = meeting_service.prepare_meeting(
                        client_id=selected_client.id,
                        meeting_id=selected_meeting.id,
                        topic=agenda_input,
                    )
                    if ok and brief:
                        st.session_state[f"active_brief_{selected_meeting.id}"] = brief
                        st.session_state[f"recalled_mems_{selected_meeting.id}"] = memories
                        st.success(msg)
                    else:
                        st.error(f"Preparation failed: {msg}")

        # ----------------------------------------------------------------------
        # Display Brief & Recalled Memories
        # ----------------------------------------------------------------------
        active_brief = st.session_state.get(f"active_brief_{selected_meeting.id}")
        recalled_mems = st.session_state.get(f"recalled_mems_{selected_meeting.id}", [])

        # Fallback to cached brief if available and not in active session state
        if not active_brief and selected_meeting.brief_cache:
            st.markdown("### 📋 Saved Meeting Briefing")
            st.markdown(selected_meeting.brief_cache)
            return

        if active_brief:
            st.markdown("---")

            # Memory Contribution Banner
            st.markdown(
                f"""
                <div class="memory-banner">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: 600; color: #e0e7ff;">🧠 Hindsight Long-Term Memory Active</span>
                        <div style="font-size: 0.85rem; color: #c7d2fe; margin-top: 3px;">
                            Recalled <b>{len(recalled_mems)} high-signal memories</b> across past meetings, decisions, preferences, and deadlines.
                        </div>
                    </div>
                    <span class="memory-badge">{len(recalled_mems)} Memories</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Collapsible Recalled Context
            with st.expander(f"🔍 Inspect Recalled Context from Hindsight ({len(recalled_mems)} items)", expanded=False):
                if recalled_mems:
                    for i, m in enumerate(recalled_mems, 1):
                        tags_html = " ".join([f"<span class='tag-pill'>{t}</span>" for t in m.tags])
                        st.markdown(
                            f"""
                            <div class="memory-item-card">
                                <div style="font-weight: 600; color: #f8fafc; font-size: 0.9rem;">#{i}. {m.text}</div>
                                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">
                                    📌 Context: {m.context or 'General'} &nbsp;|&nbsp; 🏷️ Tags: {tags_html}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No prior Hindsight memories found for this client. The agent will begin retaining memory after you save meeting notes.")

            # Structured Meeting Brief Display
            st.markdown(f"## 📋 Executive Brief: {active_brief.meeting_title}")

            # 1. Objective
            st.markdown(
                f"""
                <div class="brief-section">
                    <div style="font-weight: 700; color: #818cf8; margin-bottom: 5px;">🎯 MEETING OBJECTIVE</div>
                    <div style="color: #f8fafc; font-size: 1rem;">{active_brief.objective}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 2. What Changed Since Last Meeting (Critical differentiator for memory evolution!)
            if active_brief.what_changed_since_last_meeting:
                st.markdown(
                    f"""
                    <div class="brief-section-alert">
                        <div style="font-weight: 700; color: #f59e0b; margin-bottom: 5px;">🔄 WHAT CHANGED SINCE LAST MEETING</div>
                        <div style="color: #fef3c7; font-size: 0.95rem;">{active_brief.what_changed_since_last_meeting}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # 3. Two-Column Layout for Key Intel
            b_col1, b_col2 = st.columns(2)

            with b_col1:
                if active_brief.previous_discussions:
                    st.markdown("#### 📜 Historical Context & Past Discussions")
                    st.write(active_brief.previous_discussions)

                if active_brief.key_decisions:
                    st.markdown("#### ⚖️ Key Decisions Established")
                    for dec in active_brief.key_decisions:
                        st.markdown(f"- **{dec}**")

                if active_brief.outstanding_commitments:
                    st.markdown("#### 🤝 Outstanding Commitments")
                    for comm in active_brief.outstanding_commitments:
                        st.markdown(f"- {comm}")

                if active_brief.deadlines:
                    st.markdown("#### ⏰ Target Deadlines & Milestones")
                    for dl in active_brief.deadlines:
                        st.markdown(f"- ⏳ `{dl}`")

            with b_col2:
                if active_brief.client_preferences:
                    st.markdown("#### 💡 Client Preferences & Working Style")
                    for pref in active_brief.client_preferences:
                        st.markdown(f"- 🌟 {pref}")

                if active_brief.unresolved_issues:
                    st.markdown("#### ⚠️ Unresolved Issues & Blockers")
                    for issue in active_brief.unresolved_issues:
                        st.markdown(f"- 🚨 <span style='color: #f87171;'>{issue}</span>", unsafe_allow_html=True)

                if active_brief.recommended_talking_points:
                    st.markdown("#### 💬 Recommended Talking Points")
                    for tp in active_brief.recommended_talking_points:
                        st.markdown(f"- 🗣️ {tp}")

                if active_brief.suggested_questions:
                    st.markdown("#### ❓ Suggested High-Leverage Questions")
                    for q in active_brief.suggested_questions:
                        st.markdown(f"- ❓ *{q}*")

                if active_brief.risks_or_watchouts:
                    st.markdown("#### 🛡️ Risks to Watch")
                    for r in active_brief.risks_or_watchouts:
                        st.markdown(f"- ⚠️ {r}")

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            # Export / Download options
            st.download_button(
                label="📥 Download Brief as Markdown",
                data=active_brief.raw_markdown,
                file_name=f"Meeting_Brief_{selected_client.name.replace(' ', '_')}_{selected_meeting.meeting_date}.md",
                mime="text/markdown",
                use_container_width=True,
            )
