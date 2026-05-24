"""
pages/5_Pricing.py — Nexus Excel AI v5.0 · Pricing Page
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from styles import GLOBAL_CSS, PRICING_CSS

st.set_page_config(
    page_title="Nexus Excel AI — Pricing",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(PRICING_CSS, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; padding: 3rem 1rem 1rem 1rem; animation: fadeUp 0.4s ease both;">
    <div style="display:inline-block; background:rgba(0,212,170,0.1); border:1px solid rgba(0,212,170,0.2);
                border-radius:20px; padding:0.3rem 1rem; font-size:0.75rem; color:var(--accent);
                font-family:var(--font-mono); letter-spacing:2px; margin-bottom:1.5rem; text-transform:uppercase;">
        ◈ Simple, Transparent Pricing
    </div>
    <h1 style="font-family:var(--font-mono); font-size:clamp(2rem,5vw,3.5rem); color:var(--text-primary);
               line-height:1.1; margin:0 0 1rem 0;">
        Choose Your Plan
    </h1>
    <p style="color:var(--text-muted); font-size:1.05rem; max-width:520px; margin:0 auto 2rem auto; line-height:1.7;">
        Start free. Scale as you grow. All plans include the full Nexus feature set.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="pricing-grid">', unsafe_allow_html=True)
_, col1, col2, col3, col4, _ = st.columns([0.2, 1, 1, 1, 1, 0.2])

with col1:
    st.markdown("""
    <div class="pricing-card">
        <div class="pricing-name">Trial</div>
        <div class="pricing-price">Free</div>
        <div class="pricing-period">2 days · no card needed</div>
        <hr class="pricing-divider">
        <div class="pricing-feature">
            <span>✓</span> Full AI analysis<br>
            <span>✓</span> Interactive charts<br>
            <span>✓</span> Data cleaning<br>
            <span>✓</span> 30 queries / session<br>
            <span>✓</span> CSV &amp; Excel upload<br>
            <span style="color:var(--text-muted);">✗</span> <span style="color:var(--text-muted);">History saved</span><br>
            <span style="color:var(--text-muted);">✗</span> <span style="color:var(--text-muted);">Bookmarks</span><br>
            <span style="color:var(--text-muted);">✗</span> <span style="color:var(--text-muted);">HTML export</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="pricing-card">
        <div class="pricing-name">Basic</div>
        <div class="pricing-price">$9</div>
        <div class="pricing-period">per month</div>
        <hr class="pricing-divider">
        <div class="pricing-feature">
            <span>✓</span> Full AI analysis<br>
            <span>✓</span> Interactive charts<br>
            <span>✓</span> Data cleaning<br>
            <span>✓</span> 100 queries / session<br>
            <span>✓</span> CSV &amp; Excel upload<br>
            <span>✓</span> Analysis history (20)<br>
            <span>✓</span> 10 bookmarks<br>
            <span style="color:var(--text-muted);">✗</span> <span style="color:var(--text-muted);">HTML export</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="pricing-card featured">
        <div class="pricing-badge">Most Popular</div>
        <div class="pricing-name">Premium</div>
        <div class="pricing-price">$24</div>
        <div class="pricing-period">per month</div>
        <hr class="pricing-divider">
        <div class="pricing-feature">
            <span>✓</span> Full AI analysis<br>
            <span>✓</span> Interactive charts<br>
            <span>✓</span> Data cleaning<br>
            <span>✓</span> 500 queries / session<br>
            <span>✓</span> CSV &amp; Excel upload<br>
            <span>✓</span> Analysis history (unlimited)<br>
            <span>✓</span> Unlimited bookmarks<br>
            <span>✓</span> HTML report export<br>
            <span>✓</span> Anomaly detection<br>
            <span>✓</span> Correlation matrix
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="pricing-card">
        <div class="pricing-name">Pro</div>
        <div class="pricing-price">$59</div>
        <div class="pricing-period">per month</div>
        <hr class="pricing-divider">
        <div class="pricing-feature">
            <span>✓</span> Everything in Premium<br>
            <span>✓</span> Unlimited queries<br>
            <span>✓</span> Trend forecasting<br>
            <span>✓</span> Multi-file merge<br>
            <span>✓</span> Priority AI (faster)<br>
            <span>✓</span> Dedicated support<br>
            <span>✓</span> Custom analysis templates<br>
            <span>✓</span> Admin dashboard access
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin: 2rem auto 3rem auto; max-width: 600px;">
    <p style="color:var(--text-muted); font-size:0.875rem; line-height:1.7;">
        All plans are managed by your administrator. To upgrade, contact your admin or reach out to 
        <strong style="color:var(--text-primary);">support@nexusai.com</strong>.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="max-width:900px; margin:0 auto 3rem auto;">
    <h3 style="font-family:var(--font-mono); font-size:1.1rem; color:var(--text-primary); text-align:center; margin-bottom:2rem;">
        Feature Comparison
    </h3>
</div>
""", unsafe_allow_html=True)

_, table_col, _ = st.columns([0.5, 3, 0.5])
with table_col:
    import pandas as pd
    features_df = pd.DataFrame({
        "Feature": [
            "AI Analysis (Gemini 2.5 Flash)",
            "Interactive Plotly Charts",
            "Data Cleaning Wizard",
            "Anomaly & Outlier Detection",
            "Correlation Matrix",
            "AI-Suggested Questions",
            "Analysis Templates",
            "Column Deep-Dive Panel",
            "Multi-Sheet Excel",
            "Analysis History",
            "Query Bookmarks",
            "HTML Report Export",
            "Trend Forecasting",
            "Multi-File Merge",
            "Queries per Session",
        ],
        "Trial": ["✅","✅","✅","✅","✅","✅","✅","✅","✅","❌","❌","❌","❌","❌","30"],
        "Basic": ["✅","✅","✅","✅","✅","✅","✅","✅","✅","20 saved","10","❌","❌","❌","100"],
        "Premium": ["✅","✅","✅","✅","✅","✅","✅","✅","✅","Unlimited","Unlimited","✅","❌","❌","500"],
        "Pro": ["✅","✅","✅","✅","✅","✅","✅","✅","✅","Unlimited","Unlimited","✅","✅","✅","Unlimited"],
    })
    st.dataframe(features_df, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)
_, back_col, _ = st.columns([2, 1, 2])
with back_col:
    if st.button("← Back to Login", use_container_width=True):
        st.switch_page("Home.py")
