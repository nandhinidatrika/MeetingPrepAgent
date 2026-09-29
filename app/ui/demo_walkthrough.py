"""Interactive Step-by-Step Demo Walkthrough for Hackathon Showcase."""
import streamlit as st

from app.database import db
from app.models.schemas import ExtractedNoteItems
from app.services.meeting_service import get_meeting_service
from app.utils.helpers import format_date_human


def render_demo_walkthrough():
    """Render the guided 4-step progressive memory evolution demonstration."""
    meeting_service = get_meeting_service()

    st.title("🚀 The 'WOW' Demonstration Walkthrough")
    st.caption("A guided story demonstrating how Hindsight memory evolves across 3 meetings with ABC Technologies.")

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #4338ca; border-radius: 10px; padding: 1.2rem; margin-bottom: 1.5rem;">
            <div style="font-weight: 700; color: #818cf8; font-size: 1.1rem;">The Persistent Learning Story</div>
            <div style="color: #cbd5e1; font-size: 0.95rem; margin-top: 5px;">
                <b>At first, the agent knows little.</b> As meetings occur, it records decisions, preferences, and blockers.
                In subsequent meetings, it recalls past context. When deadlines shift or new requirements emerge, it reconciles
                both <b>OLD</b> and <b>NEW</b> memories, producing a smarter, context-aware preparation brief.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        "1️⃣ Meeting 1 (Initial Kickoff)",
        "2️⃣ Prepare Meeting 2 (Recalling M1 Context)",
        "3️⃣ Meeting 2 (Scope Expansion & Deadline Shift)",
        "4️⃣ Prepare Meeting 3 (Smarter Preparation: Old + New Memory)",
    ]

    selected_step = st.radio("Select Demo Stage:", steps, horizontal=True)

    # --------------------------------------------------------------------------
    # Step 1: Meeting 1 Kickoff
    # --------------------------------------------------------------------------
    if "Meeting 1" in selected_step:
        st.subheader("Stage 1: Meeting 1 — Analytics Dashboard Kickoff")
        st.markdown(
            """
            **Context:** First interaction with Sarah Chen (VP of Engineering, ABC Technologies).
            - **Deliverable:** Custom Analytics Dashboard
            - **Target Launch:** October 15
            - **Hard Requirement:** Comprehensive API documentation
            - **Client Preference:** Sarah explicitly requested concise, bulleted updates
            """
        )

        if st.button("🌱 Execute Step 1: Retain Meeting 1 in Hindsight", type="primary"):
            with st.spinner("Recording Meeting 1 and retaining memory in Hindsight..."):
                client = db.get_client_by_name("Sarah Chen")
                if not client:
                    client = db.create_client(
                        name="Sarah Chen",
                        organization="ABC Technologies",
                        email="sarah.chen@abctechnologies.io",
                        role="VP of Engineering",
                    )
                
                m1_notes = (
                    "Kickoff meeting with ABC Technologies. They need a custom analytics dashboard. "
                    "Target launch deadline is October 15. Sarah emphasized that comprehensive API "
                    "documentation is strictly required before any production deployment. "
                    "Client explicitly stated they prefer concise bulleted progress updates. "
                    "Agreed to deliver draft UI wireframes by this Friday."
                )
                m1_items = ExtractedNoteItems(
                    decisions=["Build custom analytics dashboard", "Deliver draft UI wireframes by Friday"],
                    commitments=["Provide comprehensive API documentation before production launch"],
                    deadlines=["Analytics dashboard launch: October 15"],
                    preferences=["Client prefers concise bulleted updates only"],
                    requirements=["Custom analytics dashboard", "Complete API documentation"],
                    follow_ups=["Send draft UI wireframes by Friday"],
                )
                
                m1 = db.create_meeting(
                    client_id=client.id,
                    title="Meeting 1: Analytics Dashboard Kickoff",
                    meeting_date="2026-09-01",
                    topic="Analytics Dashboard Requirements & Timeline",
                    status="completed",
                    notes=m1_notes,
                )
                
                ok, msg, chunks = meeting_service.save_and_remember_post_meeting(
                    client_id=client.id,
                    meeting_id=m1.id,
                    raw_notes=m1_notes,
                    extracted_items=m1_items,
                    retain_to_hindsight=True,
                )
                st.success(f"Meeting 1 recorded! Retained {len(chunks)} memory units in Hindsight Cloud.")

    # --------------------------------------------------------------------------
    # Step 2: Prepare Meeting 2
    # --------------------------------------------------------------------------
    elif "Prepare Meeting 2" in selected_step:
        st.subheader("Stage 2: Preparing for Meeting 2")
        st.markdown(
            """
            Now we prepare for the 2nd meeting.
            **Expected Outcome:** The agent recalls Meeting 1 context (Oct 15 launch deadline, API doc requirement, concise updates preference).
            """
        )
        client = db.get_client_by_name("Sarah Chen")
        if not client:
            st.warning("Please complete Step 1 first to create Sarah Chen / ABC Technologies.")
            return

        if st.button("🧠 Execute Step 2: Prepare Meeting 2 Brief", type="primary"):
            # Ensure Meeting 2 exists
            meetings = db.get_meetings_by_client(client.id)
            m2 = next((m for m in meetings if "Meeting 2" in m.title), None)
            if not m2:
                m2 = db.create_meeting(
                    client_id=client.id,
                    title="Meeting 2: Mid-Sprint Review & Scope Expansion",
                    meeting_date="2026-09-15",
                    topic="Reviewing dashboard wireframes, API docs timeline, and regional needs",
                    status="upcoming",
                )

            with st.spinner("Recalling Meeting 1 memories from Hindsight & generating brief..."):
                ok, msg, brief, mems = meeting_service.prepare_meeting(
                    client_id=client.id,
                    meeting_id=m2.id,
                    topic=m2.topic,
                )
                if ok and brief:
                    st.success(f"Recalled {len(mems)} memories from Hindsight!")
                    st.markdown(brief.raw_markdown)

    # --------------------------------------------------------------------------
    # Step 3: Meeting 2 Scope Expansion
    # --------------------------------------------------------------------------
    elif "Meeting 2 (" in selected_step:
        st.subheader("Stage 3: Meeting 2 Outcomes — Scope Expansion & Timeline Shifts")
        st.markdown(
            """
            **What happened in Meeting 2:**
            - **Scope Expansion:** Sarah added requirement for regional filtering (North America & Europe).
            - **Deadline Shift:** API documentation deadline moved from initial launch date to **October 25**.
            - **Cadence Change:** Sarah requested progress updates **twice per week** (Tuesday & Thursday).
            - **Critical Blocker:** Enterprise Okta SSO authentication is blocked pending IT security review.
            """
        )

        client = db.get_client_by_name("Sarah Chen")
        if not client:
            st.warning("Please complete Step 1 first.")
            return

        if st.button("💾 Execute Step 3: Retain Meeting 2 Updates into Hindsight", type="primary"):
            meetings = db.get_meetings_by_client(client.id)
            m2 = next((m for m in meetings if "Meeting 2" in m.title), None)
            if not m2:
                m2 = db.create_meeting(
                    client_id=client.id,
                    title="Meeting 2: Mid-Sprint Review & Scope Expansion",
                    meeting_date="2026-09-15",
                    topic="Scope Expansion, Timeline Adjustment & Auth Blocker",
                    status="completed",
                )

            m2_notes = (
                "Mid-sprint review with Sarah Chen. Major updates: "
                "1. Dashboard scope expanded: must include regional filtering for North America and Europe. "
                "2. API documentation deadline shifted to October 25 due to backend API schema changes. "
                "3. Sarah requested progress updates twice per week (every Tuesday & Thursday). "
                "4. Critical unresolved issue: Enterprise Okta SSO authentication integration is currently blocked by their IT security review."
            )
            m2_items = ExtractedNoteItems(
                decisions=["Add regional filtering (NA and EU) to dashboard scope", "Shift API documentation deadline to October 25"],
                commitments=["Provide progress updates twice per week (Tuesday & Thursday)"],
                deadlines=["API documentation shifted deadline: October 25", "Dashboard launch deadline: October 15"],
                preferences=["Progress update frequency: Twice per week (Tue/Thu)", "Concise updates"],
                requirements=["Regional filtering across NA & EU", "Enterprise Okta SSO authentication"],
                follow_ups=["Follow up with ABC Tech IT security team on Okta SSO approval"],
                unresolved_issues=["Enterprise Okta SSO authentication blocker pending IT security review"],
            )

            with st.spinner("Retaining Meeting 2 intelligence into Hindsight Cloud..."):
                ok, msg, chunks = meeting_service.save_and_remember_post_meeting(
                    client_id=client.id,
                    meeting_id=m2.id,
                    raw_notes=m2_notes,
                    extracted_items=m2_items,
                    retain_to_hindsight=True,
                )
                st.success(f"Meeting 2 updates retained! Hindsight now holds memories from BOTH Meeting 1 & Meeting 2.")

    # --------------------------------------------------------------------------
    # Step 4: Prepare Meeting 3
    # --------------------------------------------------------------------------
    elif "Prepare Meeting 3" in selected_step:
        st.subheader("Stage 4: Prepare Meeting 3 — Witnessing Combined Evolved Memory!")
        st.markdown(
            """
            **The Grand Finale:**
            When we prepare for Meeting 3, notice how the AI:
            1. Recalls **Meeting 1** initial objectives (October 15 dashboard release).
            2. Recalls **Meeting 2** updates (October 25 shifted API docs deadline, regional filters, twice-weekly updates).
            3. Flags the **Okta SSO Authentication Blocker** prominently under Unresolved Issues!
            4. Explicitly outlines **What Changed Since Last Meeting**!
            """
        )

        client = db.get_client_by_name("Sarah Chen")
        if not client:
            st.warning("Please complete Steps 1-3 first.")
            return

        if st.button("🔥 Execute Step 4: Prepare Meeting 3 (Old + New Memory)", type="primary"):
            meetings = db.get_meetings_by_client(client.id)
            m3 = next((m for m in meetings if "Meeting 3" in m.title), None)
            if not m3:
                m3 = db.create_meeting(
                    client_id=client.id,
                    title="Meeting 3: Auth Blocker Resolution & Final Pre-Launch Review",
                    meeting_date="2026-10-01",
                    topic="Resolving Okta SSO Blocker, Regional Filtering Verification, and Launch Prep",
                    status="upcoming",
                )

            with st.spinner("Recalling all historical memories from Hindsight Cloud & generating synthesis..."):
                ok, msg, brief, mems = meeting_service.prepare_meeting(
                    client_id=client.id,
                    meeting_id=m3.id,
                    topic=m3.topic,
                )
                if ok and brief:
                    st.markdown(
                        f"""
                        <div class="memory-banner">
                            <div>
                                <span style="font-size: 1.1rem; font-weight: 700; color: #e0e7ff;">
                                    🧠 Evolved Memory Active: Recalled {len(mems)} Memories from Hindsight
                                </span>
                                <div style="font-size: 0.85rem; color: #c7d2fe; margin-top: 3px;">
                                    Spanning Meeting 1 kickoff, Meeting 2 scope shifts, and ongoing blocker tracking.
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(brief.raw_markdown)
