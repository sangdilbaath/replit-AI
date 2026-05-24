"""
Home.py — Nexus Excel AI v5.0 · Landing Page
"""

import streamlit as st
import sys, os, time, re, hmac
sys.path.insert(0, os.path.dirname(__file__))

from database import verify_or_create_user, activate_plan, is_account_expired
from styles import GLOBAL_CSS

st.set_page_config(
    page_title="Nexus Excel AI — Home",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "login_attempts" not in st.session_state:
    st.session_state["login_attempts"] = 0

if st.session_state.get("user") and st.session_state["user"].get("has_payment_on_file"):
    if not is_account_expired(st.session_state["user"]):
        st.switch_page("pages/3_App.py")

st.markdown("""
<div class="hero-landing">
    <div class="hero-badge">◈ Nexus Excel AI v5.0</div>
    <h1 class="hero-h1">Your Spreadsheets,<br><span>Supercharged by AI.</span></h1>
    <p class="hero-p">
        Upload any CSV or Excel file and chat with your data in plain English.
        Nexus writes code, builds interactive charts, cleans your data,
        detects anomalies, and exports polished reports — instantly.
    </p>
</div>
""", unsafe_allow_html=True)

_, col_card, _ = st.columns([1, 1.6, 1])
with col_card:
    tab_user, tab_admin = st.tabs(["🚀 User Login", "👑 Admin"])

    with tab_user:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Get started or Log in</div>
            <div class="email-card-sub">Enter your email and password — new accounts are created automatically.</div>
            <br>
        """, unsafe_allow_html=True)

        email_input = st.text_input("Email", placeholder="you@company.com", key="user_email")
        password_input = st.text_input("Password", type="password", placeholder="Enter your password", key="user_password")

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        go_btn = st.button("Continue  →", use_container_width=True, key="login_btn")
        st.markdown('</div></div>', unsafe_allow_html=True)

        col_fp, col_pr = st.columns(2)
        with col_fp:
            if st.button("🔑 Forgot password?", use_container_width=True):
                st.switch_page("pages/2_Reset_Password.py")
        with col_pr:
            if st.button("💎 View Pricing", use_container_width=True):
                st.switch_page("pages/5_Pricing.py")

        if go_btn:
            raw_email = email_input.strip().lower()
            raw_pass = password_input.strip()

            if st.session_state.get("login_attempts", 0) >= 5:
                st.error("⛔ Too many failed attempts. Please refresh the page.")
                st.stop()

            email_pattern = r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$"

            if not re.match(email_pattern, raw_email):
                st.error("⚠️ Please enter a valid email address.")
            elif not raw_pass:
                st.error("⚠️ Please enter a password.")
            else:
                blocked_domains = ["test.com", "example.com", "fake.com", "mailinator.com", "tempmail.com"]
                if raw_email.split('@')[-1] in blocked_domains:
                    st.error("⚠️ Please use a real personal or work email address.")
                else:
                    with st.spinner("Authenticating securely..."):
                        user = verify_or_create_user(raw_email, raw_pass)
                        time.sleep(0.4)

                    if user is False:
                        st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
                        st.error(f"❌ Incorrect password. (Attempt {st.session_state['login_attempts']}/5)")
                    else:
                        st.session_state["login_attempts"] = 0
                        st.session_state["email"] = raw_email
                        st.session_state["user"] = user

                        if user.get("has_payment_on_file") and not is_account_expired(user):
                            st.switch_page("pages/3_App.py")
                        st.switch_page("pages/1_Start_Trial.py")

    with tab_admin:
        st.markdown("""
        <div class="email-card">
            <div class="email-card-title">Admin Access</div>
            <div class="email-card-sub">Restricted to authorized administrators only.</div>
            <br>
        """, unsafe_allow_html=True)

        admin_email = st.text_input("Admin Email", placeholder="admin@domain.com", key="admin_email")
        admin_pass = st.text_input("Password", type="password", key="admin_pass")

        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        admin_btn = st.button("Unlock Dashboard  →", use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if admin_btn:
            clean_email = admin_email.strip().lower()
            expected_admin_email = st.secrets.get("ADMIN_EMAIL")
            expected_admin_pass = st.secrets.get("ADMIN_PASS")

            if not expected_admin_email or not expected_admin_pass:
                st.error("❌ Admin credentials not configured in Streamlit Secrets.")
            else:
                email_ok = hmac.compare_digest(clean_email, expected_admin_email.lower())
                pass_ok = hmac.compare_digest(admin_pass, expected_admin_pass)

                if email_ok and pass_ok:
                    st.session_state["email"] = clean_email
                    st.session_state["user"] = {
                        "email": clean_email,
                        "plan_type": "pro",
                        "has_payment_on_file": True,
                        "expiry_date": None
                    }
                    st.session_state["is_admin"] = True
                    st.success("✅ Access granted!")
                    time.sleep(0.8)
                    st.switch_page("pages/4_Admin_Portal.py")
                else:
                    st.error("❌ Access Denied.")

# Feature Strip
st.markdown("""
<div class="feature-strip">
    <div class="feature-item">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">AI Data Analyst</div>
        <div class="feature-desc">Ask anything in plain English. Nexus writes and runs the code for you.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Interactive Charts</div>
        <div class="feature-desc">Zoomable, hoverable Plotly charts generated on demand.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">🧹</div>
        <div class="feature-title">Data Cleaning</div>
        <div class="feature-desc">Auto-detect nulls, duplicates, outliers — one-click fix.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">Anomaly Detection</div>
        <div class="feature-desc">IQR-based outlier scoring across every numeric column.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">📄</div>
        <div class="feature-title">HTML Reports</div>
        <div class="feature-desc">Export your full session as a shareable HTML report.</div>
    </div>
    <div class="feature-item">
        <div class="feature-icon">💡</div>
        <div class="feature-title">Smart Suggestions</div>
        <div class="feature-desc">AI auto-generates 8 smart questions from your data schema.</div>
    </div>
</div>

<div class="trust-bar">
    <p>Built for professionals</p>
    <div class="trust-pills">
        <span class="trust-pill">Plotly Charts</span>
        <span class="trust-pill">Anomaly Detection</span>
        <span class="trust-pill">Correlation Matrix</span>
        <span class="trust-pill">Multi-Sheet Excel</span>
        <span class="trust-pill">Analysis History</span>
        <span class="trust-pill">Query Bookmarks</span>
        <span class="trust-pill">HTML Export</span>
        <span class="trust-pill">Data Cleaning</span>
    </div>
</div>
""", unsafe_allow_html=True)
