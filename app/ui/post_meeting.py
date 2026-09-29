"""Post-Meeting Memory Retention UI view for Meeting Prep Agent."""
import streamlit as st

from app.database import db
from app.models.schemas import ExtractedNoteItems
from app.services.groq_service import get_groq_service
from app.services.meeting_service import get_meeting_service
from app.utils.helpers import format_date_human


def render_post_meeting():
    """Render the Post-Meeting Memory capture screen."""
    meeting_service = get_meeting_service()
    groq_service = get_groq_service()

    st.title("📝 Post-Meeting Memory Capture")
    st.caption("Record meeting outcomes, extract structured intelligence, and retain into Hindsight Cloud long-term memory.")

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

    client_names = [f"{c.name} ({c.organization})" if c.organization else c.name for c in clients]
    client_ids = [c.id for c in clients]

    default_client_idx = 0
    if "post_client_id" in st.session_state and st.session_state["post_client_id"] in client_ids:
        default_client_idx = client_ids.index(st.session_state["post_client_id"])

    with col1:
        selected_client_idx = st.selectbox(
            "👤 Select Client / Contact",
            range(len(clients)),
            format_func=lambda i: client_names[i],
            index=default_client_idx,
            key="post_client_select",
        )
        selected_client = clients[selected_client_idx]
        st.session_state["post_client_id"] = selected_client.id

    client_meetings = db.get_meetings_by_client(selected_client.id)

    with col2:
        meeting_options = ["➕ Create New Completed Meeting"] + [
            f"{m.title} ({format_date_human(m.meeting_date)}) [{m.status.upper()}]" for m in client_meetings
        ]
        
        default_meeting_idx = 0
        if "post_meeting_id" in st.session_state:
            for idx, m in enumerate(client_meetings):
                if m.id == st.session_state["post_meeting_id"]:
                    default_meeting_idx = idx + 1
                    break

        selected_meeting_opt_idx = st.selectbox(
            "📅 Select Meeting",
            range(len(meeting_options)),
            format_func=lambda i: meeting_options[i],
            index=default_meeting_idx,
            key="post_meeting_select",
        )

    # --------------------------------------------------------------------------
    # Meeting Entity Setup
    # --------------------------------------------------------------------------
    is_new = selected_meeting_opt_idx == 0
    if is_new:
        with st.expander("📝 New Meeting Details", expanded=True):
            n_col1, n_col2 = st.columns([2, 1])
            with n_col1:
                new_title = st.text_input("Meeting Title", value=f"Discussion with {selected_client.name}", key="new_post_title")
            with n_col2:
                new_date = st.date_input("Meeting Date", key="new_post_date").isoformat()
            new_topic = st.text_input("Topic / Area", value="Project Review & Action Items", key="new_post_topic")
            
            if st.button("Initialize Meeting", key="init_new_post_m"):
                created_m = db.create_meeting(
                    client_id=selected_client.id,
                    title=new_title,
                    meeting_date=new_date,
                    topic=new_topic,
                    status="completed",
                )
                st.session_state["post_meeting_id"] = created_m.id
                st.rerun()
        selected_meeting = None
    else:
        selected_meeting = client_meetings[selected_meeting_opt_idx - 1]
        st.session_state["post_meeting_id"] = selected_meeting.id

    if not selected_meeting:
        return

    st.markdown("---")

    # --------------------------------------------------------------------------
    # Raw Notes / Transcript Input
    # --------------------------------------------------------------------------
    st.subheader(f"📋 Record Notes for: {selected_meeting.title}")

    default_notes = selected_meeting.notes or (
        f"Discussed project status with {selected_client.name}.\n"
        "- Decision: Agreed on implementation path for core features.\n"
        "- Deadline: Target release date set for next month.\n"
        "- Requirement: Needs API documentation and regional support.\n"
        "- Preference: Prefers concise weekly updates.\n"
        "- Unresolved: Security review pending for authentication."
    )

    raw_notes = st.text_area(
        "Enter Raw Meeting Notes, Discussion Summary, or Transcript:",
        value=default_notes,
        height=180,
        help="Paste rough bullet points, unstructured discussion notes, or full transcripts. Groq will parse and extract high-signal items.",
    )

    # --------------------------------------------------------------------------
    # AI Extraction Step
    # --------------------------------------------------------------------------
    col_ext1, col_ext2 = st.columns([2, 1])
    with col_ext1:
        extract_clicked = st.button("⚡ AI Auto-Extract (Parse Decisions, Deadlines, Preferences)", type="secondary", use_container_width=True)

    if extract_clicked:
        with st.spinner("Extracting structured intelligence with Groq..."):
            ok, msg, extracted = groq_service.extract_structured_notes(
                raw_notes=raw_notes,
                client_name=selected_client.name,
                organization=selected_client.organization,
                topic=selected_meeting.topic or selected_meeting.title,
                date_str=selected_meeting.meeting_date,
            )
            if ok:
                st.session_state[f"extracted_{selected_meeting.id}"] = extracted
                st.toast("Structured intelligence extracted!")
            else:
                st.error(msg)

    # Retrieve or init extracted items
    extracted_items: ExtractedNoteItems = st.session_state.get(
        f"extracted_{selected_meeting.id}",
        ExtractedNoteItems(
            decisions=[],
            commitments=[],
            deadlines=[],
            preferences=[],
            requirements=[],
            follow_ups=[],
            unresolved_issues=[],
        )
    )

    # --------------------------------------------------------------------------
    # Editable Structured Review
    # --------------------------------------------------------------------------
    st.markdown("### 🧩 Structured Intelligence Review")
    st.caption("Review and fine-tune extracted items before retaining into Hindsight Cloud memory.")

    c1, c2 = st.columns(2)

    with c1:
        decisions_str = st.text_area(
            "⚖️ Key Decisions (one per line):",
            value="\n".join(extracted_items.decisions),
            height=100,
            key=f"dec_{selected_meeting.id}",
        )
        commitments_str = st.text_area(
            "🤝 Commitments & Action Items (one per line):",
            value="\n".join(extracted_items.commitments),
            height=100,
            key=f"comm_{selected_meeting.id}",
        )
        deadlines_str = st.text_area(
            "⏰ Target Deadlines & Timelines (one per line):",
            value="\n".join(extracted_items.deadlines),
            height=80,
            key=f"dead_{selected_meeting.id}",
        )

    with c2:
        preferences_str = st.text_area(
            "💡 Client Preferences & Working Style (one per line):",
            value="\n".join(extracted_items.preferences),
            height=100,
            key=f"pref_{selected_meeting.id}",
        )
        requirements_str = st.text_area(
            "🛠️ Requirements / Technical Scope (one per line):",
            value="\n".join(extracted_items.requirements),
            height=100,
            key=f"req_{selected_meeting.id}",
        )
        unresolved_str = st.text_area(
            "⚠️ Unresolved Issues & Blockers (one per line):",
            value="\n".join(extracted_items.unresolved_issues),
            height=80,
            key=f"unres_{selected_meeting.id}",
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # Save & Retain Action
    # --------------------------------------------------------------------------
    save_col1, save_col2 = st.columns([2, 1])
    with save_col1:
        save_btn = st.button("💾 Save & Retain in Hindsight Long-Term Memory", type="primary", use_container_width=True)

    if save_btn:
        # Build updated ExtractedNoteItems from text areas
        final_items = ExtractedNoteItems(
            decisions=[d.strip() for d in decisions_str.splitlines() if d.strip()],
            commitments=[c.strip() for c in commitments_str.splitlines() if c.strip()],
            deadlines=[dl.strip() for dl in deadlines_str.splitlines() if dl.strip()],
            preferences=[p.strip() for p in preferences_str.splitlines() if p.strip()],
            requirements=[r.strip() for r in requirements_str.splitlines() if r.strip()],
            follow_ups=[f.strip() for f in commitments_str.splitlines() if f.strip()],
            unresolved_issues=[u.strip() for u in unresolved_str.splitlines() if u.strip()],
        )

        with st.spinner("Retaining structured memory units in Hindsight Cloud..."):
            ok, msg, retained_chunks = meeting_service.save_and_remember_post_meeting(
                client_id=selected_client.id,
                meeting_id=selected_meeting.id,
                raw_notes=raw_notes,
                extracted_items=final_items,
                retain_to_hindsight=True,
            )

            if ok:
                st.markdown(
                    f"""
                    <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 8px; padding: 1.2rem; margin: 1rem 0;">
                        <div style="font-size: 1.1rem; font-weight: 700; color: #4ade80;">
                            ✅ Meeting Information Successfully Added to Long-Term Memory
                        </div>
                        <div style="color: #cbd5e1; font-size: 0.9rem; margin-top: 5px;">
                            {msg}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Show learned summary
                with st.expander(f"🧠 Retained Memory Units ({len(retained_chunks)} chunks stored)", expanded=True):
                    for idx, chunk in enumerate(retained_chunks, 1):
                        st.markdown(f"**{idx}.** {chunk}")
            else:
                st.error(f"Error saving to Hindsight: {msg}")
