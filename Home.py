"""
pages/3_App.py — Nexus Excel AI v5.0 · Main AI Dashboard
Features: AI Chat, Plotly Charts, Data Cleaning, Column Deep-Dive,
          Anomaly Detection, Correlation Matrix, Suggested Questions,
          Templates, History, Bookmarks, HTML Export, Multi-Sheet Excel.
"""

import streamlit as st
import sys, os, re, io, time, datetime, concurrent.futures, traceback, json, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    SEABORN_OK = True
except ImportError:
    SEABORN_OK = False

from database import (
    is_account_expired, days_remaining, PLAN_LABELS, PLAN_LIMITS,
    save_analysis, get_user_analyses,
    save_bookmark, get_bookmarks, delete_bookmark
)
from styles import GLOBAL_CSS, APP_CSS

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS, unsafe_allow_html=True)

# ── Access Control ────────────────────────────────────────────
is_admin = st.session_state.get("is_admin", False)
user = st.session_state.get("user")

if not user:
    st.switch_page("Home.py")

if is_admin:
    plan = "pro"
    account_exp = False
else:
    from database import get_user
    email = st.session_state.get("email", user.get("email", ""))
    if email:
        fresh = get_user(email)
        if fresh:
            user = fresh
            st.session_state["user"] = fresh

    if not user.get("has_payment_on_file"):
        st.switch_page("pages/1_Start_Trial.py")

    plan = user.get("plan_type", "none")
    account_exp = is_account_expired(user)

if account_exp:
    st.markdown("""
    <div style="text-align:center; padding:5rem 1rem;">
        <div style="font-size:3rem;">⏰</div>
        <h2 style="font-family:'Space Mono',monospace; color:var(--nexus-text-primary); margin:1rem 0 0.5rem 0;">
            Your access has expired.
        </h2>
        <p style="color:var(--nexus-text-muted); font-size:1rem; max-width:460px; margin:0 auto 2rem auto;">
            Contact your administrator or upgrade your plan to continue.
        </p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("💎 View Plans", use_container_width=True):
            st.switch_page("pages/5_Pricing.py")
    st.stop()

# ── Constants ─────────────────────────────────────────────────
MAX_FILE_MB = 25
MAX_REQUESTS = PLAN_LIMITS.get(plan, 30) if not is_admin else 999999
AI_TIMEOUT = 35
PYTHON_KWS = {'import','def','df','plt','pd','for','if','print','return','=','fig','ax','px','go'}

SAMPLE_DATASETS = {
    "📦 E-Commerce Sales": {
        "desc": "Monthly sales data by product, region, and channel",
        "gen": lambda: pd.DataFrame({
            "Month": pd.date_range("2024-01-01", periods=24, freq="MS"),
            "Product": np.random.choice(["Laptop","Phone","Tablet","Watch","Earbuds"], 24),
            "Region": np.random.choice(["North","South","East","West"], 24),
            "Units_Sold": np.random.randint(50, 800, 24),
            "Revenue_USD": np.random.randint(5000, 120000, 24),
            "Returns": np.random.randint(0, 50, 24),
            "Channel": np.random.choice(["Online","Retail","Wholesale"], 24),
        })
    },
    "👥 HR Analytics": {
        "desc": "Employee data with performance, salary, and attrition",
        "gen": lambda: pd.DataFrame({
            "Employee_ID": range(1, 201),
            "Department": np.random.choice(["Engineering","Sales","HR","Finance","Marketing"], 200),
            "Age": np.random.randint(22, 62, 200),
            "Salary_USD": np.random.randint(35000, 180000, 200),
            "Years_at_Company": np.random.randint(0, 20, 200),
            "Performance_Score": np.random.uniform(1.0, 5.0, 200).round(1),
            "Left_Company": np.random.choice(["Yes","No"], 200, p=[0.15, 0.85]),
        })
    },
    "💹 Financial Data": {
        "desc": "Stock prices and volume data across multiple tickers",
        "gen": lambda: pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=100),
            "Ticker": np.random.choice(["AAPL","GOOGL","MSFT","TSLA","AMZN"], 100),
            "Open": np.random.uniform(100, 400, 100).round(2),
            "Close": np.random.uniform(100, 400, 100).round(2),
            "High": np.random.uniform(110, 420, 100).round(2),
            "Low": np.random.uniform(90, 380, 100).round(2),
            "Volume": np.random.randint(1000000, 50000000, 100),
        })
    },
    "🏪 Retail Inventory": {
        "desc": "Product inventory and restock tracking",
        "gen": lambda: pd.DataFrame({
            "SKU": [f"SKU-{i:04d}" for i in range(1, 151)],
            "Category": np.random.choice(["Electronics","Clothing","Food","Toys","Sports"], 150),
            "Stock_Units": np.random.randint(0, 500, 150),
            "Reorder_Point": np.random.randint(20, 100, 150),
            "Unit_Cost_USD": np.random.uniform(2.5, 250.0, 150).round(2),
            "Days_Since_Restock": np.random.randint(0, 90, 150),
            "Supplier": np.random.choice(["SupplierA","SupplierB","SupplierC"], 150),
        })
    },
}

ANALYSIS_TEMPLATES = [
    {"icon": "📊", "title": "Monthly Revenue Trend", "prompt": "Create an interactive line chart showing revenue trend over time. Add a title and format the y-axis as currency."},
    {"icon": "🥧", "title": "Category Breakdown", "prompt": "Show the distribution of the main categorical column as an interactive pie chart with percentages."},
    {"icon": "🔝", "title": "Top 10 by Value", "prompt": "Find the top 10 rows by the highest numeric column and show them as a horizontal bar chart."},
    {"icon": "📉", "title": "Statistical Summary", "prompt": "Give me a full statistical summary of all numeric columns including mean, median, std, min, max, and percentiles."},
    {"icon": "🔗", "title": "Scatter: Two Variables", "prompt": "Create an interactive scatter plot of the two most important numeric columns. Color points by the main categorical column if available."},
    {"icon": "📦", "title": "Box Plot Distribution", "prompt": "Show the distribution of the main numeric column as a box plot grouped by the main categorical column."},
    {"icon": "⚠️", "title": "Missing Values Report", "prompt": "Identify all columns with missing values, show the count and percentage for each, and suggest the best fill strategy."},
    {"icon": "📆", "title": "Time Series Analysis", "prompt": "If there is a date column, plot a time series trend and highlight the highest and lowest points. Add a 7-period rolling average."},
    {"icon": "🏆", "title": "Group Comparison", "prompt": "Compare average values of all numeric columns across each category in the main categorical column. Show as a grouped bar chart."},
    {"icon": "📐", "title": "Data Quality Report", "prompt": "Run a full data quality assessment: row count, null rates, duplicate rows, data types, and any suspicious values per column."},
]

# ── Session State ─────────────────────────────────────────────
_defaults = {
    "query_text": "", "updated_df": None, "chart_gallery": [],
    "command_history": [], "chat_history": [], "df": None,
    "last_filename": None, "show_all_data": False, "show_all_cols": False,
    "request_count": 0, "suggested_questions": [], "auto_summary": "",
    "active_tab": "analyze", "selected_sheet": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────
def clean_ai_code(raw: str) -> str:
    m = re.search(r"```python\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    if m: return m.group(1).strip()
    m = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
    if m: return m.group(1).strip()
    return raw.strip()

def is_likely_python(code: str) -> bool:
    return any(kw in code for kw in PYTHON_KWS)

def sanitize_col(name: str) -> str:
    return re.sub(r"[^\w\s\-\.]", "_", str(name))

def get_df_summary(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        safe = sanitize_col(col)
        dtype = str(df[col].dtype)
        nulls = int(df[col].isnull().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            d = df[col].describe()
            stats = f"min={d['min']:.2f}, max={d['max']:.2f}, mean={d['mean']:.2f}, std={d.get('std',0):.2f}"
        else:
            top5 = df[col].dropna().astype(str).value_counts().head(5).index.tolist()
            stats = "top: " + ", ".join(top5)
        lines.append(f"- `{safe}` ({dtype}, {nulls} nulls) → {stats}")
    return "\n".join(lines)

def render_metrics(df: pd.DataFrame):
    num_cols = df.select_dtypes(include='number').shape[1]
    missing_pct = round(df.isnull().mean().mean() * 100, 1) if not df.empty else 0.0
    dupe_count = int(df.duplicated().sum())
    mem_kb = round(df.memory_usage(deep=True).sum() / 1024, 1)
    mem_str = f"{round(mem_kb/1024,2)} MB" if mem_kb >= 1024 else f"{mem_kb} KB"
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card"><div class="label">Rows</div><div class="value">{df.shape[0]:,}</div><div class="sub">records</div></div>
        <div class="metric-card"><div class="label">Columns</div><div class="value">{df.shape[1]}</div><div class="sub">{num_cols} numeric</div></div>
        <div class="metric-card"><div class="label">Missing</div><div class="value">{missing_pct}<span class="unit">%</span></div><div class="sub">null rate</div></div>
        <div class="metric-card"><div class="label">Duplicates</div><div class="value">{dupe_count}</div><div class="sub">duplicate rows</div></div>
        <div class="metric-card"><div class="label">Memory</div><div class="value">{mem_str}</div><div class="sub">in use</div></div>
    </div>
    """, unsafe_allow_html=True)

