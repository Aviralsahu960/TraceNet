import streamlit as st
import pandas as pd
import requests
import time
import json
from streamlit_agraph import agraph, Node, Edge, Config
from collections import defaultdict

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="TraceNet | AML Intelligence",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000"

# ============================================================
# GOD-TIER CSS
# ============================================================
st.markdown("""
<style>
    /* === GLOBAL === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    .main { background: #06080d; font-family: 'Inter', sans-serif; }
    .block-container { padding: 1rem 2rem; }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* === GLASS CARDS === */
    .glass-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin: 8px 0;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.1);
        transform: translateY(-2px);
    }

    /* === HERO HEADER === */
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 32px 40px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 42px; font-weight: 800;
        background: linear-gradient(135deg, #e0e7ff, #a5b4fc, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; line-height: 1.2;
    }
    .hero-subtitle {
        color: #94a3b8; font-size: 16px; margin: 8px 0 0 0;
        font-weight: 400; letter-spacing: 0.5px;
    }
    .hero-badge {
        display: inline-block; padding: 4px 12px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px; font-size: 12px;
        color: #a5b4fc; margin-right: 8px; margin-top: 12px;
    }

    /* === METRIC CARDS === */
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 27, 75, 0.4));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
    }
    .metric-value {
        font-size: 32px; font-weight: 800;
        background: linear-gradient(135deg, #e0e7ff, #a5b4fc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 4px 0;
    }
    .metric-label {
        color: #64748b; font-size: 12px; font-weight: 600;
        text-transform: uppercase; letter-spacing: 1.5px;
    }

    /* === COLORED METRIC VARIANTS === */
    .metric-red .metric-value {
        background: linear-gradient(135deg, #fca5a5, #ef4444);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-red { border-color: rgba(239, 68, 68, 0.2); }
    .metric-red:hover { border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15); }

    .metric-green .metric-value {
        background: linear-gradient(135deg, #86efac, #22c55e);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-green { border-color: rgba(34, 197, 94, 0.2); }

    .metric-amber .metric-value {
        background: linear-gradient(135deg, #fde68a, #f59e0b);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-amber { border-color: rgba(245, 158, 11, 0.2); }

    .metric-cyan .metric-value {
        background: linear-gradient(135deg, #a5f3fc, #06b6d4);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* === BLOCK / ALLOW BANNERS === */
    .block-banner {
        background: linear-gradient(135deg, #7f1d1d, #991b1b, #7f1d1d);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 16px; padding: 28px;
        text-align: center; position: relative; overflow: hidden;
    }
    .block-banner::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at 50% 50%, rgba(239, 68, 68, 0.2) 0%, transparent 70%);
        animation: pulse-glow 2s ease-in-out infinite;
    }
    @keyframes pulse-glow {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    .block-title { color: #fca5a5; font-size: 36px; font-weight: 900; margin: 0; position: relative; z-index: 1; }
    .block-subtitle { color: #fecaca; font-size: 14px; margin: 8px 0 0; position: relative; z-index: 1; }

    .allow-banner {
        background: linear-gradient(135deg, #14532d, #166534, #14532d);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 16px; padding: 28px; text-align: center;
    }
    .allow-title { color: #86efac; font-size: 36px; font-weight: 900; margin: 0; }

    /* === LAYER CARDS === */
    .layer-active {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.3), rgba(153, 27, 27, 0.15));
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px; padding: 16px; margin: 6px 0;
        transition: all 0.3s ease;
    }
    .layer-active:hover { border-color: rgba(239, 68, 68, 0.5); }
    .layer-safe {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(34, 197, 94, 0.15);
        border-radius: 12px; padding: 16px; margin: 6px 0;
    }
    .layer-name { color: #e2e8f0; font-weight: 600; font-size: 14px; }
    .layer-score-red { color: #ef4444; font-weight: 800; font-size: 18px; }
    .layer-score-green { color: #22c55e; font-weight: 800; font-size: 18px; }

    /* === SAR BOX === */
    .sar-box {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(30, 27, 75, 0.3));
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 4px solid #ef4444;
        border-radius: 12px; padding: 24px; margin: 12px 0;
    }
    .sar-meta { color: #64748b; font-size: 12px; font-family: 'JetBrains Mono', monospace; }
    .sar-text { color: #e2e8f0; font-size: 15px; line-height: 1.8; margin-top: 12px; }

    /* === COMMUNITY CARD === */
    .community-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 14px; padding: 20px; margin: 8px 0;
    }
    .community-critical { border-left: 4px solid #ef4444; }
    .community-high { border-left: 4px solid #f59e0b; }
    .community-moderate { border-left: 4px solid #22c55e; }

    /* === INTEL BOX === */
    .intel-box {
        background: rgba(6, 8, 13, 0.9);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px; padding: 20px;
        font-family: 'JetBrains Mono', monospace; font-size: 13px;
        color: #a5b4fc;
    }

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.1);
    }
    [data-testid="stSidebar"] .block-container { padding-top: 2rem; }

    /* === TABLE STYLING === */
    .stDataFrame { border-radius: 12px; overflow: hidden; }

    /* === DAMAGE BANNER === */
    .damage-banner {
        border-radius: 16px; padding: 28px;
        text-align: center; position: relative;
    }
    .damage-catastrophic {
        background: linear-gradient(135deg, #7f1d1d, #991b1b);
        border: 1px solid rgba(239, 68, 68, 0.5);
    }
    .damage-severe {
        background: linear-gradient(135deg, #78350f, #92400e);
        border: 1px solid rgba(245, 158, 11, 0.5);
    }
    .damage-moderate {
        background: linear-gradient(135deg, #1e3a5f, #1e40af);
        border: 1px solid rgba(59, 130, 246, 0.5);
    }

    /* === ATTACK FEED === */
    .attack-stat {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px; padding: 16px; text-align: center;
    }
    .saved-banner {
        background: linear-gradient(135deg, #14532d, #166534);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 16px; padding: 24px; text-align: center; margin-top: 20px;
    }

    /* === SECTION HEADERS === */
    .section-header {
        color: #e2e8f0; font-size: 20px; font-weight: 700;
        margin: 24px 0 12px 0; padding-bottom: 8px;
        border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    }

    /* === CHANNEL/JURISDICTION CHIPS === */
    .chip {
        display: inline-block; padding: 6px 14px;
        border-radius: 20px; font-size: 13px;
        font-weight: 600; margin: 3px;
    }
    .chip-channel {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #a5b4fc;
    }
    .chip-risk-high {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #fca5a5;
    }
    .chip-risk-med {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #fde68a;
    }
    .chip-risk-low {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        color: #86efac;
    }

    /* === STREAMLIT OVERRIDES === */
    .stSelectbox > div > div { background: rgba(15, 23, 42, 0.8); border-color: rgba(99, 102, 241, 0.2); }
    .stTextInput > div > div > input { background: rgba(15, 23, 42, 0.8); border-color: rgba(99, 102, 241, 0.2); color: #e2e8f0; }
    .stNumberInput > div > div > input { background: rgba(15, 23, 42, 0.8); border-color: rgba(99, 102, 241, 0.2); color: #e2e8f0; }
    .stButton > button {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white; border: none; border-radius: 12px;
        padding: 12px 24px; font-weight: 700; font-size: 15px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    div[data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(99, 102, 241, 0.1);
        border-radius: 12px;
    }
    .stProgress > div > div > div { background: linear-gradient(90deg, #4f46e5, #7c3aed, #a855f7); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0;'>
        <div style='font-size: 48px; margin-bottom: 8px;'>🛡️</div>
        <div style='font-size: 24px; font-weight: 800;
            background: linear-gradient(135deg, #e0e7ff, #a5b4fc);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>TraceNet</div>
        <div style='color: #64748b; font-size: 11px; letter-spacing: 2px;
            text-transform: uppercase; margin-top: 4px;'>AML INTELLIGENCE PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio("", [
        "🏠 Command Center",
        "🔍 Transaction Scanner",
        "⚔️ Attack Simulator",
        "💀 Damage Report",
        "🕸️ Graph Forensics",
        "🔮 Ring Discovery",
        "👤 Entity Profiler",
        "📊 Analytics",
        "🔒 Intel Sharing",
        "📜 SAR Reports"
    ], label_visibility="collapsed")

    st.markdown("---")

    try:
        stats = requests.get(f"{API_URL}/stats", timeout=3).json()
        config = stats.get("model_config", {})
        st.markdown(f"""
        <div class="glass-card" style="padding:16px;">
            <div style="color:#a5b4fc; font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px;">SYSTEM STATUS</div>
            <div style="color:#22c55e; font-size:13px;">● GNN Engine Online</div>
            <div style="color:#22c55e; font-size:13px;">● LLM Engine Online</div>
            <div style="color:#22c55e; font-size:13px;">● 11 Detection Layers</div>
            <div style="margin-top:12px; color:#64748b; font-size:12px;">
                Nodes: <span style="color:#e2e8f0;">{stats['total_nodes']:,}</span><br>
                Edges: <span style="color:#e2e8f0;">{stats['total_edges']:,}</span><br>
                Blocked: <span style="color:#ef4444;">{stats['blocked_count']}</span><br>
                Approved: <span style="color:#22c55e;">{stats['approved_count']}</span><br>
                Flagged: <span style="color:#f59e0b;">{stats['flagged_users']}</span><br>
                Sanctioned: <span style="color:#ef4444;">{stats['sanctioned_entities']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        st.markdown("""<div class="glass-card" style="padding:16px;">
            <div style="color:#ef4444; font-size:13px;">● API OFFLINE</div></div>""", unsafe_allow_html=True)

# ============================================================
# COMMAND CENTER
# ============================================================
if page == "🏠 Command Center":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">TraceNet Command Center</div>
        <div class="hero-subtitle">Cross-Channel Mule Ring Detection • Real-Time GNN Monitoring • 11-Layer AI Engine</div>
        <div>
            <span class="hero-badge">GraphSAGE GNN</span>
            <span class="hero-badge">Qwen 2.5 LLM</span>
            <span class="hero-badge">CUDA Accelerated</span>
            <span class="hero-badge">6 Channels</span>
            <span class="hero-badge">10 Jurisdictions</span>
            <span class="hero-badge">ISO 20022</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        stats = requests.get(f"{API_URL}/stats", timeout=3).json()
        config = stats.get("model_config", {})

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        metrics = [
            (c1, "NODES", f"{stats['total_nodes']:,}", ""),
            (c2, "EDGES", f"{stats['total_edges']:,}", ""),
            (c3, "BLOCKED", str(stats['blocked_count']), "metric-red"),
            (c4, "APPROVED", str(stats['approved_count']), "metric-green"),
            (c5, "FLAGGED", str(stats['flagged_users']), "metric-amber"),
            (c6, "SANCTIONED", str(stats['sanctioned_entities']), "metric-red"),
        ]
        for col, label, value, cls in metrics:
            with col:
                st.markdown(f"""<div class="metric-card {cls}">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("")
        col1, col2 = st.columns([2, 1])

        with col1:
            if config:
                st.markdown('<div class="section-header">🧠 AI Model Performance</div>', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                perf = [
                    (m1, "ACCURACY", f"{config.get('accuracy', 0)}%", "metric-green"),
                    (m2, "PRECISION", f"{config.get('precision', 0)}%", "metric-green"),
                    (m3, "RECALL", f"{config.get('recall', 0)}%", "metric-cyan"),
                    (m4, "F1 SCORE", f"{config.get('f1', 0)}%", "metric-cyan"),
                ]
                for col, label, value, cls in perf:
                    with col:
                        st.markdown(f"""<div class="metric-card {cls}">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-header">📡 Detection Engine</div>', unsafe_allow_html=True)
            layers = [
                ("🧠", "GNN (GraphSAGE)", "3-layer message passing, 15 topological features"),
                ("📐", "Shape Analysis", "Graph topology comparison against known mule patterns"),
                ("🎭", "Behavioral Engine", "Pass-through, fan-in/out, circular flow, structuring"),
                ("🔗", "Chain Tracer", "Multi-hop forward/backward chain tracing (10 hops)"),
                ("⚡", "Velocity Detector", "Sub-minute transaction burst detection"),
                ("📡", "Cross-Channel", "Mobile→ATM, Web→UPI pattern detection"),
                ("🌍", "Jurisdiction Risk", "10-country risk scoring, cross-border corridors"),
                ("🚫", "Sanctions Screen", "2-hop behavior-based, not just list matching"),
                ("💥", "Fragmentation", "Micro-transaction splitting detection"),
                ("👥", "Ownership Links", "Linked account resolution across entities"),
                ("🏦", "Nesting Detector", "Shell company layering depth analysis"),
            ]
            for emoji, name, desc in layers:
                st.markdown(f"""<div class="glass-card" style="padding:12px 16px; margin:4px 0;">
                    <span style="font-size:16px;">{emoji}</span>
                    <span class="layer-name" style="margin-left:8px;">{name}</span>
                    <span style="color:#64748b; font-size:12px; margin-left:8px;">{desc}</span>
                </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="section-header">��� Channels</div>', unsafe_allow_html=True)
            channels_info = [("📱", "Mobile App"), ("🌐", "Web Banking"), ("🏧", "ATM Network"),
                            ("💳", "UPI Instant"), ("🏦", "Wire Transfer"), ("🏢", "Branch")]
            for emoji, name in channels_info:
                st.markdown(f'<span class="chip chip-channel">{emoji} {name}</span>', unsafe_allow_html=True)

            st.markdown('<div class="section-header" style="margin-top:24px;">🗺️ Jurisdictions</div>', unsafe_allow_html=True)
            jur_data = [
                ("US", "low"), ("UK", "low"), ("IN", "low"), ("SG", "low"),
                ("AE", "med"), ("NGA", "med"),
                ("KY", "high"), ("PA", "high"), ("VG", "high"), ("RU", "high"),
            ]
            for code, risk in jur_data:
                cls = f"chip-risk-{risk}"
                st.markdown(f'<span class="chip {cls}">{code}</span>', unsafe_allow_html=True)

        # Live Feed
        st.markdown('<div class="section-header">📡 Live Transaction Feed</div>', unsafe_allow_html=True)
        try:
            feed = requests.get(f"{API_URL}/feed", timeout=3).json()
            if feed:
                feed_df = pd.DataFrame(feed)
                cols = ['txn_id', 'action', 'risk_score', 'confidence', 'channel', 'sender_country', 'receiver_country']
                available = [c for c in cols if c in feed_df.columns]
                if available:
                    st.dataframe(feed_df[available], use_container_width=True, height=300)
            else:
                st.info("No transactions yet. Use the Scanner or Attack Simulator.")
        except:
            st.info("Submit transactions to see the live feed.")

    except Exception as e:
        st.error(f"Cannot connect to API: {e}")

# ============================================================
# TRANSACTION SCANNER
# ============================================================
elif page == "🔍 Transaction Scanner":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Transaction Scanner</div>
        <div class="hero-subtitle">Submit any transaction for real-time 11-layer AI forensic analysis</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">⚡ Quick Test Scenarios</div>', unsafe_allow_html=True)
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button("🚨 Known Criminal", use_container_width=True):
            st.session_state.update({'q_sender': 'U00001', 'q_receiver': 'U00099', 'q_amount': 9500.0,
                'q_channel': 'mobile_app', 'q_scountry': 'US', 'q_rcountry': 'KY'})
    with qc2:
        if st.button("🆕 New Scammer", use_container_width=True):
            st.session_state.update({'q_sender': 'BRAND_NEW_99', 'q_receiver': 'OFFSHORE_01', 'q_amount': 9500.0,
                'q_channel': 'atm', 'q_scountry': 'KY', 'q_rcountry': 'VG'})
    with qc3:
        if st.button("☕ Coffee Purchase", use_container_width=True):
            st.session_state.update({'q_sender': 'NORMAL_USER', 'q_receiver': 'STARBUCKS', 'q_amount': 5.50,
                'q_channel': 'upi', 'q_scountry': 'US', 'q_rcountry': 'US'})
    with qc4:
        if st.button("🏦 Shell Transfer", use_container_width=True):
            st.session_state.update({'q_sender': 'U00998', 'q_receiver': 'U00997', 'q_amount': 45000.0,
                'q_channel': 'wire', 'q_scountry': 'KY', 'q_rcountry': 'PA'})

    st.markdown("---")

    with st.form("txn_form"):
        col1, col2 = st.columns(2)
        with col1:
            sender = st.text_input("Sender ID", st.session_state.get('q_sender', 'U00001'))
            receiver = st.text_input("Receiver ID", st.session_state.get('q_receiver', 'U00099'))
            amount = st.number_input("Amount ($)", min_value=0.01, value=st.session_state.get('q_amount', 9500.0), step=100.0)
        with col2:
            channel_options = ["mobile_app", "web", "atm", "upi", "wire", "branch"]
            default_ch = st.session_state.get('q_channel', 'mobile_app')
            channel = st.selectbox("Channel", channel_options, index=channel_options.index(default_ch) if default_ch in channel_options else 0)
            country_options = ["US", "UK", "IN", "SG", "AE", "KY", "PA", "VG", "NGA", "RU"]
            default_sc = st.session_state.get('q_scountry', 'US')
            default_rc = st.session_state.get('q_rcountry', 'KY')
            sender_country = st.selectbox("Sender Country", country_options, index=country_options.index(default_sc) if default_sc in country_options else 0)
            receiver_country = st.selectbox("Receiver Country", country_options, index=country_options.index(default_rc) if default_rc in country_options else 4)
        submitted = st.form_submit_button("🚀 Run 11-Layer AI Scan", use_container_width=True)

    if submitted:
        with st.spinner("Running GNN + Behavioral + Velocity + Cross-Channel + Jurisdiction + Sanctions..."):
            payload = {
                "txn_id": f"SCAN-{int(time.time())}",
                "sender_id": sender, "receiver_id": receiver, "amount": amount,
                "channel": channel, "sender_country": sender_country, "receiver_country": receiver_country
            }
            try:
                res = requests.post(f"{API_URL}/score_transaction", json=payload, timeout=60).json()

                if res['action'] == "BLOCK":
                    st.markdown(f"""<div class="block-banner">
                        <div class="block-title">🚨 TRANSACTION BLOCKED</div>
                        <div class="block-subtitle">{res.get('block_reason', 'Multiple detection layers triggered')}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="allow-banner">
                        <div class="allow-title">✅ TRANSACTION APPROVED</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")
                c1, c2, c3, c4, c5 = st.columns(5)
                scan_metrics = [
                    (c1, "RISK SCORE", f"{res['risk_score']}%", "metric-red" if res['risk_score'] > 50 else "metric-green"),
                    (c2, "CONFIDENCE", f"{res.get('confidence', 0)*100:.0f}%", ""),
                    (c3, "SENDER RISK", f"{res['sender_risk']}%", "metric-amber"),
                    (c4, "RECEIVER RISK", f"{res['receiver_risk']}%", "metric-amber"),
                    (c5, "TRUST TIER", f"T{res.get('trust_tier', '?')}", ""),
                ]
                for col, label, value, cls in scan_metrics:
                    with col:
                        st.markdown(f"""<div class="metric-card {cls}">
                            <div class="metric-label">{label}</div>
                            <div class="metric-value">{value}</div>
                        </div>""", unsafe_allow_html=True)

                # Risk Breakdown
                breakdown = res.get('risk_breakdown', {})
                if breakdown:
                    st.markdown('<div class="section-header">📊 Risk Breakdown by Layer</div>', unsafe_allow_html=True)
                    active = {k: v for k, v in breakdown.items() if v > 0}
                    if active:
                        bd_df = pd.DataFrame({'Layer': [k.replace('_', ' ').title() for k in active.keys()], 'Score': list(active.values())}).sort_values('Score', ascending=True)
                        st.bar_chart(bd_df.set_index('Layer'))

                    st.markdown('<div class="section-header">⚡ Layer Status</div>', unsafe_allow_html=True)
                    layer_names = {
                        "gnn_score": "🧠 GNN Memory", "behavioral": "🎭 Behavioral",
                        "velocity": "⚡ Velocity", "cross_channel": "📡 Cross-Channel",
                        "jurisdiction": "🌍 Jurisdiction", "sanctions": "🚫 Sanctions",
                        "fragmentation": "💥 Fragmentation", "ownership_link": "👥 Ownership",
                        "nesting": "🏦 Nesting", "chain_detection": "🔗 Chain",
                        "routing_complexity": "🛤️ Routing", "nesting_txn": "🏦 Nesting (Txn)",
                        "trust_violation": "🔒 Trust Gate", "shape_similarity": "📐 Shape",
                    }
                    cols = st.columns(4)
                    all_keys = list(layer_names.keys())
                    for i, key in enumerate(all_keys):
                        score = breakdown.get(key, 0)
                        label = layer_names[key]
                        with cols[i % 4]:
                            if score > 0:
                                st.markdown(f"""<div class="layer-active">
                                    <div class="layer-name">{label}</div>
                                    <div class="layer-score-red">+{score}%</div>
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.markdown(f"""<div class="layer-safe">
                                    <div class="layer-name">{label}</div>
                                    <div class="layer-score-green">0%</div>
                                </div>""", unsafe_allow_html=True)

                if res.get('sar_report'):
                    st.markdown('<div class="section-header">📜 AI-Generated SAR Report</div>', unsafe_allow_html=True)
                    st.markdown(f"""<div class="sar-box">
                        <div class="sar-meta">Generated by Qwen-2.5 3B (Local LLM) • Confidence: {res.get('confidence', 0)*100:.0f}% • {len(res.get('detection_layers_triggered', []))} layers triggered</div>
                        <div class="sar-text">{res['sar_report']}</div>
                    </div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"API Error: {e}")

# ============================================================
# ATTACK SIMULATOR
# ============================================================
elif page == "⚔️ Attack Simulator":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Live Attack Simulator</div>
        <div class="hero-subtitle">Watch real money laundering attacks unfold and see TraceNet intercept them in real-time</div>
    </div>
    """, unsafe_allow_html=True)

    attack_type = st.selectbox("Select Attack Scenario:", [
        "scatter_gather", "shell_nesting", "fragmentation", "velocity", "circular"
    ], format_func=lambda x: {
        "scatter_gather": "🎯 Scatter-Gather Ring (Boss → 50 Mules → ATM)",
        "shell_nesting": "🏦 Shell Company Nesting (4 Shells bouncing $$$)",
        "fragmentation": "💥 UPI Fragmentation (Split $10K into micro-payments)",
        "velocity": "⚡ Cross-Border Velocity (5 countries in 10 minutes)",
        "circular": "🔄 Circular Laundering (Perfect money circle)"
    }[x])

    if st.button("🚀 LAUNCH ATTACK", use_container_width=True):
        try:
            scenario = requests.get(f"{API_URL}/simulate_attack/{attack_type}", timeout=10).json()
            if "error" in scenario:
                st.error(scenario["error"])
            else:
                st.markdown(f"""<div class="glass-card">
                    <div style="color:#e2e8f0; font-size:20px; font-weight:700;">{scenario['name']}</div>
                    <div style="color:#94a3b8; margin:8px 0;">{scenario['description']}</div>
                    <div style="color:#ef4444; font-weight:700; font-size:18px;">💰 Amount at risk: ${scenario['total_laundered']:,}</div>
                </div>""", unsafe_allow_html=True)

                stats_area = st.empty()
                progress = st.progress(0)
                feed_area = st.empty()

                blocked_count = 0
                allowed_count = 0
                total_steps = len(scenario['steps'])
                results = []

                for i, step in enumerate(scenario['steps']):
                    payload = {
                        "txn_id": f"ATK-{attack_type[:3].upper()}-{i:04d}",
                        "sender_id": step['sender'], "receiver_id": step['receiver'],
                        "amount": step['amount'], "channel": step['channel'],
                        "sender_country": step['s_country'], "receiver_country": step['r_country']
                    }
                    try:
                        res = requests.post(f"{API_URL}/score_transaction", json=payload, timeout=30).json()
                        if res['action'] == "BLOCK":
                            blocked_count += 1
                        else:
                            allowed_count += 1
                        results.append({
                            "Step": i+1, "Status": res['action'],
                            "Risk": f"{res['risk_score']}%",
                            "Sender": step['sender'], "Receiver": step['receiver'],
                            "Amount": f"${step['amount']:,}", "Channel": step['channel'],
                            "Route": f"{step['s_country']}→{step['r_country']}"
                        })
                    except:
                        results.append({"Step": i+1, "Status": "ERROR", "Risk": "N/A",
                            "Sender": step['sender'], "Receiver": step['receiver'],
                            "Amount": f"${step['amount']:,}", "Channel": step['channel'],
                            "Route": f"{step['s_country']}→{step['r_country']}"})

                    progress.progress((i + 1) / total_steps)

                    block_rate = blocked_count / max(i + 1, 1) * 100
                    stats_area.markdown(f"""
                    <div style="display:flex; gap:12px;">
                        <div class="attack-stat" style="flex:1;"><div class="metric-label">PROCESSED</div><div class="metric-value">{i+1}/{total_steps}</div></div>
                        <div class="attack-stat" style="flex:1;"><div class="metric-label">BLOCKED</div><div style="color:#ef4444; font-size:28px; font-weight:800;">{blocked_count}</div></div>
                        <div class="attack-stat" style="flex:1;"><div class="metric-label">ALLOWED</div><div style="color:#22c55e; font-size:28px; font-weight:800;">{allowed_count}</div></div>
                        <div class="attack-stat" style="flex:1;"><div class="metric-label">BLOCK RATE</div><div style="color:#a5b4fc; font-size:28px; font-weight:800;">{block_rate:.1f}%</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    time.sleep(0.05)

                results_df = pd.DataFrame(results)
                def style_status(val):
                    if val == "BLOCK": return 'background-color: #7f1d1d; color: #fca5a5; font-weight: bold'
                    elif val == "ALLOW": return 'background-color: #14532d; color: #86efac'
                    return 'background-color: #78350f; color: #fde68a'
                styled = results_df.style.applymap(style_status, subset=['Status'])
                feed_area.dataframe(styled, use_container_width=True, height=400)

                money_blocked = blocked_count * scenario['steps'][0]['amount'] if scenario['steps'] else 0
                st.markdown(f"""<div class="saved-banner">
                    <div style="color:#86efac; font-size:32px; font-weight:900;">💰 TraceNet saved ${money_blocked:,.2f}</div>
                    <div style="color:#bbf7d0; font-size:14px;">Blocked {blocked_count}/{total_steps} fraudulent transactions</div>
                </div>""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================
# DAMAGE REPORT
# ============================================================
elif page == "💀 Damage Report":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">What-If Damage Estimator</div>
        <div class="hero-subtitle">See the catastrophic impact if a criminal's transactions were not blocked</div>
    </div>
    """, unsafe_allow_html=True)

    entity_id = st.text_input("Enter Entity ID:", "U00001")
    if st.button("💀 Calculate Damage", use_container_width=True):
        with st.spinner("Tracing downstream money flows..."):
            try:
                damage = requests.get(f"{API_URL}/damage_estimate/{entity_id}", timeout=10).json()
                if "error" in damage:
                    st.error(damage["error"])
                else:
                    assessment = damage['damage_assessment']
                    cls = f"damage-{assessment.lower()}" if assessment.lower() in ['catastrophic', 'severe', 'moderate'] else "damage-moderate"
                    st.markdown(f"""<div class="damage-banner {cls}">
                        <div style="color:white; font-size:36px; font-weight:900;">⚠️ {assessment}</div>
                        <div style="color:rgba(255,255,255,0.8); font-size:15px; margin-top:8px;">{damage['what_if_statement']}</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("")
                    c1, c2, c3, c4 = st.columns(4)
                    dmg_metrics = [
                        (c1, "TOTAL SENT", f"${damage['total_money_sent']:,.0f}", "metric-red"),
                        (c2, "NETWORK EXPOSURE", f"${damage['total_network_exposure']:,.0f}", "metric-red"),
                        (c3, "DOWNSTREAM", str(damage['downstream_entities_affected']), "metric-amber"),
                        (c4, "MULES REACHED", str(damage['downstream_mules_connected']), "metric-red"),
                    ]
                    for col, label, value, cls in dmg_metrics:
                        with col:
                            st.markdown(f"""<div class="metric-card {cls}">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value">{value}</div>
                            </div>""", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<div class="section-header">🌍 Jurisdictions at Risk</div>', unsafe_allow_html=True)
                        for c in damage.get('jurisdictions_at_risk', []):
                            risk_cls = "chip-risk-high" if c in ['KY','PA','VG','RU'] else "chip-risk-med" if c in ['AE','NGA'] else "chip-risk-low"
                            st.markdown(f'<span class="chip {risk_cls}">{c}</span>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="section-header">📡 Channels Exploited</div>', unsafe_allow_html=True)
                        for ch in damage.get('channels_exploited', []):
                            st.markdown(f'<span class="chip chip-channel">{ch}</span>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================
# GRAPH FORENSICS
# ============================================================
elif page == "🕸️ Graph Forensics":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Graph Forensics</div>
        <div class="hero-subtitle">Visualize hidden money laundering topologies and mule ring structures</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        suspect_id = st.text_input("Suspect Entity:", "U00001")
    with col2:
        max_edges = st.slider("Max connections:", 10, 200, 80)

    if st.button("🔍 Generate Forensic Web", use_container_width=True):
        with st.spinner(f"Mapping {suspect_id}..."):
            df = pd.read_csv("data/transactions.csv")
            users_df = pd.read_csv("data/users.csv")
            mule_ids = set(users_df[users_df['is_mule'] == 1]['user_id'])
            sanc_ids = set(users_df[users_df['is_sanctioned'] == 1]['user_id'])

            sus_txns = df[(df['sender_id'] == suspect_id) | (df['receiver_id'] == suspect_id)]
            if len(sus_txns) == 0:
                st.warning("No transactions found.")
            else:
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">CONNECTIONS</div><div class="metric-value">{len(sus_txns)}</div></div>""", unsafe_allow_html=True)
                unique = set(sus_txns['sender_id']).union(set(sus_txns['receiver_id']))
                with c2: st.markdown(f"""<div class="metric-card"><div class="metric-label">ENTITIES</div><div class="metric-value">{len(unique)}</div></div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">VOLUME</div><div class="metric-value">${sus_txns['amount'].sum():,.0f}</div></div>""", unsafe_allow_html=True)
                with c4: st.markdown(f"""<div class="metric-card"><div class="metric-label">CHANNELS</div><div class="metric-value">{sus_txns['channel'].nunique() if 'channel' in sus_txns else 0}</div></div>""", unsafe_allow_html=True)

                nodes, edges, added = [], [], set()
                nodes.append(Node(id=suspect_id, label=suspect_id, size=500, color="#ef4444"))
                added.add(suspect_id)

                ch_colors = {'mobile_app': '#4ade80', 'web': '#60a5fa', 'atm': '#f87171', 'upi': '#fbbf24', 'wire': '#f472b6', 'branch': '#22d3ee'}
                for _, row in sus_txns.head(max_edges).iterrows():
                    for uid in [str(row['sender_id']), str(row['receiver_id'])]:
                        if uid not in added:
                            color = "#f97316" if uid in mule_ids else "#ef4444" if uid in sanc_ids else "#6366f1"
                            nodes.append(Node(id=uid, label=uid, size=300 if uid in mule_ids else 200, color=color))
                            added.add(uid)
                    edges.append(Edge(source=str(row['sender_id']), target=str(row['receiver_id']),
                        label=f"${row['amount']}", color=ch_colors.get(str(row.get('channel', '')), '#475569')))

                st.markdown("**🔴 Suspect** • **🟠 Mule** • **🟣 Normal** | Edges: 🟢Mobile 🔵Web 🔴ATM 🟡UPI 🩷Wire 🩵Branch")
                config = Config(width=1000, height=600, directed=True, nodeHighlightBehavior=True, highlightColor="#a855f7",
                    node={'labelProperty': 'label', 'renderLabel': True}, link={'labelProperty': 'label', 'renderLabel': False})
                agraph(nodes=nodes, edges=edges, config=config)

                if 'channel' in sus_txns.columns:
                    st.markdown('<div class="section-header">📊 Channel Breakdown</div>', unsafe_allow_html=True)
                    st.dataframe(sus_txns.groupby('channel').agg(count=('amount', 'count'), total=('amount', 'sum'), avg=('amount', 'mean')).round(2), use_container_width=True)

# ============================================================
# RING DISCOVERY
# ============================================================
elif page == "🔮 Ring Discovery":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Mule Ring Discovery</div>
        <div class="hero-subtitle">Louvain community detection automatically finds hidden criminal clusters</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Run Community Detection", use_container_width=True):
        with st.spinner("Running Louvain algorithm on entire graph..."):
            try:
                result = requests.get(f"{API_URL}/communities", timeout=30).json()
                if 'error' in result:
                    st.error(result['error'])
                else:
                    communities = result.get('suspicious_communities', [])
                    st.success(f"Found **{result['total_communities_found']}** suspicious communities")

                    for i, comm in enumerate(communities):
                        sus = comm['suspicion_score']
                        cls = "community-critical" if sus > 50 else "community-high" if sus > 30 else "community-moderate"
                        threat = "🔴 CRITICAL" if sus > 50 else "🟡 HIGH" if sus > 30 else "🟢 MODERATE"

                        with st.expander(f"{threat} Community #{comm['community_id']} — {comm['size']} members | Score: {sus}", expanded=(i < 3)):
                            c1, c2, c3, c4 = st.columns(4)
                            with c1: st.metric("Members", comm['size'])
                            with c2: st.metric("Density", f"{comm['density']:.4f}")
                            with c3: st.metric("Avg Risk", f"{comm['avg_risk']}%")
                            with c4: st.metric("Known Mules", comm['known_mules'])

                            st.markdown("**Members:** " + " ".join([f"`{m}`" for m in comm.get('members', [])]))

                            members = comm.get('members', [])
                            if len(members) >= 2:
                                df = pd.read_csv("data/transactions.csv")
                                comm_txns = df[(df['sender_id'].isin(members)) & (df['receiver_id'].isin(members))]
                                if len(comm_txns) > 0:
                                    mule_ids = set(pd.read_csv("data/users.csv").query("is_mule == 1")['user_id'])
                                    c_nodes = [Node(id=m, label=m, size=300, color="#ef4444" if m in mule_ids else "#6366f1") for m in members if m not in set()]
                                    c_added = set()
                                    c_nodes_final = []
                                    for m in members:
                                        if m not in c_added:
                                            c_nodes_final.append(Node(id=m, label=m, size=300, color="#ef4444" if m in mule_ids else "#6366f1"))
                                            c_added.add(m)
                                    c_edges = [Edge(source=str(r['sender_id']), target=str(r['receiver_id']), color="#fbbf24") for _, r in comm_txns.head(50).iterrows()]
                                    agraph(nodes=c_nodes_final, edges=c_edges, config=Config(width=800, height=400, directed=True, nodeHighlightBehavior=True))

            except Exception as e:
                st.error(f"Error: {e}")

# ============================================================
# ENTITY PROFILER
# ============================================================
elif page == "👤 Entity Profiler":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Entity Profiler</div>
        <div class="hero-subtitle">Deep-dive into trust scores, ownership links, and behavioral patterns</div>
    </div>
    """, unsafe_allow_html=True)

    entity_id = st.text_input("Entity ID:", "U00001")
    if st.button("🔍 Profile Entity", use_container_width=True):
        try:
            trust = requests.get(f"{API_URL}/trust/{entity_id}", timeout=3).json()
            tier = trust['trust_tier']
            status = "🚨 FLAGGED" if trust['is_flagged'] else "🚫 SANCTIONED" if trust['is_sanctioned'] else "✅ CLEAN"

            st.markdown(f"""<div class="glass-card">
                <div style="color:#e2e8f0; font-size:24px; font-weight:800;">{entity_id}</div>
                <div style="color:#94a3b8; font-size:14px;">Status: {status} | Tier {tier}: {trust['trust_label']}</div>
            </div>""", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">TRUST TIER</div><div class="metric-value">T{tier}</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="metric-card"><div class="metric-label">MAX TRANSFER</div><div class="metric-value">${trust['max_transfer']:,}</div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">TRANSACTIONS</div><div class="metric-value">{trust['total_transactions']}</div></div>""", unsafe_allow_html=True)
            with c4:
                cls = "metric-red" if trust['is_flagged'] or trust['is_sanctioned'] else "metric-green"
                st.markdown(f"""<div class="metric-card {cls}"><div class="metric-label">STATUS</div><div class="metric-value">{'⚠️' if trust['is_flagged'] else '✅'}</div></div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-header">📡 Channels</div>', unsafe_allow_html=True)
                for ch in trust.get('channels_used', []):
                    st.markdown(f'<span class="chip chip-channel">{ch}</span>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="section-header">🌍 Countries</div>', unsafe_allow_html=True)
                for c in trust.get('countries_connected', []):
                    cls = "chip-risk-high" if c in ['KY','PA','VG','RU'] else "chip-risk-low"
                    st.markdown(f'<span class="chip {cls}">{c}</span>', unsafe_allow_html=True)

            try:
                own = requests.get(f"{API_URL}/ownership/{entity_id}", timeout=3).json()
                if own.get('linked_accounts'):
                    st.markdown('<div class="section-header">👥 Linked Accounts</div>', unsafe_allow_html=True)
                    for la in own['linked_accounts']:
                        st.markdown(f'<span class="chip chip-risk-high">🔗 {la}</span>', unsafe_allow_html=True)
            except:
                pass

            df = pd.read_csv("data/transactions.csv")
            entity_txns = df[(df['sender_id'] == entity_id) | (df['receiver_id'] == entity_id)]
            if len(entity_txns) > 0:
                st.markdown('<div class="section-header">📊 Transaction History</div>', unsafe_allow_html=True)
                cols = ['timestamp', 'sender_id', 'receiver_id', 'amount', 'channel']
                available = [c for c in cols if c in entity_txns.columns]
                st.dataframe(entity_txns[available].tail(50), use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================
# ANALYTICS
# ============================================================
elif page == "📊 Analytics":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Network Analytics</div>
        <div class="hero-subtitle">Cross-channel visibility across all payment rails and jurisdictions</div>
    </div>
    """, unsafe_allow_html=True)

    df = pd.read_csv("data/transactions.csv")
    users_df = pd.read_csv("data/users.csv")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">TRANSACTIONS</div><div class="metric-value">{len(df):,}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card"><div class="metric-label">TOTAL VOLUME</div><div class="metric-value">${df['amount'].sum():,.0f}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card"><div class="metric-label">ENTITIES</div><div class="metric-value">{len(set(df['sender_id']).union(set(df['receiver_id']))):,}</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="metric-card"><div class="metric-label">AVG AMOUNT</div><div class="metric-value">${df['amount'].mean():,.0f}</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    if 'channel' in df.columns:
        st.markdown('<div class="section-header">📡 Volume by Channel</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Transaction Count**")
            st.bar_chart(df.groupby('channel').size())
        with col2:
            st.markdown("**Total Volume ($)**")
            st.bar_chart(df.groupby('channel')['amount'].sum())

        st.dataframe(df.groupby('channel').agg(count=('amount', 'count'), total=('amount', 'sum'), avg=('amount', 'mean'), max_amt=('amount', 'max')).round(2), use_container_width=True)

    if 'sender_country' in df.columns and 'receiver_country' in df.columns:
        st.markdown('<div class="section-header">🌍 Cross-Border Analysis</div>', unsafe_allow_html=True)
        cross = df[df['sender_country'] != df['receiver_country']]
        domestic = df[df['sender_country'] == df['receiver_country']]

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">CROSS-BORDER</div><div class="metric-value">{len(cross):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="metric-card"><div class="metric-label">DOMESTIC</div><div class="metric-value">{len(domestic):,}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="metric-card metric-amber"><div class="metric-label">CROSS-BORDER %</div><div class="metric-value">{len(cross)/max(len(df),1)*100:.1f}%</div></div>""", unsafe_allow_html=True)
        with c4: st.markdown(f"""<div class="metric-card metric-red"><div class="metric-label">CB VOLUME</div><div class="metric-value">${cross['amount'].sum():,.0f}</div></div>""", unsafe_allow_html=True)

        if len(cross) > 0:
            st.markdown("#### Top 10 Corridors")
            corridors = cross.groupby(['sender_country', 'receiver_country']).agg(count=('amount', 'count'), volume=('amount', 'sum')).sort_values('volume', ascending=False).head(10).round(2)
            st.dataframe(corridors, use_container_width=True)

    if 'is_suspicious' in df.columns:
        st.markdown('<div class="section-header">🎯 Threat Breakdown</div>', unsafe_allow_html=True)
        sus = df[df['is_suspicious'] == 1]
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="metric-card metric-green"><div class="metric-label">NORMAL</div><div class="metric-value">{len(df) - len(sus):,}</div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="metric-card metric-red"><div class="metric-label">SUSPICIOUS</div><div class="metric-value">{len(sus):,}</div></div>""", unsafe_allow_html=True)
        with c3: st.markdown(f"""<div class="metric-card metric-amber"><div class="metric-label">SUS RATE</div><div class="metric-value">{len(sus)/max(len(df),1)*100:.1f}%</div></div>""", unsafe_allow_html=True)

        if 'channel' in sus.columns and len(sus) > 0:
            st.markdown("**Suspicious by Channel**")
            st.bar_chart(sus.groupby('channel').size())

    st.markdown('<div class="section-header">💰 Structuring Detection ($8,500 - $9,999)</div>', unsafe_allow_html=True)
    structuring = df[(df['amount'] >= 8500) & (df['amount'] <= 9999)]
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"""<div class="metric-card metric-amber"><div class="metric-label">STRUCTURING TXNS</div><div class="metric-value">{len(structuring)}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card metric-red"><div class="metric-label">STRUCTURING VOL</div><div class="metric-value">${structuring['amount'].sum():,.0f}</div></div>""", unsafe_allow_html=True)
    if len(structuring) > 0:
        cols = ['timestamp', 'sender_id', 'receiver_id', 'amount', 'channel']
        available = [c for c in cols if c in structuring.columns]
        st.dataframe(structuring[available].head(30), use_container_width=True)

    st.markdown('<div class="section-header">👥 User Distribution</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card"><div class="metric-label">TOTAL USERS</div><div class="metric-value">{len(users_df):,}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card metric-red"><div class="metric-label">MULE ACCOUNTS</div><div class="metric-value">{users_df['is_mule'].sum()}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card metric-red"><div class="metric-label">SANCTIONED</div><div class="metric-value">{users_df['is_sanctioned'].sum()}</div></div>""", unsafe_allow_html=True)

    st.markdown("**Account Types**")
    st.bar_chart(users_df['account_type'].value_counts())

# ============================================================
# INTEL SHARING
# ============================================================
elif page == "🔒 Intel Sharing":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Privacy-Safe Intelligence</div>
        <div class="hero-subtitle">Generate anonymized risk intelligence for inter-bank sharing (ISO 20022)</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <div style="color:#a5b4fc; font-weight:700;">How It Works</div>
        <div style="color:#94a3b8; font-size:14px; margin-top:8px;">
            Banks cannot share customer names (GDPR/privacy). But they CAN share <strong style="color:#e2e8f0;">SHA-256 hashed IDs</strong>
            and <strong style="color:#e2e8f0;">behavioral risk signals</strong>. This enables cross-institutional mule ring detection
            without exposing Personally Identifiable Information (PII).
        </div>
    </div>
    """, unsafe_allow_html=True)

    entity_id = st.text_input("Entity ID:", "U00001")
    if st.button("🔐 Generate Intelligence Package", use_container_width=True):
        try:
            intel = requests.get(f"{API_URL}/intel/{entity_id}", timeout=3).json()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-header">🔑 Entity Identification</div>', unsafe_allow_html=True)
                flagged_str = "🔴 YES" if intel['is_flagged'] else "🟢 NO"
                sanctioned_str = "🔴 YES" if intel['is_sanctioned'] else "🟢 NO"
                st.markdown(f"""<div class="intel-box">
                    <div><span style="color:#64748b;">HASHED ID:</span> <span style="color:#a5b4fc;">{intel['hashed_entity_id']}</span></div>
                    <div><span style="color:#64748b;">RISK SCORE:</span> <span style="color:#ef4444;">{intel['risk_score']}%</span></div>
                    <div><span style="color:#64748b;">FLAGGED:</span> {flagged_str}</div>
                    <div><span style="color:#64748b;">SANCTIONED:</span> {sanctioned_str}</div>
                    <div><span style="color:#64748b;">TRUST TIER:</span> <span style="color:#e2e8f0;">{intel['trust_tier']}</span></div>
                    <div><span style="color:#64748b;">STANDARD:</span> <span style="color:#22c55e;">{intel['sharing_standard']}</span></div>
                    <div><span style="color:#64748b;">GENERATED:</span> <span style="color:#94a3b8;">{intel['generated_at']}</span></div>
                </div>""", unsafe_allow_html=True)

            with col2:
                behav = intel.get('behavioral_signals', {})
                st.markdown('<div class="section-header">📊 Behavioral Signals</div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="intel-box">
                    <div><span style="color:#64748b;">CHANNELS:</span> <span style="color:#e2e8f0;">{behav.get('channels_count', 0)}</span></div>
                    <div><span style="color:#64748b;">CROSS-BORDER:</span> <span style="color:#e2e8f0;">{behav.get('cross_border_count', 0)}</span></div>
                    <div><span style="color:#64748b;">COUNTRIES:</span> <span style="color:#e2e8f0;">{behav.get('countries_count', 0)}</span></div>
                    <div><span style="color:#64748b;">TXN COUNT:</span> <span style="color:#e2e8f0;">{behav.get('transaction_count', 0)}</span></div>
                </div>""", unsafe_allow_html=True)

                graph = intel.get('graph_signals', {})
                st.markdown('<div class="section-header">🕸️ Graph Signals</div>', unsafe_allow_html=True)
                pt_str = "🔴 YES" if graph.get('is_pass_through') else "🟢 NO"
                cf_str = "🔴 YES" if graph.get('has_circular_flow') else "🟢 NO"
                st.markdown(f"""<div class="intel-box">
                    <div><span style="color:#64748b;">IN-DEGREE:</span> <span style="color:#e2e8f0;">{graph.get('in_degree', 0)}</span></div>
                    <div><span style="color:#64748b;">OUT-DEGREE:</span> <span style="color:#e2e8f0;">{graph.get('out_degree', 0)}</span></div>
                    <div><span style="color:#64748b;">PASS-THROUGH:</span> {pt_str}</div>
                    <div><span style="color:#64748b;">NEIGHBORS:</span> <span style="color:#e2e8f0;">{graph.get('neighbor_count', 0)}</span></div>
                    <div><span style="color:#64748b;">CIRCULAR:</span> {cf_str}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-header">📦 Raw API Response (JSON)</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color:#64748b; font-size:12px; margin-bottom:8px;">This JSON would be sent to partner banks via encrypted API channel:</div>', unsafe_allow_html=True)
            st.json(intel)

        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================
# SAR REPORTS
# ============================================================
elif page == "📜 SAR Reports":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Suspicious Activity Reports</div>
        <div class="hero-subtitle">Regulator-ready reports with confidence scores and AI-generated narratives</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        blocked = requests.get(f"{API_URL}/blocked", timeout=3).json()
        if not blocked:
            st.info("No SAR reports yet. Use the Transaction Scanner or Attack Simulator to generate them.")
        else:
            st.markdown(f"""<div class="metric-card" style="margin-bottom:20px;">
                <div class="metric-label">TOTAL SAR REPORTS</div>
                <div class="metric-value">{len(blocked)}</div>
            </div>""", unsafe_allow_html=True)

            summary = []
            for r in blocked:
                summary.append({
                    "TXN": r['txn_id'], "Risk": f"{r['risk_score']}%",
                    "Conf": f"{r.get('confidence', 0)*100:.0f}%",
                    "Channel": r.get('channel', '-'),
                    "Route": f"{r.get('sender_country', '?')}→{r.get('receiver_country', '?')}",
                    "Layers": len(r.get('detection_layers_triggered', []))
                })
            st.dataframe(pd.DataFrame(summary), use_container_width=True)

            st.markdown("---")

            for i, report in enumerate(reversed(blocked)):
                risk_icon = "🔴" if report['risk_score'] > 80 else "🟡" if report['risk_score'] > 50 else "🟢"
                with st.expander(f"{risk_icon} SAR #{len(blocked)-i} — {report['txn_id']} | Risk: {report['risk_score']}% | Conf: {report.get('confidence', 0)*100:.0f}%", expanded=(i == 0)):

                    c1, c2, c3, c4 = st.columns(4)
                    with c1: st.metric("Risk", f"{report['risk_score']}%")
                    with c2: st.metric("Confidence", f"{report.get('confidence', 0)*100:.0f}%")
                    with c3: st.metric("Sender Risk", f"{report.get('sender_risk', 0)}%")
                    with c4: st.metric("Receiver Risk", f"{report.get('receiver_risk', 0)}%")

                    st.markdown(f"""
                    | Field | Value |
                    |-------|-------|
                    | **Transaction** | `{report['txn_id']}` |
                    | **Channel** | {report.get('channel', '-')} |
                    | **Route** | {report.get('sender_country', '?')} → {report.get('receiver_country', '?')} |
                    | **Trust Tier** | T{report.get('trust_tier', '?')} ({report.get('trust_label', '')}) |
                    | **Block Reason** | {report.get('block_reason', '-')} |
                    | **Layers** | {', '.join(report.get('detection_layers_triggered', []))} |
                    """)

                    breakdown = report.get('risk_breakdown', {})
                    if breakdown:
                        active = {k: v for k, v in breakdown.items() if v > 0}
                        if active:
                            bd_df = pd.DataFrame({'Layer': [k.replace('_', ' ').title() for k in active.keys()], 'Score': list(active.values())}).sort_values('Score', ascending=True)
                            st.bar_chart(bd_df.set_index('Layer'))

                    if report.get('sar_report'):
                        st.markdown(f"""<div class="sar-box">
                            <div class="sar-meta">Qwen-2.5 3B (Local LLM) • Confidence: {report.get('confidence', 0)*100:.0f}% • {len(report.get('detection_layers_triggered', []))} layers</div>
                            <div class="sar-text">{report['sar_report']}</div>
                        </div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Cannot connect to API: {e}")