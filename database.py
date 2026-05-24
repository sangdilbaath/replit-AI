"""
pages/4_Admin_Portal.py — Nexus Excel AI v5.0 · Admin Portal
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import (get_admin_stats, admin_create_user, block_user_trial,
                      PLAN_LABELS, supabase, get_all_users, is_account_expired)
from styles import GLOBAL_CSS
import pandas as pd

st.set_page_config(
    page_title="Nexus Excel AI — Admin Portal",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.admin-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 30px rgba(0,0,0,0.3);
}
.admin-card-title { font-family: var(--font-mono); font-size: 1.1rem; color: var(--accent); margin-bottom: 0.75rem; }
.admin-stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
}
.admin-stat-val { font-family: var(--font-mono); font-size: 2rem; color: var(--text-primary); font-weight: 700; }
.admin-stat-lbl { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("is_admin", False):
    st.switch_page("Home.py")

st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
    <div style="display:inline-block; background:#f8514922; border:1px solid #f8514960; border-radius:20px;
                padding:0.3rem 1rem; font-size:0.75rem; color:#f85149; font-family:var(--font-mono);
                letter-spacing:2px; margin-bottom:1.5rem; text-transform:uppercase; font-weight:bold;">
        👑 Master Administrator Mode
    </div>
    <h2 style="font-family:'Space Mono',monospace; color:var(--text-primary); margin:0;">
        Nexus Control Panel
    </h2>
    <p style="color:var(--text-muted); font-size:0.875rem;">
        Monitor accounts, provision licenses, and manage all users.
    </p>
</div>
""", unsafe_allow_html=True)

if not supabase:
    st.warning("⚠️ Supabase is inactive. Configure SUPABASE_URL and SUPABASE_KEY in secrets.", icon="⚠️")

tab_stats, tab_provision, tab_users, tab_revoke = st.tabs([
    "📊 Statistics", "🚀 Provision User", "👥 All Users", "🚫 Revoke Access"
])

with tab_stats:
    stats = get_admin_stats()
    total_users = stats.get("total_users", 0)
    plans = stats.get("plans", {})

    st.markdown('<div class="section-label">Realtime Statistics</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    stat_items = [
        (total_users, "Total Accounts"),
        (plans.get("trial", 0) + plans.get("free_trial", 0), "Active Trials"),
        (plans.get("basic", 0), "Basic Tier"),
        (plans.get("premium", 0), "Premium Tier"),
        (plans.get("pro", 0), "Pro Tier"),
    ]
    for col, (val, lbl) in zip(cols, stat_items):
        with col:
            st.markdown(f"""
            <div class="admin-stat-card">
                <div class="admin-stat-val">{val}</div>
                <div class="admin-stat-lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    if plans:
        st.markdown('<div class="section-label">Plan Distribution</div>', unsafe_allow_html=True)
        plan_data = {PLAN_LABELS.get(k, k): v for k, v in plans.items()}
        plan_df = pd.DataFrame(list(plan_data.items()), columns=["Plan", "Users"])
        st.bar_chart(plan_df.set_index("Plan"))

with tab_provision:
    st.markdown("""
    <div class="admin-card">
        <div class="admin-card-title">🚀 Provision User License</div>
        <p style="color:var(--text-muted); font-size:0.8rem; line-height:1.5; margin-bottom:1rem;">
            Register a new client or update an existing account plan and duration.
            Passwords are hashed automatically.
        </p>
    """, unsafe_allow_html=True)

    with st.form("provision_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            p_email = st.text_input("User Email", placeholder="client@company.com")
            p_plan = st.selectbox("Plan Tier", ["trial", "free_trial", "basic", "premium", "pro"],
                                  format_func=lambda x: PLAN_LABELS.get(x, x))
        with col_b:
            p_pass = st.text_input("Temporary Password", placeholder="secure1234", type="password")
            p_dur = st.number_input("License Duration (Days)", min_value=1, max_value=3650, value=30)

        prov_btn = st.form_submit_button("Grant Access License ➔", use_container_width=True)

        if prov_btn:
            if not p_email.strip() or not p_pass.strip():
                st.error("❌ Email and password are required.")
            elif not supabase:
                st.error("❌ Supabase inactive.")
            else:
                with st.spinner("Writing to database..."):
                    success = admin_create_user(p_email.strip().lower(), p_pass.strip(), p_plan, int(p_dur))
                if success:
                    st.success(f"✅ '{PLAN_LABELS[p_plan]}' plan assigned to {p_email} for {p_dur} days.")
                else:
                    st.error("❌ Database rejected entry.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab_users:
    st.markdown('<div class="section-label">All Registered Users</div>', unsafe_allow_html=True)

    if not supabase:
        st.info("Connect Supabase to view user records.")
    else:
        users = get_all_users(limit=500)
        if not users:
            st.info("No users found.")
        else:
            rows = []
            for u in users:
                exp = u.get("expiry_date", "—")
                plan = u.get("plan_type", "none")
                status = "Active"
                if exp and exp != "—":
                    from database import is_account_expired as _exp
                    if _exp(u):
                        status = "Expired"
                rows.append({
                    "Email": u.get("email", ""),
                    "Plan": PLAN_LABELS.get(plan, plan),
                    "Status": status,
                    "Expiry": str(exp)[:10] if exp else "No expiry",
                    "Trial Started": str(u.get("trial_start_date", "—"))[:10] if u.get("trial_start_date") else "—",
                })

            df_users = pd.DataFrame(rows)
            col_search, _ = st.columns([1, 2])
            with col_search:
                search = st.text_input("🔍 Filter by email", placeholder="Search...")
            if search:
                df_users = df_users[df_users["Email"].str.contains(search, case=False, na=False)]

            st.dataframe(df_users, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df_users)} user(s)")

with tab_revoke:
    st.markdown("""
    <div class="admin-card">
        <div class="admin-card-title">🚫 Revoke Access / Block Account</div>
        <p style="color:var(--text-muted); font-size:0.8rem; line-height:1.5; margin-bottom:1rem;">
            Instantly force an account to expire, immediately blocking all AI dashboard access.
        </p>
    """, unsafe_allow_html=True)

    with st.form("revoke_form", clear_on_submit=True):
        r_email = st.text_input("Target User Email", placeholder="user@company.com")
        st.warning("⚠️ This action immediately locks the user out. It cannot be undone without re-provisioning.")
        revoke_btn = st.form_submit_button("🚫 Revoke Access ➔", use_container_width=True)

        if revoke_btn:
            if not r_email.strip():
                st.error("❌ Email is required.")
            elif not supabase:
                st.error("❌ Supabase inactive.")
            else:
                with st.spinner("Revoking access..."):
                    success = block_user_trial(r_email.strip().lower())
                if success:
                    st.success(f"✅ Access revoked for {r_email}.")
                else:
                    st.error("❌ Failed. User may not exist.")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns([6, 1])
with col_right:
    if st.button("→ AI Dashboard", use_container_width=True):
        st.switch_page("pages/3_App.py")