def load_file(uploaded_file):
    name = uploaded_file.name
    if name.endswith('.csv'):
        raw = uploaded_file.read()
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=enc, parse_dates=True), None
            except Exception:
                continue
        raise ValueError("Could not decode CSV.")
    else:
        xl = pd.ExcelFile(uploaded_file)
        sheets = xl.sheet_names
        return xl, sheets

def load_sheet(xl, sheet: str) -> pd.DataFrame:
    df = xl.parse(sheet, parse_dates=True)
    if df.columns.duplicated().any() or df.columns.isnull().any():
        st.warning("Merged or unnamed header cells detected. Consider un-merging headers in Excel.", icon="⚠️")
    for col in df.select_dtypes(include='object').columns:
        try:
            converted = pd.to_datetime(df[col], errors='coerce')
            if converted.notna().sum() / max(len(df), 1) > 0.7:
                df[col] = converted
        except Exception:
            pass
    return df

def call_ai(client, prompt: str, timeout: int = AI_TIMEOUT) -> str:
    def _call():
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        ).text
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_call)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"AI did not respond within {timeout}s.")

def classify_query(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ['chart','plot','graph','visuali','bar','line','scatter','histogram','heatmap']):
        return "chart"
    if any(w in q for w in ['filter','where','remove','drop','clean','deduplic','fix','fill']):
        return "transform"
    if any(w in q for w in ['predict','forecast','trend','regression','correlat','model']):
        return "model"
    if any(w in q for w in ['summar','describ','overview','what is','tell me','show me']):
        return "summary"
    return "analysis"

def trim_memory():
    if len(st.session_state.command_history) > 60:
        st.session_state.command_history = st.session_state.command_history[-60:]
    if len(st.session_state.chart_gallery) > 15:
        st.session_state.chart_gallery = st.session_state.chart_gallery[-15:]
    if len(st.session_state.chat_history) > 20:
        st.session_state.chat_history = st.session_state.chat_history[-20:]

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    num_df = df.select_dtypes(include='number')
    if num_df.empty:
        return pd.DataFrame()
    results = []
    for col in num_df.columns:
        s = num_df[col].dropna()
        if len(s) < 4:
            continue
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        IQR = Q3 - Q1
        if IQR == 0:
            continue
        lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        mask = (df[col] < lo) | (df[col] > hi)
        n = int(mask.sum())
        if n > 0:
            results.append({
                "Column": col,
                "Outliers": n,
                "Pct of Rows": f"{n/len(df)*100:.1f}%",
                "Lower Fence": f"{lo:.2f}",
                "Upper Fence": f"{hi:.2f}",
                "Min Outlier": f"{df.loc[mask, col].min():.2f}",
                "Max Outlier": f"{df.loc[mask, col].max():.2f}",
            })
    return pd.DataFrame(results) if results else pd.DataFrame()

