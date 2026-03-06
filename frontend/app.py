"""Streamlit Dashboard for OSINT Platform"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/v1"

# Page configuration
st.set_page_config(
    page_title="OSINT Terminal v2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Visibility Cyber Theme
st.markdown("""
<style>
    /* Import Hacker Font */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;700&family=Share+Tech+Mono&display=swap');
    
    /* Brighter Theme Base - Much More Visible */
    .stApp {
        background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
        color: #ffffff;
        font-family: 'Fira Code', 'Share Tech Mono', monospace;
    }
    
    /* Sidebar - Brighter Theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e2749 0%, #2a3358 100%);
        border-right: 3px solid #00ff88;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
        font-family: 'Fira Code', monospace !important;
    }
    
    /* Sidebar text - HIGH VISIBILITY */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Main content text - HIGH CONTRAST */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
        color: #ffffff !important;
        font-size: 15px !important;
    }
    
    /* Labels - BRIGHT AND VISIBLE */
    label, .stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label {
        color: #00ffdd !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        text-shadow: 0 0 5px rgba(0,255,221,0.5);
    }
    
    /* Ensure all form labels are highly visible */
    .stSelectbox label p, .stMultiSelect label p {
        color: #00ffdd !important;
        font-weight: 700 !important;
    }
    
    /* Regular text - WHITE */
    p, span, div {
        color: #ffffff !important;
    }
    
    /* Form labels - BRIGHT */
    .stForm label {
        color: #00ff88 !important;
        font-weight: 700 !important;
    }
    
    /* Main Header - BRIGHTER Cyber Style */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00ff88, #00ddff, #ff0099);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 1rem 0 2rem 0;
        font-family: 'Fira Code', monospace;
        text-shadow: 0 0 30px rgba(0,255,136,0.8);
        letter-spacing: 2px;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 10px #00ff88); }
        to { filter: drop-shadow(0 0 25px #00ff88); }
    }
    
    /* Terminal-style inputs - HIGH VISIBILITY */
    .stTextInput input, .stTextArea textarea {
        background-color: #1e2749 !important;
        color: #ffffff !important;
        border: 2px solid #00ff88 !important;
        border-radius: 6px !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    /* Input text - BRIGHT WHITE */
    .stTextInput input:not(:placeholder-shown) {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #88aaff !important;
        opacity: 0.9 !important;
        -webkit-text-fill-color: #88aaff !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 2px solid #00ddff !important;
        box-shadow: 0 0 20px rgba(0,221,255,0.8) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    /* Help text - MORE VISIBLE */
    .stTextInput > div > div:last-child,
    .stTextArea > div > div:last-child,
    .stSelectbox > div > div:last-child,
    .stMultiSelect > div > div:last-child,
    .stNumberInput > div > div:last-child {
        color: #88aaff !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    
    /* Input containers - WHITE TEXT */
    .stTextInput div, .stTextInput span,
    .stSelectbox div, .stSelectbox span,
    .stMultiSelect div, .stMultiSelect span {
        color: #ffffff !important;
    }
    
    /* Input wrapper styling */
    .stTextInput > div > div {
        background-color: #1e2749 !important;
    }
    
    /* Metric Cards - BRIGHT AND VISIBLE */
    [data-testid="stMetricValue"] {
        color: #00ff88 !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        font-family: 'Fira Code', monospace !important;
        text-shadow: 0 0 10px rgba(0,255,136,0.6);
    }
    
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 1rem !important;
        font-family: 'Fira Code', monospace !important;
        font-weight: 600 !important;
    }
    
    /* Buttons - HIGHLY VISIBLE */
    .stButton button {
        background: linear-gradient(90deg, #00ff88, #00ddff) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 2.5rem !important;
        font-family: 'Fira Code', monospace !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s !important;
        font-size: 15px !important;
        box-shadow: 0 0 15px rgba(0,255,136,0.5);
    }
    
    .stButton button:hover {
        transform: scale(1.08);
        box-shadow: 0 0 30px rgba(0,255,136,1) !important;
    }
    
    /* Dataframe/Table Style - HIGH VISIBILITY */
    .dataframe {
        background-color: #1e2749 !important;
        color: #ffffff !important;
        border: 2px solid #00ff88 !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 14px !important;
    }
    
    .dataframe th {
        background-color: #2a3358 !important;
        color: #00ffdd !important;
        border: 1px solid #00ff88 !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 10px !important;
    }
    
    .dataframe td {
        border: 1px solid #3a4568 !important;
        color: #ffffff !important;
        padding: 8px !important;
    }
    
    /* Streamlit dataframe container - BRIGHT */
    [data-testid="stDataFrame"] {
        background-color: #1e2749 !important;
    }
    
    [data-testid="stDataFrame"] table {
        color: #ffffff !important;
    }
    
    [data-testid="stDataFrame"] th {
        background-color: #2a3358 !important;
        color: #00ffdd !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stDataFrame"] td {
        color: #ffffff !important;
    }
    
    /* Success/Error/Warning Messages - VISIBLE */
    .stAlert {
        background-color: #1e2749 !important;
        border-left: 5px solid #00ff88 !important;
        color: #ffffff !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    
    .stSuccess {
        border-left-color: #00ff88 !important;
        background-color: rgba(0,255,136,0.1) !important;
    }
    
    .stError {
        border-left-color: #ff0099 !important;
        color: #ff99cc !important;
        background-color: rgba(255,0,153,0.1) !important;
    }
    
    .stWarning {
        border-left-color: #ffdd00 !important;
        color: #ffff88 !important;
        background-color: rgba(255,221,0,0.1) !important;
    }
    
    .stInfo {
        border-left-color: #00ddff !important;
        color: #88eeff !important;
        background-color: rgba(0,221,255,0.1) !important;
    }
    
    /* Selectbox and Multiselect - BRIGHT */
    .stSelectbox, .stMultiSelect {
        font-family: 'Fira Code', monospace !important;
    }
    
    .stSelectbox > div, .stMultiSelect > div {
        background-color: #1e2749 !important;
        color: #ffffff !important;
        border: 2px solid #00ff88 !important;
    }
    
    /* Selectbox and MultiSelect text - WHITE */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Selected values text - BRIGHT */
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    
    /* Placeholder text - VISIBLE */
    .stSelectbox input::placeholder,
    .stMultiSelect input::placeholder {
        color: #88aaff !important;
        opacity: 0.9 !important;
    }
    
    /* Dropdown options - HIGH CONTRAST */
    [data-baseweb="select"] {
        background-color: #1e2749 !important;
        color: #ffffff !important;
    }
    
    [data-baseweb="popover"] {
        background-color: #1e2749 !important;
        border: 2px solid #00ff88 !important;
    }
    
    /* Dropdown menu items - VISIBLE */
    [role="option"] {
        background-color: #1e2749 !important;
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    
    [role="option"]:hover {
        background-color: #2a3358 !important;
        color: #00ffdd !important;
    }
    
    /* Multi-select tags/chips - HIGH VISIBILITY */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #00ff88 !important;
        color: #000000 !important;
        border: 2px solid #00ff88 !important;
        font-weight: 700 !important;
    }
    
    /* Number input - BRIGHT */
    .stNumberInput input {
        background-color: #1e2749 !important;
        color: #ffffff !important;
        border: 2px solid #00ff88 !important;
        font-weight: 600 !important;
    }
    
    /* Checkbox - VISIBLE */
    .stCheckbox span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Expander - CLEAR */
    .streamlit-expanderHeader {
        background-color: #2a3358 !important;
        color: #ffffff !important;
        border: 2px solid #3a4568 !important;
        font-weight: 700 !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #3a4568 !important;
        border-color: #00ff88 !important;
    }
    
    /* Code blocks - READABLE */
    .stCodeBlock, code {
        background-color: #1e2749 !important;
        color: #00ff88 !important;
        border: 2px solid #3a4568 !important;
        font-size: 14px !important;
    }
    
    /* Headers h1, h2, h3 - BRIGHT */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Fira Code', monospace !important;
        font-weight: 700 !important;
    }
    
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.5rem !important; }
    
    /* Spinner text - VISIBLE */
    .stSpinner > div {
        color: #00ff88 !important;
    }
    
    /* Info, Success, Warning, Error boxes content - WHITE TEXT */
    .stAlert, .element-container .stAlert {
        color: #ffffff !important;
    }
    
    .stAlert > div {
        color: #ffffff !important;
    }
    
    /* Radio buttons - CLEAR */
    .stRadio label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .stRadio > div {
        color: #ffffff !important;
    }
    
    /* Progress bar text - BRIGHT */
    .stProgress > div > div {
        color: #00ff88 !important;
        font-weight: 700 !important;
    }
    
    /* Tabs - HIGH VISIBILITY */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1f3a;
        border-bottom: 3px solid #00ff88;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #ffffff !important;
        font-family: 'Fira Code', monospace !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00ff88 !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* ASCII Art Header - BRIGHTER */
    .ascii-header {
        font-family: 'Courier New', 'Consolas', monospace;
        color: #00ff88;
        text-align: center;
        line-height: 1.1;
        font-size: 0.7rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 15px rgba(0,255,136,1);
        white-space: pre;
        overflow-x: auto;
        padding: 15px;
        background: rgba(30, 39, 73, 0.9);
        border: 3px solid #00ff88;
        border-radius: 8px;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0e27;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ff41;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #00d9ff;
    }
    
    /* Glowing divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00ff41, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}


def get_statistics():
    """Get system statistics"""
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get statistics: {e}")
        return None


def search_entities(query, entity_types=None, limit=100, deduplicate=False, exclude_tables=None, exclude_sources=None):
    """Search entities"""
    try:
        payload = {
            "query": query,
            "limit": limit,
            "deduplicate": deduplicate
        }
        
        if entity_types:
            payload["entity_types"] = entity_types
        
        if exclude_tables:
            payload["exclude_tables"] = exclude_tables
        
        if exclude_sources:
            payload["exclude_sources"] = exclude_sources
        
        response = requests.post(f"{API_BASE}/search", json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Search failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Search error: {e}")
        return None


def get_entity_relationships(entity_id, depth=1):
    """Get entity relationships"""
    try:
        response = requests.get(
            f"{API_BASE}/entities/{entity_id}/relationships",
            params={"depth": depth},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get relationships: {e}")
        return None


def start_import_job(source_name, tables=None, field_mapping=None, dump_file=None):
    """Start MySQL import job"""
    try:
        payload = {
            "source_name": source_name,
            "tables": tables,
            "field_mapping": field_mapping,
            "dump_file": dump_file
        }
        
        response = requests.post(f"{API_BASE}/import/mysql", json=payload, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Import failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Import error: {e}")
        return None


def get_import_status(job_id):
    """Get import job status"""
    try:
        response = requests.get(f"{API_BASE}/import/status/{job_id}", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to get job status: {e}")
        return None


def main():
    """Main application"""
    
    # ASCII Art Header
    st.markdown('''
    <div class="ascii-header">
╔═══════════════════════════════════════════════════════════════════════════╗
║   ██████╗ ███████╗██╗███╗   ██╗████████╗    ████████╗███████╗██████╗     ║
║  ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝    ╚══██╔══╝██╔════╝██╔══██╗    ║
║  ██║   ██║███████╗██║██╔██╗ ██║   ██║          ██║   █████╗  ██████╔╝    ║
║  ██║   ██║╚════██║██║██║╚██╗██║   ██║          ██║   ██╔══╝  ██╔══██╗    ║
║  ╚██████╔╝███████║██║██║ ╚████║   ██║          ██║   ███████╗██║  ██║    ║
║   ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝          ╚═╝   ╚══════╝╚═╝  ╚═╝    ║
╚═══════════════════════════════════════════════════════════════════════════╝
    </div>
    ''', unsafe_allow_html=True)    
    # Main Header
    st.markdown('<div class="main-header">⚡ CYBER INTELLIGENCE TERMINAL ⚡</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚡ NAVIGATION MENU")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["🏠 COMMAND CENTER", "🔍 INTEL SEARCH", "📊 ANALYTICS", "📥 DATA IMPORT", "🕸️ NETWORK MAP", "⚙️ SYSTEM STATUS"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Backend health check
        st.markdown("### 🔌 SYSTEM STATUS")
        is_healthy, health_data = check_backend_health()
        
        if is_healthy:
            st.success("✅ CORE ONLINE")
            
            services = health_data.get("services", {})
            service_icons = {
                "mysql": "🗄️",
                "mongodb": "🍃",
                "elasticsearch": "🔍",
                "neo4j": "🕸️",
                "redis": "⚡"
            }
            
            for service, status in services.items():
                icon = service_icons.get(service, "💾")
                status_icon = "✅" if status else "❌"
                st.text(f"{status_icon} {icon} {service.upper()}")
        else:
            st.error("❌ CORE OFFLINE")
            st.warning("⚠️ Initialize backend systems")
        
        st.markdown("---")
        st.markdown("### 🛡️ SECURITY LEVEL")
        st.progress(0.95)
        st.markdown("**CLASSIFIED**")
    
    # Main content routing
    if page == "🏠 COMMAND CENTER":
        show_dashboard()
    elif page == "🔍 INTEL SEARCH":
        show_search()
    elif page == "📊 ANALYTICS":
        show_statistics()
    elif page == "📥 DATA IMPORT":
        show_import()
    elif page == "🕸️ NETWORK MAP":
        show_relationships()
    elif page == "⚙️ SYSTEM STATUS":
        show_system_status()


def show_dashboard():
    """Show dashboard overview - Cyber themed"""
    st.markdown("## 🎯 COMMAND CENTER")
    st.markdown("### Real-time Intelligence Dashboard")
    
    stats = get_statistics()
    
    if stats:
        # Overview metrics with cyber styling
        col1, col2, col3, col4 = st.columns(4)
        
        es_stats = stats.get("elasticsearch", {})
        mongo_stats = stats.get("mongodb", {})
        neo4j_stats = stats.get("neo4j", {})
        
        with col1:
            total_es = es_stats.get("total_entities", 0)
            st.metric("🔍 INDEXED INTEL", f"{total_es:,}", delta="Live")
        
        with col2:
            total_mongo = mongo_stats.get("total_entities", 0)
            st.metric("💾 ARCHIVED DATA", f"{total_mongo:,}", delta="Secured")
        
        with col3:
            total_nodes = neo4j_stats.get("total_nodes", 0)
            st.metric("🕸️ NETWORK NODES", f"{total_nodes:,}", delta="Mapped")
        
        with col4:
            total_rels = neo4j_stats.get("total_relationships", 0)
            st.metric("🔗 CONNECTIONS", f"{total_rels:,}", delta="Active")
        
        st.markdown("---")
        
        # Entity type distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 TARGET TYPE ANALYSIS")
            by_type = es_stats.get("by_type", {})
            
            if by_type:
                df_types = pd.DataFrame(list(by_type.items()), columns=["Type", "Count"])
                fig = px.pie(
                    df_types, 
                    values="Count", 
                    names="Type",
                    color_discrete_sequence=px.colors.sequential.Viridis,
                    hole=0.4
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#00ff41', family='Fira Code'),
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("⚠️ No intel data available")
        
        with col2:
            st.markdown("### 🎯 SOURCE DISTRIBUTION")
            by_source = es_stats.get("by_source", {})
            
            if by_source:
                df_sources = pd.DataFrame(list(by_source.items()), columns=["Source", "Count"])
                fig = px.bar(
                    df_sources, 
                    x="Source", 
                    y="Count",
                    color="Count",
                    color_continuous_scale=[[0, '#00ff41'], [1, '#00d9ff']]
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#00ff41', family='Fira Code'),
                    xaxis=dict(gridcolor='#1a1a2e'),
                    yaxis=dict(gridcolor='#1a1a2e')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("⚠️ No source data available")
        
        # Additional cyber-themed stats
        st.markdown("---")
        st.markdown("### ⚡ SYSTEM PERFORMANCE")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔥 Query Speed", "< 100ms", delta="Optimized")
        with col2:
            st.metric("🛡️ Security Level", "MAXIMUM", delta="Protected")
        with col3:
            st.metric("⚡ System Uptime", "99.9%", delta="Stable")
            
    else:
        st.error("❌ Unable to establish connection to intelligence systems")
        st.warning("⚠️ Verify backend connectivity")


def show_search():
    """Show search interface - Clean modern dark theme"""
    st.markdown("## 🔍 Intelligence Search")

    # --- session state init ---
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "search_query_used" not in st.session_state:
        st.session_state.search_query_used = ""
    if "search_took" not in st.session_state:
        st.session_state.search_took = 0.0
    if "search_deduplicated" not in st.session_state:
        st.session_state.search_deduplicated = False

    # Search form
    col1, col2, col3 = st.columns([4, 1, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter email, phone, username, domain, IP...",
            key="search_query",
            label_visibility="collapsed"
        )

    with col2:
        limit = st.selectbox(
            "Results",
            [25, 50, 100, 250, 500],
            index=2,
            key="search_limit",
            label_visibility="collapsed"
        )

    with col3:
        search_btn = st.button("🔍 Search", type="primary", use_container_width=True)

    # Advanced filters in expander
    with st.expander("⚙️ Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            entity_types = st.multiselect(
                "Entity Type",
                ["email", "username", "domain", "phone", "ip"],
                default=None,
                help="Filter by specific type"
            )

        with col2:
            exclude_noise = st.checkbox(
                "Exclude Noise Tables",
                value=False,
                help="Exclude system tables like notifications, logs, sessions"
            )

        with col3:
            deduplicate = st.checkbox(
                "Remove Duplicates",
                value=False,
                help="Show only unique entries per source table"
            )

    # Execute search — only when button clicked, then store in session_state
    if search_btn:
        if query:
            # Only exclude noise tables if user explicitly opted in
            exclude_tables = ["notifications", "logs", "sessions", "audit", "cache", "tokens"] if exclude_noise else None

            with st.spinner("🔍 Scanning databases..."):
                results = search_entities(
                    query,
                    entity_types or None,
                    limit,
                    deduplicate=deduplicate,
                    exclude_tables=exclude_tables,
                    exclude_sources=None
                )

            # Persist results in session state so they survive reruns
            st.session_state.search_results = results
            st.session_state.search_query_used = query
            st.session_state.search_took = results.get("took", 0) if results else 0
            st.session_state.search_deduplicated = deduplicate
        else:
            st.warning("⚠️ Please enter a search query")
            st.session_state.search_results = None

    # Always render results from session state (survives button re-clicks, expander interactions)
    results = st.session_state.search_results
    display_query = st.session_state.search_query_used
    took = st.session_state.search_took
    is_deduped = st.session_state.search_deduplicated

    if results is not None:
        total = results.get("total", 0)
        entities = results.get("results", [])

        # Results header
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center;
                    padding: 16px 20px; background: linear-gradient(90deg, #2a3358 0%, #1e2749 100%);
                    border-radius: 10px; margin: 16px 0; border: 3px solid #00ff88;
                    box-shadow: 0 0 20px rgba(0,255,136,0.3);">
            <div>
                <span style="color: #00ff88; font-size: 28px; font-weight: 700;
                             text-shadow: 0 0 10px rgba(0,255,136,0.5);">{total:,}</span>
                <span style="color: #ffffff; font-size: 16px; margin-left: 12px;
                             font-weight: 600;">results for <code>{display_query}</code></span>
            </div>
            <div style="color: #88aaff; font-size: 14px; font-weight: 600;">
                ⚡ {took:.3f}s
                {' • 🧹 Deduplicated' if is_deduped else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if entities:
            # Separate exact vs partial matches
            exact_matches = []
            partial_matches = []

            for entity in entities:
                value = entity.get('value', '').lower()
                email = entity.get('email', '').lower() if entity.get('email') else ''
                search_lower = display_query.lower()

                if value == search_lower or email == search_lower:
                    exact_matches.append(entity)
                else:
                    partial_matches.append(entity)

            if exact_matches:
                st.markdown("""
                <div style="background: linear-gradient(90deg, #00ff88 0%, #2a3358 100%);
                            padding: 12px 20px; border-radius: 8px; margin: 16px 0;
                            border-left: 6px solid #00ff88;
                            box-shadow: 0 0 15px rgba(0,255,136,0.4);">
                    <span style="color: #000000; font-weight: 700; font-size: 16px;">✓ EXACT MATCHES</span>
                </div>
                """, unsafe_allow_html=True)

                for entity in exact_matches:
                    render_entity_card(entity, is_exact=True)

            if partial_matches:
                if exact_matches:
                    st.markdown("""
                    <div style="background: #2a3358; padding: 12px 20px; border-radius: 8px;
                                margin: 20px 0 12px 0; border: 2px solid #00ddff;">
                        <span style="color: #ffffff; font-weight: 700; font-size: 16px;">📋 SIMILAR RESULTS</span>
                    </div>
                    """, unsafe_allow_html=True)

                for entity in partial_matches[:50]:
                    render_entity_card(entity, is_exact=False)

            if len(partial_matches) > 50:
                st.info(f"ℹ️ Showing 50 of {len(partial_matches)} similar results. Refine your search or increase the limit.")

        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: #8b949e;">
                <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                <div style="font-size: 18px; color: #ffffff;">No results found</div>
                <div style="font-size: 14px; margin-top: 8px; color: #88aaff;">
                    Try a broader search term, or disable "Exclude Noise Tables" if enabled
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif not search_btn:
        # Initial state — show hint
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; color: #88aaff;">
            <div style="font-size: 56px; margin-bottom: 16px;">⚡</div>
            <div style="font-size: 20px; color: #ffffff; font-weight: 600;">Enter a search term above and click Search</div>
            <div style="font-size: 14px; margin-top: 10px;">Supports emails, usernames, domains, IPs, phone numbers</div>
        </div>
        """, unsafe_allow_html=True)


def render_entity_card(entity, is_exact=False):
    """Render a single entity as a clean card"""
    entity_type = entity.get('entity_type', 'unknown').upper()
    value = entity.get('value', 'N/A')
    source = entity.get('source', 'Unknown')
    table = entity.get('source_table', 'unknown')
    email = entity.get('email', '')
    username = entity.get('username', '')
    phone = entity.get('phone', '')
    domain = entity.get('domain', '')
    metadata = entity.get('metadata', {})
    
    # Type colors - BRIGHT AND VISIBLE
    type_colors = {
        'EMAIL': '#00ddff',
        'USERNAME': '#cc88ff',
        'DOMAIN': '#00ff88',
        'PHONE': '#ffaa44',
        'IP': '#ff6699',
        'UNKNOWN': '#88aaff'
    }
    color = type_colors.get(entity_type, '#88aaff')
    border_color = '#00ff88' if is_exact else '#3a4568'
    
    # Build card content with HIGH VISIBILITY
    with st.container():
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2a3358 0%, #1e2749 100%); 
                    border: 3px solid {border_color}; border-radius: 10px; 
                    padding: 20px; margin-bottom: 16px; 
                    {'border-left: 8px solid #00ff88; box-shadow: 0 0 20px rgba(0,255,136,0.4);' if is_exact else 'box-shadow: 0 0 10px rgba(58,69,104,0.5);'}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                <div>
                    <span style="background: {color}; color: #000000; padding: 6px 14px; 
                                 border-radius: 6px; font-size: 13px; font-weight: 700; 
                                 border: 2px solid {color}; box-shadow: 0 0 10px {color}88;">{entity_type}</span>
                    <span style="color: #ffffff; font-size: 13px; margin-left: 15px; font-weight: 600;">📁 {table}</span>
                </div>
                <span style="color: #88aaff; font-size: 12px; font-weight: 600;">{source}</span>
            </div>
            <div style="font-family: 'Fira Code', monospace; font-size: 17px; color: #ffffff; 
                        font-weight: 600; margin-bottom: 10px; word-break: break-all;
                        text-shadow: 0 0 5px rgba(255,255,255,0.3);">{value}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("📋 View Details", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show all available fields
                fields = []
                if email and email != value:
                    fields.append(('📧 Email', email))
                if username and username != value:
                    fields.append(('👤 Username', username))
                if phone and phone != value:
                    fields.append(('📱 Phone', phone))
                if domain and domain != value:
                    fields.append(('🌐 Domain', domain))
                
                if fields:
                    for label, val in fields:
                        st.markdown(f"**{label}:** `{val}`")
                
                # Show metadata
                if metadata:
                    st.markdown("**📄 Additional Data:**")
                    for key, val in list(metadata.items())[:8]:
                        if val and str(val).strip() and len(str(val)) < 200:
                            st.text(f"  {key}: {val}")
            
            with col2:
                st.markdown("**ℹ️ Source Info:**")
                st.text(f"Database: {source}")
                st.text(f"Table: {table}")
                
                timestamp = entity.get('timestamp', '')
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                        st.text(f"Date: {dt.strftime('%Y-%m-%d')}")
                    except:
                        pass


def show_statistics():
    """Show detailed statistics"""
    st.header("📊 Detailed Statistics")
    
    if st.button("🔄 Refresh Statistics"):
        st.rerun()
    
    stats = get_statistics()
    
    if stats:
        # Elasticsearch stats
        st.subheader("Elasticsearch Index")
        es_stats = stats.get("elasticsearch", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entities", f"{es_stats.get('total_entities', 0):,}")
        with col2:
            by_type = es_stats.get("by_type", {})
            st.metric("Entity Types", len(by_type))
        with col3:
            by_source = es_stats.get("by_source", {})
            st.metric("Data Sources", len(by_source))
        
        # MongoDB stats
        st.subheader("MongoDB Storage")
        mongo_stats = stats.get("mongodb", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stored Entities", f"{mongo_stats.get('total_entities', 0):,}")
        with col2:
            st.metric("Raw Records", f"{mongo_stats.get('total_raw_records', 0):,}")
        
        # Neo4j stats
        st.subheader("Neo4j Graph Database")
        neo4j_stats = stats.get("neo4j", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Graph Nodes", f"{neo4j_stats.get('total_nodes', 0):,}")
        with col2:
            st.metric("Relationships", f"{neo4j_stats.get('total_relationships', 0):,}")
        
        # Detailed breakdowns
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Entities by Type")
            by_type_df = pd.DataFrame(
                list(es_stats.get("by_type", {}).items()),
                columns=["Type", "Count"]
            ).sort_values("Count", ascending=False)
            
            if not by_type_df.empty:
                st.dataframe(by_type_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("Entities by Source")
            by_source_df = pd.DataFrame(
                list(es_stats.get("by_source", {}).items()),
                columns=["Source", "Count"]
            ).sort_values("Count", ascending=False)
            
            if not by_source_df.empty:
                st.dataframe(by_source_df, use_container_width=True, hide_index=True)


def show_import():
    """Show import interface"""
    st.header("📥 Import Data")
    
    tab1, tab2 = st.tabs(["Start New Import", "Monitor Jobs"])
    
    with tab1:
        st.subheader("Start MySQL Import Job")
        
        with st.form("import_form"):
            source_name = st.text_input("Source Name", placeholder="e.g., leaked_db_2023")
            
            dump_file = st.text_input(
                "MySQL Dump File Path (optional)",
                placeholder="/dumps/database_dump.sql"
            )
            
            tables_input = st.text_area(
                "Tables to Import (one per line, leave empty for all tables)",
                placeholder="users\naccounts\nemails"
            )
            
            st.subheader("Field Mapping Configuration")
            st.info("Map source fields to standard fields: email, ip, domain, username, phone")
            
            field_mapping_text = st.text_area(
                "Field Mapping (JSON format)",
                placeholder='{\n  "users": {\n    "email_addr": "email",\n    "user_name": "username"\n  }\n}',
                height=150
            )
            
            submit = st.form_submit_button("🚀 Start Import", use_container_width=True)
        
        if submit and source_name:
            # Parse tables
            tables = [t.strip() for t in tables_input.split("\n") if t.strip()] if tables_input else None
            
            # Parse field mapping
            field_mapping = None
            if field_mapping_text:
                try:
                    import json
                    field_mapping = json.loads(field_mapping_text)
                except Exception as e:
                    st.error(f"Invalid JSON in field mapping: {e}")
                    return
            
            # Start import
            with st.spinner("Starting import job..."):
                result = start_import_job(
                    source_name,
                    tables,
                    field_mapping,
                    dump_file if dump_file else None
                )
            
            if result:
                st.success(f"✅ Import job started! Job ID: {result.get('job_id')}")
                st.info("Monitor the job progress in the 'Monitor Jobs' tab")
    
    with tab2:
        st.subheader("Monitor Import Jobs")
        
        if st.button("🔄 Refresh Jobs"):
            st.rerun()
        
        try:
            response = requests.get(f"{API_BASE}/import/jobs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                
                if jobs:
                    for job in jobs:
                        with st.expander(f"Job: {job.get('source_name', 'N/A')} - {job.get('status', 'unknown')}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Job ID:** `{job.get('job_id', 'N/A')}`")
                                st.write(f"**Status:** `{job.get('status', 'N/A')}`")
                                st.write(f"**Source:** `{job.get('source_name', 'N/A')}`")
                            
                            with col2:
                                st.write(f"**Started:** `{job.get('started_at', 'N/A')}`")
                                st.write(f"**Total Records:** `{job.get('total_records', 0):,}`")
                                st.write(f"**Processed:** `{job.get('processed_records', 0):,}`")
                else:
                    st.info("No import jobs found")
        except Exception as e:
            st.error(f"Failed to load jobs: {e}")


def show_system_status():
    """Show detailed system status - Cyber themed"""
    st.markdown("## ⚙️ SYSTEM STATUS TERMINAL")
    st.markdown("### Real-time System Monitoring")
    
    # Backend health check
    is_healthy, health_data = check_backend_health()
    
    # Overall status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if is_healthy:
            st.success("### ✅ CORE ONLINE")
        else:
            st.error("### ❌ CORE OFFLINE")
    
    with col2:
        st.metric("🕒 UPTIME", "Active", delta="Live")
    
    with col3:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.metric("📡 LAST CHECK", timestamp)
    
    st.markdown("---")
    
    # Service Status Grid
    st.markdown("### 🔌 SERVICE STATUS MATRIX")
    
    if is_healthy:
        services = health_data.get("services", {})
        
        service_info = {
            "mysql": {"name": "MySQL Database", "icon": "🗄️", "port": "3307"},
            "mongodb": {"name": "MongoDB NoSQL", "icon": "🍃", "port": "27018"},
            "elasticsearch": {"name": "Elasticsearch", "icon": "🔍", "port": "9201"},
            "neo4j": {"name": "Neo4j Graph DB", "icon": "🕸️", "port": "7475"},
            "redis": {"name": "Redis Cache", "icon": "⚡", "port": "6380"}
        }
        
        cols = st.columns(5)
        
        for idx, (service, status) in enumerate(services.items()):
            info = service_info.get(service, {"name": service.upper(), "icon": "💾", "port": "N/A"})
            
            with cols[idx]:
                status_color = "🟢" if status else "🔴"
                status_text = "ONLINE" if status else "OFFLINE"
                
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #2a3358 0%, #1e2749 100%);
                    border: 3px solid {"#00ff88" if status else "#ff0099"};
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    margin: 5px;
                    box-shadow: 0 0 15px {"rgba(0,255,136,0.3)" if status else "rgba(255,0,153,0.3)"};
                '>
                    <div style='font-size: 2.5rem;'>{info["icon"]}</div>
                    <div style='color: #ffffff; font-weight: bold; margin: 10px 0; font-size: 1.1rem;'>{info["name"]}</div>
                    <div style='color: {"#00ff88" if status else "#ff99cc"}; font-weight: bold; font-size: 1.2rem;'>{status_color} {status_text}</div>
                    <div style='color: #88aaff; font-size: 0.9rem; margin-top: 8px; font-weight: 600;'>Port: {info["port"]}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("⚠️ Cannot retrieve service status - Backend offline")
        st.info("💡 Check if Docker containers are running: `sudo docker-compose ps`")
    
    st.markdown("---")
    
    # System Statistics
    st.markdown("### 📊 SYSTEM STATISTICS")
    
    stats = get_statistics()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        es_stats = stats.get("elasticsearch", {})
        mongo_stats = stats.get("mongodb", {})
        neo4j_stats = stats.get("neo4j", {})
        
        with col1:
            total_es = es_stats.get("total_entities", 0)
            st.metric("🔍 Elasticsearch Docs", f"{total_es:,}")
        
        with col2:
            total_mongo = mongo_stats.get("total_entities", 0)
            st.metric("🍃 MongoDB Docs", f"{total_mongo:,}")
        
        with col3:
            total_nodes = neo4j_stats.get("total_nodes", 0)
            st.metric("🕸️ Neo4j Nodes", f"{total_nodes:,}")
        
        with col4:
            total_rels = neo4j_stats.get("total_relationships", 0)
            st.metric("🔗 Relationships", f"{total_rels:,}")
        
        # Detailed breakdowns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📁 Entity Types")
            by_type = es_stats.get("by_type", {})
            if by_type:
                for entity_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                    st.text(f"  {entity_type}: {count:,}")
            else:
                st.info("No data indexed yet")
        
        with col2:
            st.markdown("#### 📂 Data Sources")
            by_source = es_stats.get("by_source", {})
            if by_source:
                for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
                    st.text(f"  {source}: {count:,}")
            else:
                st.info("No sources imported yet")
    else:
        st.warning("Unable to retrieve statistics")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### 🛠️ QUICK ACTIONS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 View Logs", use_container_width=True):
            st.info("Run: `sudo docker-compose logs -f` in terminal")
    
    with col3:
        if st.button("🔧 Restart Services", use_container_width=True):
            st.warning("Run: `sudo docker-compose restart` in terminal")


def show_relationships():
    """Show relationship explorer"""
    st.header("🕸️ Entity Relationships")
    
    st.info("Enter an entity ID in the format: `type:value` (e.g., `email:user@example.com`)")
    
    entity_id = st.text_input("Entity ID", placeholder="email:user@example.com")
    depth = st.slider("Relationship Depth", min_value=1, max_value=3, value=1)
    
    if st.button("🔍 Explore Relationships") and entity_id:
        with st.spinner("Loading relationships..."):
            result = get_entity_relationships(entity_id, depth)
        
        if result:
            relationships = result.get("relationships", [])
            
            if relationships:
                st.success(f"Found {len(relationships)} relationship paths")
                
                for idx, rel in enumerate(relationships):
                    with st.expander(f"Path {idx + 1}"):
                        nodes = rel.get("nodes", [])
                        rels = rel.get("relationships", [])
                        
                        st.write("**Nodes:**")
                        for node in nodes:
                            st.write(f"- {node.get('entity_type', 'N/A')}: `{node.get('value', 'N/A')}`")
                        
                        st.write("**Relationships:**")
                        for r in rels:
                            st.write(f"- Type: `{r.get('type', 'N/A')}`")
            else:
                st.info("No relationships found")


if __name__ == "__main__":
    main()
