"""
pages/2_Reset_Password.py — Nexus Excel AI v5.0 · Password Reset
"""

import streamlit as st
import sys, os, time, secrets
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import get_user, hash_password, supabase
from styles import GLOBAL_CSS

st.set_page_config(
    page_title="Nexus Excel AI — Reset Password",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.reset-wrap { max-width: 480px; margin: 4rem auto; animation: fadeUp 0.35s ease both; }
.reset-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="reset-wrap">', unsafe_allow_html=True)
st.markdown("""
<div class="reset-card">
    <div style="font-size:3rem; margin-bottom:1rem;">🔑</div>
    <h3 style="font-family:var(--font-mono); color:var(--text-primary); margin-bottom:0.4rem;">Reset Password</h3>
    <p style="color:var(--text-muted); font-size:0.875rem; margin-bottom:1.5rem;">
        Enter your email and a new password. Your account must already exist.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.form("reset_form"):
    r_email = st.text_input("Email Address", placeholder="you@company.com")
    r_new_pass = st.text_input("New Password", type="password", placeholder="At least 8 characters")
    r_confirm_pass = st.text_input("Confirm New Password", type="password", placeholder="Re-enter password")

    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    reset_btn = st.form_submit_button("Reset Password  →", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if reset_btn:
        email_clean = r_email.strip().lower()
        if not email_clean or not r_new_pass or not r_confirm_pass:
            st.error("⚠️ All fields are required.")
        elif len(r_new_pass) < 8:
            st.error("⚠️ Password must be at least 8 characters.")
        elif r_new_pass != r_confirm_pass:
            st.error("⚠️ Passwords do not match.")
        elif not supabase:
            st.error("❌ No database connection. Cannot reset password.")
        else:
            user = get_user(email_clean)
            if not user:
                st.error("❌ No account found with this email address.")
            else:
                try:
                    new_hash = hash_password(r_new_pass)
                    supabase.table("users").update({"password": new_hash}).eq("email", email_clean).execute()
                    st.success("✅ Password updated successfully!")
                    time.sleep(1.5)
                    st.switch_page("Home.py")
                except Exception as e:
                    st.error(f"❌ Failed to update password: {e}")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("← Back to Login", use_container_width=True):
    st.switch_page("Home.py")

st.markdown('</div>', unsafe_allow_html=True)
