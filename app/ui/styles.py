"""Custom CSS styling for the Streamlit Meeting Prep Agent UI."""

CUSTOM_CSS = """
<style>
/* Main Container Styling */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Metric Cards */
.metric-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem;
    color: #f8fafc;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    border-color: #6366f1;
    transform: translateY(-2px);
}
.metric-value {
    font-size: 2.1rem;
    font-weight: 700;
    color: #818cf8;
    margin: 0.3rem 0;
}
.metric-label {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Status Badges */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
}
.status-connected {
    background-color: rgba(34, 197, 94, 0.15);
    color: #4ade80;
    border: 1px solid rgba(34, 197, 94, 0.3);
}
.status-disconnected {
    background-color: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Memory Callout Banner */
.memory-banner {
    background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
    border: 1px solid #6366f1;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.memory-badge {
    background: #4f46e5;
    color: white;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85rem;
}

/* Briefing Section Cards */
.brief-section {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-left: 4px solid #6366f1;
    border-radius: 8px;
    padding: 1.1rem;
    margin-bottom: 1rem;
}
.brief-section-alert {
    background: #1c1917;
    border: 1px solid #44403c;
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 1.1rem;
    margin-bottom: 1rem;
}
.brief-section-danger {
    background: #18181b;
    border: 1px solid #3f3f46;
    border-left: 4px solid #ef4444;
    border-radius: 8px;
    padding: 1.1rem;
    margin-bottom: 1rem;
}

/* Tag Pills */
.tag-pill {
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    margin-right: 4px;
}

/* Memory Card */
.memory-item-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.9rem;
    margin-bottom: 0.7rem;
}
</style>
"""


def apply_custom_css():
    """Apply custom CSS styling into Streamlit page."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
