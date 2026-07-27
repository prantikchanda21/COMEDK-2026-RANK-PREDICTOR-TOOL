import streamlit as st
import numpy as np
import scipy.stats as stats

# --- Configure the page for a modern look ---
st.set_page_config(
    page_title="COMEDK 2026 Predictor", 
    page_icon="🚀", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ROBUST CUSTOM CSS FOR NEON RGB FLICKERING GRID ---
cyberpunk_bg = """
<div class="neon-grid-bg"></div>

<style>
    /* 1. Force Streamlit's default backgrounds to be fully transparent */
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"], 
    .stApp {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* 2. Create the fixed background layer */
    .neon-grid-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -9999; /* Keeps it behind all app elements */
        background-color: #020202; /* Deep black base */
        
        /* The Grid */
        background-image: 
            linear-gradient(transparent 95%, rgba(0, 255, 255, 0.9) 95%),
            linear-gradient(90deg, transparent 95%, rgba(0, 255, 255, 0.9) 95%);
        background-size: 50px 50px;
        
        /* Apply animations: Movement, RGB Color Shift, and Flickering */
        animation: 
            moveGrid 3s linear infinite, 
            rgbShift 8s linear infinite, 
            flicker 4s infinite;
    }

    /* 3. Animation Keyframes */
    
    /* Moves the grid diagonally forever */
    @keyframes moveGrid {
        0% { background-position: 0 0; }
        100% { background-position: 50px 50px; }
    }

    /* Cycles through the RGB spectrum */
    @keyframes rgbShift {
        0%   { filter: hue-rotate(0deg) drop-shadow(0 0 10px cyan); }
        33%  { filter: hue-rotate(120deg) drop-shadow(0 0 10px magenta); }
        66%  { filter: hue-rotate(240deg) drop-shadow(0 0 10px yellow); }
        100% { filter: hue-rotate(360deg) drop-shadow(0 0 10px cyan); }
    }

    /* Creates a random-looking electrical flicker */
    @keyframes flicker {
        0%, 100% { opacity: 1; }
        10%, 12% { opacity: 0.8; }
        13%, 49% { opacity: 1; }
        50%, 52% { opacity: 0.4; }
        53%, 79% { opacity: 1; }
        80%      { opacity: 0.6; }
        81%      { opacity: 1; }
    }

    /* 4. Style the Streamlit containers so they are readable over the wild background */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 10, 10, 0.85) !important; /* Dark glassy look */
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px;
        box-shadow: 0px 0px 20px rgba(0, 255, 255, 0.1);
    }
    
    /* Ensure all text stays bright white for contrast */
    h1, h2, h3, p, label, .st-emotion-cache-10trblm {
        color: #ffffff !important;
        text-shadow: 0 0 4px rgba(255,255,255,0.4);
    }
    
    /* Style the main button */
    button[kind="primary"] {
        background: linear-gradient(90deg, #ff00ff, #00ffff) !important;
        border: none !important;
        color: white !important;
        font-weight: bold;
        transition: transform 0.2s;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
    }
</style>
"""
st.markdown(cyberpunk_bg, unsafe_allow_html=True)

# --- Data Dictionaries from Projected Tables ---
table_9s1 = {
    (130, 180): (1, 150),  
    (120, 129): (150, 750),
    (110, 119): (750, 2500),
    (100, 109): (2500, 4500),
    (90, 99): (4500, 9500),
    (80, 89): (9500, 14000),
    (70, 79): (14000, 22000),
    (60, 69): (22000, 37000),
    (50, 59): (37000, 57000)
}

# PRECISE RECALIBRATION: 9S2 is "Slightly Tougher" than 9S1. 
table_9s2 = {
    (130, 180): (1, 120),
    (120, 129): (120, 650),
    (110, 119): (650, 2200),
    (100, 109): (2200, 4200),
    (90, 99): (4200, 8800),
    (80, 89): (8800, 13000),
    (70, 79): (13000, 20000),
    (60, 69): (20000, 34000),
    (50, 59): (34000, 54000)
}

# --- Core Logic ---
def get_base_rank_bounds(marks, shift):
    active_table = table_9s1 if "9S1" in shift else table_9s2
    for (min_m, max_m), (min_r, max_r) in active_table.items():
        if min_m <= marks <= max_m:
            return min_r, max_r, min_m, max_m
            
    # Adjusted fallback for lower scores
    return 57000, 110000, 0, 49

def calculate_projected_rank(marks, shift, scenario):
    if marks == 180:
        return 1

    min_r, max_r, min_m, max_m = get_base_rank_bounds(marks, shift)
    N = (max_m - min_m) + 1 
    base_pos = (marks - min_m) / N 

    if "High Math" in scenario: 
        bracket_position = base_pos + (1.0 / N)
        raw_val = stats.norm.cdf(bracket_position, loc=0.3, scale=0.2)
        v_min = stats.norm.cdf(0, loc=0.3, scale=0.2)
        v_max = stats.norm.cdf(1, loc=0.3, scale=0.2)
        
    elif "Balanced" in scenario: 
        bracket_position = base_pos + (0.5 / N)
        raw_val = stats.gamma.cdf(bracket_position, a=3, scale=0.2)
        v_min = stats.gamma.cdf(0, a=3, scale=0.2)
        v_max = stats.gamma.cdf(1, a=3, scale=0.2)
        
    else: 
        bracket_position = base_pos
        raw_val = stats.laplace.cdf(bracket_position, loc=0.7, scale=0.15)
        v_min = stats.laplace.cdf(0, loc=0.7, scale=0.15)
        v_max = stats.laplace.cdf(1, loc=0.7, scale=0.15)

    weight = (raw_val - v_min) / (v_max - v_min)
    rank_span = max_r - min_r
    projected = max_r - (weight * rank_span)

    return max(min_r, min(max_r, int(projected)))

# --- UI Setup ---
st.markdown("<h1 style='text-align: center;'>🚀 COMEDK 2026 Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Advanced Rank Projection based on 1.1 Lakh candidate datasets.</p>", unsafe_allow_html=True)
st.divider()

# --- Input Module ---
with st.container(border=True):
    st.markdown("### ⚙️ Telemetry Input")
    col1, col2 = st.columns(2)

    with col1:
        shift = st.selectbox("Exam Shift Array:", ["9S1 (9 May Morning)", "9S2 (9 May Evening)"])

    with col2:
        marks = st.number_input(f"Raw Score (Max 180):", min_value=0, max_value=180, value=90, step=1)
    
    # Mathematical contribution logic
    shift_avg = 93.1 if "9S1" in shift else 91.5 
    deviation = round(marks - shift_avg, 1)
    
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Shift Mean Score", f"{shift_avg}")
    m2.metric("Your Deviation from Mean", f"{deviation:+} Marks", delta=deviation)

    st.markdown("<br>", unsafe_allow_html=True)
    scenario = st.select_slider(
        "CASE METER:",
        options=["WORST CASE", "NORMAL CASE", "BEST CASE"],
        value="NORMAL CASE"
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- Processing & Output Module ---
if st.button("Initialize Prediction ⚡", type="primary", use_container_width=True):
    estimated_rank = calculate_projected_rank(marks, shift, scenario)
    min_r, max_r, _, _ = get_base_rank_bounds(marks, shift)
    
    # Calculate Percentile based on 110,000 candidates
    total_candidates = 110000
    estimated_percentile = round(((total_candidates - estimated_rank) / total_candidates) * 100, 3)
    
    with st.container(border=True):
        st.markdown("### 📊 Projection Results")
        
        r1, r2 = st.columns(2)
        r1.metric(label="Predicted Rank", value=f"{estimated_rank:,}")
        r2.metric(label="Projected Percentile", value=f"{estimated_percentile}%")
        
        st.markdown("---")
        if marks == 180:
            st.info("🎯 **Target Acquired:** Absolute Maximum Bracket Reached.")
        else:
            st.info(f"📍 **Bracket Constraint:** The algorithm bounds this score strictly between Rank **{min_r:,}** and **{max_r:,}**.")
            
        if "9S2" in shift:
            st.caption("⚖️ *Note: 9S2 brackets are normalized to reflect a slightly higher exam difficulty compared to 9S1.*")

st.divider()
st.markdown("<p style='text-align: center; font-size: 12px;'>Developed with Statistical Distribution | Advanced statistical tie-breaker modeling enabled</p>", unsafe_allow_html=True)
