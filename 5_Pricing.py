"""
pages/1_Start_Trial.py — Nexus Excel AI v5.0 · Start Trial
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import activate_plan, has_used_trial, supabase
from styles import GLOBAL_CSS

st.set_page_config(
    page_title="Nexus Excel AI — Start Trial",
    page_icon="🎁",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.trial-wrap { max-width: 520px; margin: 3rem auto; animation: fadeUp 0.35s ease both; text-align: center; }
.trial-card {
    background: var(--bg-card);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 40px #00d4aa15;
}
.blocked-card {
    background: var(--bg-card);
    border: 1px solid var(--danger);
    border-radius: 16px;
    padding: 2.5rem 2rem;
}
.trial-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.trial-email-box {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: var(--font-mono);
    font-size: 0.95rem;
    color: var(--text-primary);
    margin: 1.5rem 0;
    word-break: break-all;
}
.feature-list {
    text-align: left;
    margin: 1rem 0;
    padding: 0;
    list-style: none;
}
.feature-list li {
    font-size: 0.875rem;
    color: var(--text-muted);
    padding: 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.feature-list li span { color: var(--accent); font-weight: 700; }
</style>
""", unsafe_allow_html=True)

if "email" not in st.session_state or not st.session_state["email"]:
    st.switch_page("Home.py")

email = st.session_state["email"]

st.markdown('<div class="trial-wrap">', unsafe_allow_html=True)

if has_used_trial(email):
    st.markdown(f"""
    <div class="blocked-card">
        <div class="trial-icon">🚫</div>
        <h3 style="color:var(--danger); font-family:var(--font-mono); margin-bottom: 0.5rem;">Trial Already Used</h3>
        <p style="color:var(--text-muted); font-size: 0.95rem; line-height: 1.6;">
            This email has already claimed a free trial.
        </p>
        <div class="trial-email-box">{email}</div>
        <p style="color:var(--text-muted); font-size: 0.9rem;">
            Please upgrade to a paid plan to continue using Nexus.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💎 View Plans", use_container_width=True):
            st.switch_page("pages/5_Pricing.py")
    with col2:
        if st.button("← Back to Home", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")

else:
    st.markdown(f"""
    <div class="trial-card">
        <div class="trial-icon">🎁</div>
        <h3 style="color:var(--accent); font-family:var(--font-mono); margin-bottom: 0.5rem;">Start Your Free Trial</h3>
        <p style="color:var(--text-muted); font-size: 0.95rem; line-height: 1.6;">
            Unlock all Nexus Pro features for <strong style="color:var(--text-primary);">2 full days</strong>. No credit card required.
        </p>
        <div class="trial-email-box">{email}</div>
        <ul class="feature-list">
            <li><span>✓</span> AI-powered analysis with Google Gemini 2.5 Flash</li>
            <li><span>✓</span> Interactive Plotly charts (zoom, hover, export)</li>
            <li><span>✓</span> Data cleaning wizard & anomaly detection</li>
            <li><span>✓</span> Correlation matrix & column deep-dive</li>
            <li><span>✓</span> AI-suggested questions & analysis templates</li>
            <li><span>✓</span> Analysis history & query bookmarks</li>
            <li><span>✓</span> HTML report export</li>
            <li><span>✓</span> Multi-sheet Excel support</li>
            <li><span>✓</span> 30 AI queries per session</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    start_btn = st.button("🚀 Activate Free Trial", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if start_btn:
        if not supabase:
            st.error("❌ No database connection. Configure SUPABASE_URL and SUPABASE_KEY in your Streamlit secrets.")
        else:
            with st.spinner("Activating your trial..."):
                updated_user = activate_plan(email, "trial")

            if not updated_user:
                st.error("❌ Activation failed. Check your Supabase users table schema.")
            else:
                st.session_state["user"] = updated_user
                st.success("✅ Trial activated! Redirecting to your dashboard...")
                time.sleep(1.0)
                st.switch_page("pages/3_App.py")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💎 View Paid Plans", use_container_width=True):
            st.switch_page("pages/5_Pricing.py")
    with col2:
        if st.button("← Different email", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")

st.markdown('</div>', unsafe_allow_html=True)
