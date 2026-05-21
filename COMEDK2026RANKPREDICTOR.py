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
# Yields slightly better ranks than 9S1 for the same marks, removing the extreme "hopium" jumps.
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

    if "High Math" in scenario: # Best Case
        bracket_position = base_pos + (1.0 / N)
        raw_val = stats.norm.cdf(bracket_position, loc=0.3, scale=0.2)
        v_min = stats.norm.cdf(0, loc=0.3, scale=0.2)
        v_max = stats.norm.cdf(1, loc=0.3, scale=0.2)
        
    elif "Balanced" in scenario: # Moderate Case
        bracket_position = base_pos + (0.5 / N)
        raw_val = stats.gamma.cdf(bracket_position, a=3, scale=0.2)
        v_min = stats.gamma.cdf(0, a=3, scale=0.2)
        v_max = stats.gamma.cdf(1, a=3, scale=0.2)
        
    else: # Worst Case
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
st.markdown("<p style='text-align: center; color: gray;'>Advanced Rank Projection based on 1.1 Lakh candidate datasets.</p>", unsafe_allow_html=True)
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
    shift_avg = 93.1 if "9S1" in shift else 91.5 # Adjusted 9S2 average to reflect the slight difficulty increase
    deviation = round(marks - shift_avg, 1)
    
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Shift Mean Score", f"{shift_avg}")
    m2.metric("Your Deviation from Mean", f"{deviation:+} Marks", delta=deviation)

    st.markdown("<br>", unsafe_allow_html=True)
    scenario = st.select_slider(
        "Tie-Breaker Edge (Based on Subject Performance):",
        options=["Weak (Low Math)", "Moderate (Balanced)", "Strong (High Math)"],
        value="Moderate (Balanced)",
        help="COMEDK resolves ties using Mathematics score first, then Physics. Higher math scores push you to the top of your rank bracket."
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
st.markdown("<p style='text-align: center; font-size: 12px; color: gray;'>Developed with Statistical Distribution | Advanced statistical tie-breaker modeling enabled</p>", unsafe_allow_html=True)
