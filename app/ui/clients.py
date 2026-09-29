"""Clients and Contacts management UI for Meeting Prep Agent."""
import streamlit as st

from app.database import db
from app.utils.helpers import format_date_human


def render_clients():
    """Render the Clients and Contacts management screen."""
    st.title("👥 Clients & Contacts")
    st.caption("Manage client relationships, organization context, and contact profiles.")

    clients = db.get_all_clients()

    tab_list, tab_create = st.tabs(["📋 All Clients", "➕ Add New Client"])

    with tab_create:
        st.subheader("Add New Client Profile")
        with st.form("create_client_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", placeholder="e.g. Alex Morgan")
                organization = st.text_input("Organization / Company", placeholder="e.g. Acme Corp")
                role = st.text_input("Role / Title", placeholder="e.g. Chief Product Officer")
            with col2:
                email = st.text_input("Email Address", placeholder="e.g. alex@acmecorp.com")
                notes = st.text_area("Initial Context / Notes", placeholder="e.g. Primary point of contact for enterprise tier.")

            submitted = st.form_submit_button("Create Client Profile", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Client name is required.")
                else:
                    new_client = db.create_client(
                        name=name,
                        organization=organization,
                        email=email,
                        role=role,
                        notes=notes,
                    )
                    st.success(f"Client '{new_client.name}' created successfully!")
                    st.rerun()

    with tab_list:
        if not clients:
            st.info("No clients found. Click 'Add New Client' above to create one.")
            return

        for c in clients:
            meetings = db.get_meetings_by_client(c.id)
            follow_ups = db.get_pending_follow_ups(client_id=c.id)

            with st.expander(f"👤 {c.name} — {c.organization or 'Individual'} ({len(meetings)} meetings, {len(follow_ups)} pending follow-ups)", expanded=False):
                c_col1, c_col2 = st.columns([2, 1])
                with c_col1:
                    st.markdown(f"**Email:** {c.email or 'N/A'}")
                    st.markdown(f"**Role:** {c.role or 'N/A'}")
                    if c.notes:
                        st.markdown(f"**Notes:** {c.notes}")
                    st.markdown(f"**Created:** {format_date_human(c.created_at)}")

                with c_col2:
                    if st.button("🧠 Prepare Meeting for Client", key=f"c_prep_{c.id}", use_container_width=True):
                        st.session_state["selected_page"] = "Meeting Preparation"
                        st.session_state["prep_client_id"] = c.id
                        st.rerun()

                    if st.button("🔍 Explore Hindsight Memories", key=f"c_mem_{c.id}", use_container_width=True):
                        st.session_state["selected_page"] = "Memory Explorer"
                        st.session_state["mem_exp_client_id"] = c.id
                        st.rerun()

                st.markdown("##### 📅 Meetings History")
                if meetings:
                    for m in meetings:
                        status_color = "#3b82f6" if m.status == "upcoming" else "#10b981"
                        st.markdown(
                            f"- **{m.title}** ({format_date_human(m.meeting_date)}) — <span style='color: {status_color}; font-weight: 600;'>{m.status.upper()}</span>: *{m.topic or 'General'}*",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("No meetings recorded yet.")