def generate_html_report(df: pd.DataFrame, chat_history: list, charts: list, filename: str, auto_summary: str) -> str:
    rows_html = ""
    for msg in chat_history:
        role_label = "You" if msg["role"] == "user" else "Nexus AI"
        role_color = "#00d4aa" if msg["role"] == "assistant" else "#e6edf3"
        rows_html += f"""
        <div style="margin-bottom:1rem; padding:0.85rem 1.25rem;
                    background:{'#1c2333' if msg['role']=='assistant' else '#161b22'};
                    border-radius:10px; border-left:3px solid {role_color};">
            <div style="font-size:0.72rem; color:#8b949e; margin-bottom:0.4rem; text-transform:uppercase; letter-spacing:1px;">{role_label}</div>
            <div style="color:#e6edf3; font-size:0.9rem; line-height:1.6; white-space:pre-wrap;">{msg['content'][:2000]}</div>
        </div>"""

    summary_section = f"""
    <div style="background:#1c2333; border:1px solid rgba(0,212,170,0.3); border-radius:10px; padding:1.25rem; margin-bottom:1.5rem;">
        <div style="font-family:monospace; font-size:0.8rem; color:#00d4aa; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px;">◈ AI Data Summary</div>
        <div style="color:#e6edf3; font-size:0.9rem; line-height:1.7;">{auto_summary.replace(chr(10), '<br>')}</div>
    </div>""" if auto_summary else ""

    stats_html = df.describe(include='all').to_html(classes="stats-table", border=0)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nexus AI Report — {filename}</title>
