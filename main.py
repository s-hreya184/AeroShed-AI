import streamlit as st
import os

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="AeroZen Aviation Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE
# ============================================================================
if 'selected_module' not in st.session_state:
    st.session_state.selected_module = None

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e1a 0%, #1a1d2e 50%, #2d1b4e 100%);
    }
    
    .main {
        background-color: transparent;
        color: #ffffff;
        padding-top: 1rem !important;
    }
    
    h1, h2, h3, h4, p, label, span, div {
        color: white !important;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6);
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #1a1d2e 100%);
    }
    
    .module-card {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(59, 130, 246, 0.04) 100%);
        padding: 1.75rem;
        border-radius: 12px;
        border: 1px solid rgba(37, 99, 235, 0.25);
        transition: all 0.3s ease;
        height: 100%;
        backdrop-filter: blur(10px);
    }
    
    .module-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.25);
        border: 1px solid rgba(37, 99, 235, 0.5);
    }
    
    .feature-badge {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%);
        padding: 0.3rem 0.85rem;
        border-radius: 12px;
        font-size: 0.75rem;
        display: inline-block;
        margin: 0.3rem 0.3rem 0.3rem 0;
        border: 1px solid rgba(37, 99, 235, 0.3);
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    
    .hero-section {
        text-align: center;
        padding: 2.5rem 0 0.5rem 0;
        background: linear-gradient(180deg, rgba(37, 99, 235, 0.08) 0%, transparent 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.12) 0%, rgba(59, 130, 246, 0.06) 100%);
        padding: 1.2rem 1.75rem;
        border-radius: 10px;
        border-left: 4px solid #2563eb;
        margin: 1.25rem 0;
        backdrop-filter: blur(10px);
    }
    
    .tech-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.25rem;
        margin: 1.5rem 0;
    }
    
    .tech-item {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .tech-item:hover {
        border-color: rgba(37, 99, 235, 0.4);
        transform: translateY(-2px);
    }
    
    .streamlit-expanderHeader {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    hr {
        margin: 2rem 0 !important;
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    
    .feature-section {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, transparent 100%);
        padding: 1.25rem;
        border-radius: 10px;
        border-left: 3px solid;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HERO SECTION
# ============================================================================
st.markdown("""
<div class='hero-section'>
    <h1 style='font-size: 2.75rem; margin-bottom: 0.5rem; font-weight: 700; letter-spacing: -0.02em;'>
        AeroZen
    </h1>
    <p style='font-size: 1.15rem; color: #94a3b8; margin: 0; font-weight: 400; letter-spacing: 0.01em;'>
        Integrated Aviation Management Platform
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# WELCOME MESSAGE
# ============================================================================
st.markdown("""
<div class='info-box'>
    <p style='color: #cbd5e1; margin: 0; line-height: 1.7; font-size: 0.95rem;'>
        <strong style='color: #ffffff;'>Platform Overview:</strong> Transform aviation operations through AI-powered risk prediction, 
        intelligent crew scheduling, and real-time optimization. Built with enterprise-grade machine learning and optimization algorithms.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MODULE CARDS
# ============================================================================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <div class='module-card'>
        <h3 style='color: #60a5fa; margin: 0 0 0.85rem 0; font-size: 1.35rem; font-weight: 600;'>
            Risk Predictions & AI Copilot
        </h3>
        <p style='color: #94a3b8; font-size: 0.92rem; margin: 0 0 1.25rem 0; line-height: 1.6;'>
            Advanced machine learning models for comprehensive aviation risk assessment with integrated AI assistant for intelligent decision support and analysis.
        </p>
        <div style='margin: 1rem 0 0 0;'>
            <span class='feature-badge'>Weather Delay Analysis</span>
            <span class='feature-badge'>Crew Health Monitoring</span>
            <span class='feature-badge'>Equipment Failure Prediction</span>
            <span class='feature-badge'>Emergency Risk Assessment</span>
            <span class='feature-badge'>AI-Powered Copilot</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Navigate to Risk Predictions module via sidebar")

with col2:
    st.markdown("""
    <div class='module-card'>
        <h3 style='color: #4ade80; margin: 0 0 0.85rem 0; font-size: 1.35rem; font-weight: 600;'>
            Crew Schedule Optimizer
        </h3>
        <p style='color: #94a3b8; font-size: 0.92rem; margin: 0 0 1.25rem 0; line-height: 1.6;'>
            Google OR-Tools powered optimization engine for intelligent crew allocation, ensuring regulatory compliance and maximizing operational efficiency.
        </p>
        <div style='margin: 1rem 0 0 0;'>
            <span class='feature-badge'>OR-Tools CP-SAT Solver</span>
            <span class='feature-badge'>Constraint Management</span>
            <span class='feature-badge'>Regulatory Compliance</span>
            <span class='feature-badge'>Visual Analytics</span>
            <span class='feature-badge'>Resource Optimization</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Navigate to Schedule Optimizer module via sidebar")

# ============================================================================
# TECHNOLOGY STACK
# ============================================================================
st.markdown("---")

st.markdown("<h3 style='text-align: center; color: #e2e8f0; margin: 1.5rem 0; font-size: 1.5rem; font-weight: 600;'>Technology Stack</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class='tech-item'>
        <strong style='color: #60a5fa; font-size: 1.1rem; display: block; margin-bottom: 0.75rem;'>Artificial Intelligence</strong>
        <p style='font-size: 0.85rem; color: #94a3b8; margin: 0; line-height: 1.6;'>
            Scikit-learn ML Framework<br>
            Phi-3 Language Model<br>
            Ollama Runtime
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='tech-item'>
        <strong style='color: #4ade80; font-size: 1.1rem; display: block; margin-bottom: 0.75rem;'>Optimization Engine</strong>
        <p style='font-size: 0.85rem; color: #94a3b8; margin: 0; line-height: 1.6;'>
            Google OR-Tools<br>
            CP-SAT Constraint Solver<br>
            Linear Programming
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='tech-item'>
        <strong style='color: #a78bfa; font-size: 1.1rem; display: block; margin-bottom: 0.75rem;'>Data Visualization</strong>
        <p style='font-size: 0.85rem; color: #94a3b8; margin: 0; line-height: 1.6;'>
            Plotly Interactive Charts<br>
            Streamlit Framework<br>
            Python Analytics
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# KEY CAPABILITIES
# ============================================================================
st.markdown("---")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <div class='feature-section' style='border-color: #60a5fa;'>
        <h4 style='margin: 0 0 0.75rem 0; color: #60a5fa; font-weight: 600; font-size: 1.1rem;'>
            Risk Intelligence Platform
        </h4>
        <ul style='color: #cbd5e1; font-size: 0.9rem; margin: 0; padding-left: 1.3rem; line-height: 1.9;'>
            <li>Real-time risk scoring and predictive analytics</li>
            <li>Multi-dimensional analysis across weather, crew, and equipment factors</li>
            <li>AI-powered decision support with natural language interaction</li>
            <li>Historical trend analysis and pattern recognition</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='feature-section' style='border-color: #4ade80;'>
        <h4 style='margin: 0 0 0.75rem 0; color: #4ade80; font-weight: 600; font-size: 1.1rem;'>
            Intelligent Optimization
        </h4>
        <ul style='color: #cbd5e1; font-size: 0.9rem; margin: 0; padding-left: 1.3rem; line-height: 1.9;'>
            <li>Automated crew scheduling with constraint satisfaction</li>
            <li>Regulatory compliance enforcement and validation</li>
            <li>Resource utilization maximization and efficiency gains</li>
            <li>Dynamic adjustment capabilities for operational changes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# QUICK START
# ============================================================================
st.markdown("---")

with st.expander("Quick Start Guide", expanded=False):
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        **Risk Predictions Module:**
        
        1. Select your desired prediction model from the sidebar options
        2. Input relevant flight and operational parameters
        3. Execute prediction analysis with a single click
        4. Review comprehensive AI-generated insights and recommendations
        5. Interact with the Phi-3 Copilot for deeper analysis and questions
        """)
    
    with col2:
        st.markdown("""
        **Schedule Optimizer Module:**
        
        1. Configure operational constraints through the sidebar interface
        2. Define duty hour limits and mandatory rest period requirements
        3. Generate optimized schedules using the CP-SAT solver
        4. Analyze results through interactive Gantt charts and metrics
        5. Export schedules or make real-time adjustments as needed
        """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1.25rem 0;'>
    <p style='margin: 0; font-size: 0.95rem; font-weight: 500;'>
        <span style='color: #94a3b8;'>AeroZen Platform</span> <span style='color: #475569;'>v2.0</span>
    </p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #475569;'>
        Powered by Machine Learning, Optimization Algorithms & Artificial Intelligence
    </p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #334155;'>
        Built for Microsoft Imagine Cup 2026
    </p>
</div>
""", unsafe_allow_html=True)