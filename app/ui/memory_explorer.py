"""Memory Explorer UI view for Meeting Prep Agent."""
import streamlit as st

from app.database import db
from app.services.groq_service import get_groq_service
from app.services.hindsight_service import get_hindsight_service
from app.utils.helpers import format_date_human


def render_memory_explorer():
    """Render the interactive Hindsight Memory Explorer screen."""
    hindsight = get_hindsight_service()
    groq = get_groq_service()

    st.title("🔍 Hindsight Memory Explorer")
    st.caption("Inspect, query, and reflect on the persistent knowledge graph and memories the agent has learned.")

    clients = db.get_all_clients()
    if not clients:
        st.info("No clients available. Create a client or seed the demo dataset.")
        return

    # Client Selection
    client_names = [f"{c.name} ({c.organization})" if c.organization else c.name for c in clients]
    col_c1, col_c2 = st.columns([2, 2])

    with col_c1:
        sel_idx = st.selectbox(
            "👤 Select Client to Explore:",
            range(len(clients)),
            format_func=lambda i: client_names[i],
            key="mem_exp_client",
        )
        selected_client = clients[sel_idx]

    with col_c2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        reflect_btn = st.button("✨ Reflect on Client Relationship (Agent Synthesis)", use_container_width=True)

    # --------------------------------------------------------------------------
    # Search Query Bar
    # --------------------------------------------------------------------------
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        query_input = st.text_input(
            "🔎 Query Hindsight Memory Bank:",
            value="",
            placeholder=f"E.g., What are {selected_client.name}'s communication preferences? What deadlines were set?",
        )
    with search_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        search_btn = st.button("Search Memories", type="primary", use_container_width=True)

    # --------------------------------------------------------------------------
    # Relationship Reflection Trigger
    # --------------------------------------------------------------------------
    if reflect_btn:
        with st.spinner("Synthesizing agent reflection from Hindsight memories..."):
            all_mems = hindsight.list_client_memories(selected_client.name)
            ok, reflection_text = groq.reflect_client_relationship(
                client_name=selected_client.name,
                organization=selected_client.organization,
                recalled_memories=all_mems,
            )
            if ok:
                st.markdown("### 🧠 Strategic Relationship Reflection")
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%); border: 1px solid #6366f1; border-radius: 10px; padding: 1.2rem; margin: 1rem 0;">
                        {reflection_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.warning(reflection_text)

    # --------------------------------------------------------------------------
    # Fetch & Display Memories
    # --------------------------------------------------------------------------
    with st.spinner("Retrieving memories from Hindsight Cloud..."):
        if query_input.strip():
            memories = hindsight.recall_memories(
                query=query_input.strip(),
                client_name=selected_client.name,
            )
        else:
            memories = hindsight.list_client_memories(selected_client.name)

    st.markdown("---")

    # Metrics on memory bank
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.metric("Total Recalled Units", len(memories))
    with stat_col2:
        decisions_cnt = sum(1 for m in memories if any("decision" in t for t in m.tags) or "decision" in m.text.lower())
        st.metric("Decisions & Governance", decisions_cnt)
    with stat_col3:
        prefs_cnt = sum(1 for m in memories if any("preference" in t for t in m.tags) or "prefer" in m.text.lower())
        st.metric("Preferences & Style", prefs_cnt)

    if not memories:
        st.info(
            f"No memories found in Hindsight for **{selected_client.name}**. "
            "Record notes from meetings or seed the demo scenario to see memories populated."
        )
        return

    # Categorized Tab Views
    tab_all, tab_dec, tab_pref, tab_dead, tab_block = st.tabs([
        "📋 All Memories",
        "⚖️ Decisions",
        "💡 Preferences",
        "⏰ Deadlines & Milestones",
        "⚠️ Blockers & Risks",
    ])

    with tab_all:
        for i, m in enumerate(memories, 1):
            tags_html = " ".join([f"<span class='tag-pill'>{t}</span>" for t in m.tags])
            st.markdown(
                f"""
                <div class="memory-item-card">
                    <div style="font-weight: 600; color: #f8fafc; font-size: 0.95rem;">#{i}. {m.text}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 5px;">
                        📌 Context: {m.context or 'General'} &nbsp;|&nbsp; 🏷️ {tags_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_dec:
        dec_mems = [m for m in memories if any("decision" in t for t in m.tags) or "decision" in m.text.lower()]
        if not dec_mems:
            st.info("No specific decision memories found.")
        for i, m in enumerate(dec_mems, 1):
            st.markdown(f"**{i}.** {m.text}")

    with tab_pref:
        pref_mems = [m for m in memories if any("preference" in t for t in m.tags) or "prefer" in m.text.lower()]
        if not pref_mems:
            st.info("No specific preference memories found.")
        for i, m in enumerate(pref_mems, 1):
            st.markdown(f"**{i}.** 🌟 {m.text}")

    with tab_dead:
        dead_mems = [m for m in memories if any("deadline" in t for t in m.tags) or "deadline" in m.text.lower()]
        if not dead_mems:
            st.info("No deadline memories found.")
        for i, m in enumerate(dead_mems, 1):
            st.markdown(f"**{i}.** ⏳ `{m.text}`")

    with tab_block:
        block_mems = [m for m in memories if any("unresolved" in t for t in m.tags) or "blocker" in m.text.lower() or "issue" in m.text.lower()]
        if not block_mems:
            st.info("No unresolved blocker memories found.")
        for i, m in enumerate(block_mems, 1):
            st.markdown(f"**{i}.** 🚨 <span style='color: #f87171;'>{m.text}</span>", unsafe_allow_html=True)