<style>
*{{box-sizing:border-box; margin:0; padding:0;}}
body{{background:#0d1117; color:#e6edf3; font-family:'Segoe UI',sans-serif; padding:2rem;}}
h1{{font-family:monospace; color:#00d4aa; font-size:1.8rem; margin-bottom:0.5rem;}}
h2{{font-family:monospace; color:#e6edf3; font-size:1.1rem; margin:2rem 0 1rem 0; border-bottom:1px solid #30363d; padding-bottom:0.5rem;}}
.meta{{color:#8b949e; font-size:0.8rem; margin-bottom:2rem;}}
.stats-table{{width:100%; border-collapse:collapse; font-size:0.8rem; margin-bottom:1.5rem;}}
.stats-table th{{background:#161b22; color:#00d4aa; padding:0.5rem 0.75rem; text-align:left; font-family:monospace;}}
.stats-table td{{padding:0.4rem 0.75rem; border-bottom:1px solid #30363d; color:#e6edf3;}}
.stats-table tr:hover td{{background:#1c2333;}}
</style>
</head>
<body>
<h1>◈ NEXUS Excel AI — Analysis Report</h1>
<div class="meta">
    File: <strong>{filename}</strong> &nbsp;·&nbsp;
    Rows: <strong>{len(df):,}</strong> &nbsp;·&nbsp;
    Columns: <strong>{df.shape[1]}</strong> &nbsp;·&nbsp;
    Generated: <strong>{datetime.datetime.now().strftime("%B %d, %Y at %H:%M")}</strong>
</div>
{summary_section}
<h2>Dataset Statistics</h2>
{stats_html}
<h2>AI Conversation ({len(chat_history)} messages)</h2>
{rows_html if rows_html else '<p style="color:#8b949e;">No conversation recorded.</p>'}
<br><hr style="border-color:#30363d; margin:2rem 0;">
<div style="color:#8b949e; font-size:0.72rem; text-align:center;">Generated by Nexus Excel AI v5.0</div>
</body>
</html>"""

# ── Sidebar ───────────────────────────────────────────────────
plan_label = PLAN_LABELS.get(plan, plan)
trial_days = days_remaining(user) if "trial" in plan else None

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo">◈ NEXUS</div>
        <div class="tagline">Excel AI · v5.0</div>
    </div>
    """, unsafe_allow_html=True)

    if is_admin:
        st.markdown("""
        <div style="background:rgba(248,81,73,0.1); border:1px solid rgba(248,81,73,0.3);
                    border-radius:8px; padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
            <span style="font-size:0.75rem; color:#f85149; text-transform:uppercase; letter-spacing:1px; font-weight:700;">
                👑 Master Key Active
            </span>
        </div>
        """, unsafe_allow_html=True)

    plan_color = {"trial":"var(--warning)","free_trial":"var(--warning)","basic":"#8b949e","premium":"#0099ff","pro":"var(--nexus-accent)"}.get(plan, "#8b949e")
    trial_info = f" · {trial_days}d left" if trial_days is not None else ""
    st.markdown(f"""
    <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:8px;
                padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
        <span style="font-size:0.7rem; color:var(--nexus-text-muted); text-transform:uppercase; letter-spacing:1px;">Active Plan</span><br>
        <span style="font-family:'Space Mono',monospace; color:{plan_color}; font-weight:700;">{plan_label}{trial_info}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza…",
                            help="Get your key at aistudio.google.com")

    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload file",
        type=["xlsx", "xls", "csv"],
        label_visibility="collapsed",
        help="CSV or Excel (.xlsx/.xls) · Max 25 MB"
    )

    st.markdown('<div class="section-label">Or Use Sample Data</div>', unsafe_allow_html=True)
    sample_choice = st.selectbox(
        "Sample dataset",
        ["— None —"] + list(SAMPLE_DATASETS.keys()),
        label_visibility="collapsed"
    )

    st.markdown('<div class="section-label">Controls</div>', unsafe_allow_html=True)
    if st.button("🗑️ Reset Session", use_container_width=True):
        for k in ["updated_df","chart_gallery","query_text","command_history",
                  "chat_history","df","last_filename","show_all_data","show_all_cols",
                  "request_count","suggested_questions","auto_summary","selected_sheet"]:
            st.session_state[k] = [] if k in ("command_history","chart_gallery","chat_history","suggested_questions") \
                                   else "" if k in ("query_text","auto_summary") \
                                   else 0 if k == "request_count" \
                                   else False if k in ("show_all_data","show_all_cols") \
                                   else None
        st.rerun()

    if st.session_state.command_history:
        st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
        with st.expander(f"📝 {len(st.session_state.command_history)} command(s)", expanded=False):
            for entry in reversed(st.session_state.command_history[-20:]):
                badge = '<span class="audit-badge-ok">✓ OK</span>' if entry["ok"] \
                   else '<span class="audit-badge-err">✗ Fail</span>'
                st.markdown(f"""
                <div class="audit-item">
                    <div class="audit-cmd">{entry["cmd"][:80]}</div>
                    <div class="audit-meta">{badge}<span style="font-size:0.65rem;">{entry["ts"]}</span></div>
                </div>""", unsafe_allow_html=True)

    remaining = MAX_REQUESTS - st.session_state.request_count
    limit_txt = "◈ Unlimited requests" if is_admin else f"◈ {remaining}/{MAX_REQUESTS} requests left"
    st.markdown(f'<div class="rate-limit-badge">{limit_txt}</div>', unsafe_allow_html=True)

    if is_admin:
        st.divider()
        if st.button("← Admin Portal", use_container_width=True):
            st.switch_page("pages/4_Admin_Portal.py")

    st.divider()
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Home.py")

# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero-zone fade-up">
    <div class="hero-title">◈ NEXUS Excel AI</div>
    <div class="hero-sub">Professional Spreadsheet Intelligence Engine · v5.0</div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
    <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:12px;
                padding:2.5rem; text-align:center; margin-top:2rem;">
        <div style="font-size:2.5rem; margin-bottom:0.75rem;">🔑</div>
        <div style="font-family:'Space Mono',monospace; color:var(--nexus-text-primary); font-size:1rem;">API Key Required</div>
        <div style="color:var(--nexus-text-muted); font-size:0.875rem; margin-top:0.5rem;">
            Enter your <strong>Gemini API Key</strong> in the sidebar to activate Nexus AI.<br>
            Get a free key at <strong>aistudio.google.com</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Google Gemini Client ──────────────────────────────────────
try:
    from google import genai
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Could not initialise Gemini client: {e}")
    st.stop()

# ── Load Data ─────────────────────────────────────────────────
active_df = None

if sample_choice != "— None —" and not uploaded_file:
    sample = SAMPLE_DATASETS[sample_choice]
    if st.session_state.last_filename != sample_choice:
        df_gen = sample["gen"]()
        st.session_state.df = df_gen
        st.session_state.updated_df = df_gen.copy()
        st.session_state.last_filename = sample_choice
        st.session_state.chart_gallery = []
        st.session_state.chat_history = []
        st.session_state.suggested_questions = []
        st.session_state.auto_summary = ""
        st.session_state.selected_sheet = None
        st.success(f"✅ Sample dataset loaded: {sample_choice} — {sample['desc']}")

elif uploaded_file is not None:
    if st.session_state.last_filename != uploaded_file.name:
        with st.spinner("Processing file..."):
            try:
                result, sheets = load_file(uploaded_file)
                if sheets is None:
                    df = result
                    st.session_state.df = df
                    st.session_state.updated_df = df.copy()
                    st.session_state.last_filename = uploaded_file.name
                    st.session_state.chart_gallery = []
                    st.session_state.chat_history = []
                    st.session_state.suggested_questions = []
                    st.session_state.auto_summary = ""
                    st.session_state.selected_sheet = None
                    st.success(f"✅ Loaded {uploaded_file.name}")
                else:
                    st.session_state["_xl_object"] = result
                    st.session_state["_xl_sheets"] = sheets
                    st.session_state.last_filename = uploaded_file.name
                    st.session_state.selected_sheet = sheets[0]
                    st.success(f"✅ Excel workbook loaded — {len(sheets)} sheet(s) found")
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    if st.session_state.get("_xl_sheets"):
        sheets = st.session_state["_xl_sheets"]
        sheet_choice = st.selectbox("📋 Select sheet to analyze:", sheets,
                                    index=sheets.index(st.session_state.selected_sheet) if st.session_state.selected_sheet in sheets else 0)
        if sheet_choice != st.session_state.selected_sheet:
            st.session_state.selected_sheet = sheet_choice
            st.session_state.suggested_questions = []
            st.session_state.auto_summary = ""
        df = load_sheet(st.session_state["_xl_object"], st.session_state.selected_sheet)
        st.session_state.df = df
        st.session_state.updated_df = df.copy()

if st.session_state.df is not None:
    active_df = st.session_state.updated_df if st.session_state.updated_df is not None else st.session_state.df

if active_df is None:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem; color:var(--nexus-text-muted);">
        <div style="font-size:3rem; margin-bottom:1rem;">📂</div>
        <div style="font-family:'Space Mono',monospace; font-size:1rem; color:var(--nexus-text-primary);">No data loaded</div>
        <div style="font-size:0.875rem; margin-top:0.5rem;">Upload a CSV or Excel file — or choose a sample dataset from the sidebar.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Auto-generate Suggested Questions ─────────────────────────
if active_df is not None and not st.session_state.suggested_questions and api_key:
    with st.spinner("◈ Generating smart questions from your data..."):
        try:
            df_sum = get_df_summary(active_df)
            q_prompt = f"""You are an expert data analyst. Given this dataset schema, generate exactly 8 short, 
specific, and insightful analysis questions a business user would ask. 
Return ONLY a JSON array of 8 strings. No explanation, no markdown, just the JSON array.

Dataset schema:
{df_sum}
Total rows: {len(active_df):,}"""
            raw_q = call_ai(client, q_prompt, timeout=20)
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_q).strip()
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                st.session_state.suggested_questions = [str(q) for q in parsed[:8]]
        except Exception:
            st.session_state.suggested_questions = [
                "What are the key trends in this dataset?",
                "Which column has the most missing values?",
                "Show me the top 10 rows by the highest numeric value.",
                "Create a chart showing distribution of the main numeric column.",
                "Are there any outliers or anomalies in the data?",
                "What is the correlation between numeric columns?",
                "Give me a full statistical summary.",
                "Which category appears most frequently?",
            ]

# ── Auto Summary ──────────────────────────────────────────────
if active_df is not None and not st.session_state.auto_summary and api_key:
    with st.spinner("◈ Generating data summary..."):
        try:
            df_sum = get_df_summary(active_df)
            sum_prompt = f"""You are Nexus AI. Write a 3-sentence executive summary of this dataset.
Be specific — mention actual column names, data types, row counts, and any notable patterns.
Keep it professional and concise. Do not use markdown headers or bullet points.

Schema:
{df_sum}
Rows: {len(active_df):,} | Columns: {active_df.shape[1]}"""
            st.session_state.auto_summary = call_ai(client, sum_prompt, timeout=15)
        except Exception:
            st.session_state.auto_summary = ""

# ── Dataset Overview ──────────────────────────────────────────
render_metrics(active_df)

if st.session_state.auto_summary:
    st.markdown(f"""
    <div class="insight-card">
        <h4>◈ AI Data Summary</h4>
        <p>{st.session_state.auto_summary}</p>
    </div>
    """, unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────
tab_analyze, tab_clean, tab_explore, tab_history, tab_bookmarks = st.tabs([
    "💬 AI Analyze", "🧹 Clean Data", "📊 Explore", "📚 History", "🔖 Bookmarks"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1: AI ANALYZE
# ═══════════════════════════════════════════════════════════════
with tab_analyze:
    st.markdown('<div class="section-label">Dataset Preview</div>', unsafe_allow_html=True)
    show_all = st.checkbox("Show all rows", value=False)
    preview = active_df if show_all else active_df.head(15)
    st.dataframe(preview, use_container_width=True)

    col_expand, _ = st.columns([2, 4])
    with col_expand:
        show_cols = st.checkbox("Show all column pills", value=False)
    pills_html = f'<div class="col-pills-wrap {"expanded" if show_cols else ""}">'
    for c in active_df.columns:
        pills_html += f'<span class="col-pill">{sanitize_col(c)} ({str(active_df[c].dtype)})</span>'
    pills_html += '</div>'
    st.markdown(pills_html, unsafe_allow_html=True)

    # AI-Suggested Questions
    if st.session_state.suggested_questions:
        st.markdown('<div class="section-label">AI-Suggested Questions</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:0.75rem;">', unsafe_allow_html=True)
        cols_q = st.columns(4)
        for i, q in enumerate(st.session_state.suggested_questions):
            with cols_q[i % 4]:
                if st.button(f"💡 {q[:55]}{'…' if len(q)>55 else ''}", key=f"sq_{i}", use_container_width=True):
                    st.session_state["prefill_query"] = q
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Analysis Templates
    st.markdown('<div class="section-label">Quick Templates</div>', unsafe_allow_html=True)
    t_cols = st.columns(5)
    for i, tmpl in enumerate(ANALYSIS_TEMPLATES):
        with t_cols[i % 5]:
            if st.button(f"{tmpl['icon']} {tmpl['title']}", key=f"tmpl_{i}", use_container_width=True):
                st.session_state["prefill_query"] = tmpl["prompt"]
                st.rerun()

    # Query Input
    st.markdown('<div class="section-label">AI Command Centre</div>', unsafe_allow_html=True)
    _prefill = st.session_state.pop("prefill_query", "") if "prefill_query" in st.session_state else ""

    user_prompt = st.text_area(
        "What would you like to analyze?",
        value=_prefill,
        placeholder="e.g. 'Draw an interactive bar chart of sales by region' or 'Find all rows where revenue > 50000'",
        key="query_text_area",
        height=95
    )

    col_run, col_bm = st.columns([5, 1])
    with col_run:
        st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
        run_btn = st.button("⚡ Execute AI Analysis", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_bm:
        if st.button("🔖 Bookmark", use_container_width=True, help="Save this query as a bookmark"):
            if user_prompt.strip():
                em = st.session_state.get("email", "")
                save_bookmark(em, user_prompt.strip())
                st.success("Bookmarked!", icon="🔖")

    # ── Execution Logic ───────────────────────────────────────
    if run_btn and user_prompt.strip():
        query_to_run = user_prompt.strip()
        if not is_admin and st.session_state.request_count >= MAX_REQUESTS:
            st.error(f"Rate limit reached ({MAX_REQUESTS} queries). Please upgrade your plan.")
        else:
            st.session_state.request_count += 1
            df_summary = get_df_summary(active_df)

            history_block = ""
            if st.session_state.chat_history:
                history_block = "CONVERSATION HISTORY:\n"
                for msg in st.session_state.chat_history[-8:]:
                    role = "User" if msg["role"] == "user" else "Nexus AI"
                    history_block += f"{role}: {msg['content'][:250]}\n"

            spinner_labels = {
                "chart": "◈ Building interactive chart...",
                "transform": "◈ Applying transformation...",
                "model": "◈ Running predictive model...",
                "summary": "◈ Generating summary...",
                "analysis": "◈ Running deep analysis...",
            }
            cat = classify_query(query_to_run)

            system_prompt = f"""You are Nexus AI — an elite data analyst and Python engineer.

── DATASET SCHEMA ──
{df_summary}
Total rows: {len(active_df):,} | Columns: {active_df.shape[1]}

── CONVERSATION HISTORY ──
{history_block if history_block else "No prior context."}

── CURRENT REQUEST ──
{query_to_run}

── RESPONSE FORMAT (strict) ──

## Analysis
2–4 sentences explaining what you found. Be specific — use real column names and numbers.

## Methodology
One sentence describing the technique (e.g. "groupby aggregation", "IQR outlier detection").

## Code
If computation is needed, ONE clean ```python``` block:
- Operate on `df` variable directly.
- For charts: USE PLOTLY ONLY. Example:
    import plotly.express as px
    fig = px.bar(df, x='col1', y='col2', title='My Chart', template='plotly_dark')
    # or: import plotly.graph_objects as go
  Do NOT call fig.show(). The system will render it automatically.
- For mutations: assign back (e.g. df = df[df['col'] > 0]).
- Import only: pandas, numpy, plotly, scipy. Never import os, sys, subprocess.
- If no code needed, omit the block entirely.

## Insight
1–3 bullet points of actionable insight grounded in the actual data.
"""
            with st.spinner(spinner_labels[cat]):
                try:
                    ai_response = call_ai(client, system_prompt)
                    st.session_state.chat_history.append({"role": "user", "content": query_to_run})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    trim_memory()

                    # Parse response
                    analysis_text = ""
                    insight_text = ""
                    methodology_text = ""
                    for key, pat in [
                        ("Analysis",    r"##\s*Analysis\s*(.*?)(?=##|\Z)"),
                        ("Methodology", r"##\s*Methodology\s*(.*?)(?=##|\Z)"),
                        ("Insight",     r"##\s*Insight\s*(.*?)(?=##|\Z)"),
                    ]:
                        m = re.search(pat, ai_response, re.DOTALL | re.IGNORECASE)
                        if m:
                            if key == "Analysis": analysis_text = m.group(1).strip()
                            if key == "Methodology": methodology_text = m.group(1).strip()
                            if key == "Insight": insight_text = m.group(1).strip()

                    code_raw = clean_ai_code(ai_response)
                    has_code = is_likely_python(code_raw)

                    # Display results
                    with st.container():
                        st.markdown('<div class="results-panel">', unsafe_allow_html=True)

                        if analysis_text:
                            st.markdown(f"**◈ Analysis**\n\n{analysis_text}")
                        if methodology_text:
                            st.caption(f"Methodology: {methodology_text}")

                        ok = True
                        rows_before = len(active_df)

                        if has_code:
                            st.markdown("**◈ Generated Code**")
                            st.code(code_raw, language="python")

                            exec_ns = {
                                "df": active_df.copy(),
                                "pd": pd, "np": np,
                                "px": px, "go": go,
                                "plt": plt,
                            }
                            if SEABORN_OK:
                                exec_ns["sns"] = sns
                            try:
                                exec(compile(code_raw, "<nexus>", "exec"), exec_ns)
                                out_df = exec_ns.get("df", active_df)

                                # Handle Plotly figures
                                plotly_fig = exec_ns.get("fig")
                                if plotly_fig is not None:
                                    try:
                                        plotly_fig.update_layout(
                                            template="plotly_dark",
                                            paper_bgcolor="rgba(0,0,0,0)",
                                            plot_bgcolor="rgba(0,0,0,0)",
                                            font_color="#e6edf3",
                                            margin=dict(l=20, r=20, t=50, b=30),
                                        )
                                        st.plotly_chart(plotly_fig, use_container_width=True)
                                        st.session_state.chart_gallery.append({
                                            "label": query_to_run[:60],
                                            "fig": plotly_fig,
                                            "ts": datetime.datetime.now().strftime("%H:%M"),
                                        })
                                    except Exception as pe:
                                        st.warning(f"Chart render issue: {pe}")

                                # Handle matplotlib figures
                                mpl_fig = plt.gcf()
                                if mpl_fig.get_axes() and not plotly_fig:
                                    buf = io.BytesIO()
                                    mpl_fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                                                    facecolor="#0d1117")
                                    buf.seek(0)
                                    st.image(buf, use_container_width=True)
                                    plt.close('all')

                                # DataFrame mutation
                                if not out_df.equals(active_df) and isinstance(out_df, pd.DataFrame):
                                    st.session_state.updated_df = out_df
                                    st.success(f"✅ DataFrame updated: {rows_before:,} → {len(out_df):,} rows")

                            except Exception as exec_err:
                                ok = False
                                st.error(f"❌ Execution error: {exec_err}")
                                st.code(traceback.format_exc(), language="text")

                        if insight_text:
                            st.markdown(f"""
                            <div class="insight-card">
                                <h4>◈ Key Insights</h4>
                                <p>{insight_text.replace(chr(10), '<br>')}</p>
                            </div>""", unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

                    # Save to history
                    em = st.session_state.get("email", "")
                    fn = st.session_state.last_filename or ""
                    save_analysis(em, query_to_run, analysis_text + "\n" + insight_text, fn)

                    st.session_state.command_history.append({
                        "cmd": query_to_run, "ok": ok,
                        "ts": datetime.datetime.now().strftime("%H:%M:%S"),
                        "rows_before": rows_before,
                        "rows_after": len(st.session_state.updated_df) if st.session_state.updated_df is not None else rows_before,
                    })

                except TimeoutError as te:
                    st.error(str(te))
                except Exception as e:
                    st.error(f"❌ AI Error: {e}")

    # Chart Gallery
    if st.session_state.chart_gallery:
        st.markdown('<div class="section-label">Chart Gallery</div>', unsafe_allow_html=True)
        for i, item in enumerate(reversed(st.session_state.chart_gallery)):
            with st.expander(f"📈 {item['label']} · {item['ts']}", expanded=(i == 0)):
                st.plotly_chart(item["fig"], use_container_width=True)

    # Export Controls
    st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        csv_buf = io.StringIO()
        active_df.to_csv(csv_buf, index=False)
        st.download_button("⬇️ Download CSV", csv_buf.getvalue(),
                           file_name=f"nexus_export_{datetime.date.today()}.csv",
                           mime="text/csv", use_container_width=True)

    with exp_col2:
        xl_buf = io.BytesIO()
        with pd.ExcelWriter(xl_buf, engine='openpyxl') as writer:
            active_df.to_excel(writer, index=False, sheet_name="Nexus Export")
        st.download_button("⬇️ Download Excel", xl_buf.getvalue(),
                           file_name=f"nexus_export_{datetime.date.today()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    with exp_col3:
        fn = st.session_state.last_filename or "data"
        html_report = generate_html_report(
            active_df, st.session_state.chat_history,
            st.session_state.chart_gallery, fn, st.session_state.auto_summary
        )
        st.download_button("📄 HTML Report", html_report,
                           file_name=f"nexus_report_{datetime.date.today()}.html",
                           mime="text/html", use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2: CLEAN DATA
# ═══════════════════════════════════════════════════════════════
with tab_clean:
    st.markdown('<div class="section-label">Data Quality Scan</div>', unsafe_allow_html=True)

    df_work = st.session_state.updated_df.copy() if st.session_state.updated_df is not None else active_df.copy()

    # Issue detection
    null_counts = df_work.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    dup_count = int(df_work.duplicated().sum())

    issues_found = len(null_cols) + (1 if dup_count > 0 else 0)
    if issues_found == 0:
        st.success("✅ No data quality issues found! Your dataset looks clean.")
    else:
        st.warning(f"⚠️ Found {issues_found} issue type(s) to address.")

    if not null_cols.empty:
        st.markdown('<div class="section-label">Missing Values</div>', unsafe_allow_html=True)
        null_df = pd.DataFrame({
            "Column": null_cols.index,
            "Missing Count": null_cols.values,
            "Missing %": (null_cols.values / len(df_work) * 100).round(1),
            "Data Type": [str(df_work[c].dtype) for c in null_cols.index],
        })
        st.dataframe(null_df, use_container_width=True, hide_index=True)

        fig_null = px.bar(null_df, x="Column", y="Missing Count",
                          title="Missing Values by Column",
                          template="plotly_dark",
                          color="Missing %",
                          color_continuous_scale="Reds")
        fig_null.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_null, use_container_width=True)

        st.markdown('<div class="section-label">Fix Missing Values</div>', unsafe_allow_html=True)
        col_fix1, col_fix2, col_fix3 = st.columns(3)
        with col_fix1:
            if st.button("📊 Fill numeric with median", use_container_width=True):
                for col in df_work.select_dtypes(include='number').columns:
                    df_work[col].fillna(df_work[col].median(), inplace=True)
                st.session_state.updated_df = df_work
                st.success("✅ Numeric nulls filled with column medians.")
                st.rerun()
        with col_fix2:
            if st.button("🔤 Fill text with 'Unknown'", use_container_width=True):
                for col in df_work.select_dtypes(include='object').columns:
                    df_work[col].fillna("Unknown", inplace=True)
                st.session_state.updated_df = df_work
                st.success("✅ Text nulls filled with 'Unknown'.")
                st.rerun()
        with col_fix3:
            if st.button("🗑️ Drop rows with any null", use_container_width=True):
                before = len(df_work)
                df_work.dropna(inplace=True)
                after = len(df_work)
                st.session_state.updated_df = df_work
                st.success(f"✅ Dropped {before - after:,} rows with nulls. Remaining: {after:,}")
                st.rerun()

    if dup_count > 0:
        st.markdown('<div class="section-label">Duplicate Rows</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="clean-issue">
            <div class="clean-issue-label">Duplicate rows detected</div>
            <div class="clean-issue-count">{dup_count} duplicate(s) · {dup_count/len(df_work)*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ Remove all duplicate rows", use_container_width=True):
            before = len(df_work)
            df_work.drop_duplicates(inplace=True)
            st.session_state.updated_df = df_work
            st.success(f"✅ Removed {before - len(df_work):,} duplicate rows.")
            st.rerun()

    # Anomaly section in Clean tab
    st.markdown('<div class="section-label">Anomaly & Outlier Detection (IQR)</div>', unsafe_allow_html=True)
    anomaly_df = detect_anomalies(df_work)
    if anomaly_df.empty:
        st.info("No statistical outliers detected using IQR method.")
    else:
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)

        if len(anomaly_df) > 0:
            worst_col = anomaly_df.sort_values("Outliers", ascending=False).iloc[0]["Column"]
            Q1 = df_work[worst_col].quantile(0.25)
            Q3 = df_work[worst_col].quantile(0.75)
            IQR = Q3 - Q1
            lo, hi = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR

            fig_box = px.box(df_work, y=worst_col,
                             title=f"Outlier Distribution: {worst_col}",
                             template="plotly_dark")
            fig_box.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_box, use_container_width=True)

            if st.button(f"✂️ Remove outliers from '{worst_col}'", use_container_width=True):
                before = len(df_work)
                df_work = df_work[(df_work[worst_col] >= lo) & (df_work[worst_col] <= hi)]
                st.session_state.updated_df = df_work
                st.success(f"✅ Removed {before - len(df_work):,} outlier rows from '{worst_col}'.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# TAB 3: EXPLORE
# ═══════════════════════════════════════════════════════════════
with tab_explore:
    explore_df = st.session_state.updated_df if st.session_state.updated_df is not None else active_df

    sub_col, sub_corr, sub_dist = st.tabs(["🔬 Column Deep-Dive", "🔗 Correlation Matrix", "📊 Distributions"])

    with sub_col:
        st.markdown('<div class="section-label">Column Deep-Dive</div>', unsafe_allow_html=True)
        col_select = st.selectbox("Select a column to inspect:", explore_df.columns.tolist())

        if col_select:
            s = explore_df[col_select]
            null_n = int(s.isnull().sum())
            unique_n = int(s.nunique())

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Values", f"{len(s):,}")
            m2.metric("Unique Values", f"{unique_n:,}")
            m3.metric("Missing", f"{null_n:,} ({null_n/len(s)*100:.1f}%)")
            m4.metric("Data Type", str(s.dtype))

            if pd.api.types.is_numeric_dtype(s):
                desc = s.describe()
                d1, d2, d3, d4, d5 = st.columns(5)
                d1.metric("Mean", f"{desc['mean']:.2f}")
                d2.metric("Median", f"{s.median():.2f}")
                d3.metric("Std Dev", f"{desc['std']:.2f}")
                d4.metric("Min", f"{desc['min']:.2f}")
                d5.metric("Max", f"{desc['max']:.2f}")

                fig_hist = px.histogram(explore_df, x=col_select,
                                        title=f"Distribution: {col_select}",
                                        template="plotly_dark",
                                        marginal="box",
                                        nbins=40,
                                        color_discrete_sequence=["#00d4aa"])
                fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_hist, use_container_width=True)

            else:
                top_vals = s.value_counts().head(20)
                fig_bar = px.bar(x=top_vals.index.astype(str), y=top_vals.values,
                                 title=f"Top Values: {col_select}",
                                 labels={"x": col_select, "y": "Count"},
                                 template="plotly_dark",
                                 color=top_vals.values,
                                 color_continuous_scale="Teal")
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)

                st.markdown('<div class="section-label">Frequency Table</div>', unsafe_allow_html=True)
                freq_df = pd.DataFrame({
                    "Value": top_vals.index.astype(str),
                    "Count": top_vals.values,
                    "% of Total": (top_vals.values / len(s) * 100).round(1)
                })
                st.dataframe(freq_df, use_container_width=True, hide_index=True)

    with sub_corr:
        st.markdown('<div class="section-label">Correlation Matrix</div>', unsafe_allow_html=True)
        num_cols = explore_df.select_dtypes(include='number').columns.tolist()
        if len(num_cols) < 2:
            st.info("Need at least 2 numeric columns for a correlation matrix.")
        else:
            corr = explore_df[num_cols].corr()
            fig_corr = px.imshow(
                corr, text_auto=".2f", aspect="auto",
                title="Pearson Correlation Matrix",
                template="plotly_dark",
                color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1,
            )
            fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   height=500)
            st.plotly_chart(fig_corr, use_container_width=True)

            # Strongest correlations
            st.markdown('<div class="section-label">Strongest Correlations</div>', unsafe_allow_html=True)
            pairs = []
            for i in range(len(num_cols)):
                for j in range(i+1, len(num_cols)):
                    pairs.append({
                        "Column A": num_cols[i],
                        "Column B": num_cols[j],
                        "Correlation": round(corr.iloc[i, j], 4),
                        "Strength": "Strong" if abs(corr.iloc[i, j]) > 0.7 else "Moderate" if abs(corr.iloc[i, j]) > 0.4 else "Weak",
                    })
            pairs_df = pd.DataFrame(pairs).sort_values("Correlation", key=abs, ascending=False)
            st.dataframe(pairs_df, use_container_width=True, hide_index=True)

    with sub_dist:
        st.markdown('<div class="section-label">Numeric Column Distributions</div>', unsafe_allow_html=True)
        num_cols_list = explore_df.select_dtypes(include='number').columns.tolist()
        if not num_cols_list:
            st.info("No numeric columns to plot.")
        else:
            dist_col = st.selectbox("Select column:", num_cols_list, key="dist_col_sel")
            cat_cols = explore_df.select_dtypes(include='object').columns.tolist()
            color_by = st.selectbox("Color by (optional):", ["— None —"] + cat_cols, key="color_dist")

            color_arg = None if color_by == "— None —" else color_by
            fig_d = px.histogram(explore_df, x=dist_col, color=color_arg,
                                 title=f"Distribution of {dist_col}" + (f" by {color_by}" if color_arg else ""),
                                 template="plotly_dark", nbins=50, marginal="violin",
                                 barmode="overlay", opacity=0.75)
            fig_d.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_d, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 4: HISTORY
# ═══════════════════════════════════════════════════════════════
with tab_history:
    st.markdown('<div class="section-label">Your Analysis History</div>', unsafe_allow_html=True)
    em = st.session_state.get("email", "")

    if not em or is_admin:
        st.info("Analysis history is linked to your user account. Log in as a regular user to view history.")
    else:
        analyses = get_user_analyses(em, limit=30)
        if not analyses:
            st.info("No saved analyses yet. Run some queries and they'll appear here.")
        else:
            for item in analyses:
                ts = str(item.get("created_at", ""))[:16]
                q = item.get("query", "")
                result = item.get("result", "")
                fn = item.get("filename", "")
                with st.expander(f"🕐 {ts}  ·  {q[:70]}{'…' if len(q)>70 else ''}", expanded=False):
                    if fn:
                        st.caption(f"File: {fn}")
                    st.markdown(f"**Query:** {q}")
                    if result:
                        st.markdown("**AI Result:**")
                        st.markdown(result[:1500])
                    if st.button("▶️ Re-run this query", key=f"rerun_{item.get('id',ts)}"):
                        st.session_state["prefill_query"] = q
                        st.rerun()


# ═══════════════════════════════════════════════════════════════
# TAB 5: BOOKMARKS
# ═══════════════════════════════════════════════════════════════
with tab_bookmarks:
    st.markdown('<div class="section-label">Saved Query Bookmarks</div>', unsafe_allow_html=True)
    em = st.session_state.get("email", "")

    if not em or is_admin:
        st.info("Bookmarks are linked to your user account.")
    else:
        bookmarks = get_bookmarks(em)
        if not bookmarks:
            st.info("No bookmarks yet. Click 🔖 Bookmark when entering a query to save it here.")
        else:
            for bm in bookmarks:
                bm_id = bm.get("id")
                bm_q = bm.get("query", "")
                bm_ts = str(bm.get("created_at", ""))[:10]
                col_bm1, col_bm2, col_bm3 = st.columns([5, 1, 1])
                with col_bm1:
                    st.markdown(f"""
                    <div class="history-item">
                        <div class="history-query">{bm_q}</div>
                        <div class="history-meta">Saved {bm_ts}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_bm2:
                    if st.button("▶️ Use", key=f"use_bm_{bm_id}", use_container_width=True):
                        st.session_state["prefill_query"] = bm_q
                        st.rerun()
                with col_bm3:
                    if st.button("🗑️", key=f"del_bm_{bm_id}", use_container_width=True):
                        delete_bookmark(bm_id)
                        st.rerun()
