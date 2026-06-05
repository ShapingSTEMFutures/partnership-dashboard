import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Shaping STEM Futures – Partnerships Dashboard",
    page_icon="🤝",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600&family=DM+Serif+Display&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'DM Serif Display', serif; }
    .metric-card {
        background: #f0f7f4;
        border-left: 4px solid #2d7a5f;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-card .label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-card .value { font-size: 2.2rem; font-weight: 600; color: #1a1a2e; line-height: 1.1; }
    .placeholder {
        background: #fff8e1;
        border: 1px dashed #d4a017;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        color: #6b5b00;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

EXCEL_FILE = "partnerships_data.xlsx"

st.title("Shaping STEM Futures")
st.markdown("#### Partner Network")
st.markdown("---")

st.markdown('<div class="placeholder">⚠️ <b>Placeholder dashboard.</b> Real partnership data has not been added yet. Replace the sample data in <code>partnerships_data.xlsx</code> to populate this dashboard.</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ─── Load or use sample data ──────────────────────────────────────────────────
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE, sheet_name="Partners")
else:
    df = pd.DataFrame({
        "Year": [2021, 2022, 2023, 2024, 2025],
        "Active Partners": [4, 6, 9, 12, 15],
        "Industry": [2, 3, 5, 7, 9],
        "Academic": [1, 2, 2, 3, 4],
        "Community": [1, 1, 2, 2, 2],
    })

# ─── Metric cards ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="label">Active Partners (Latest)</div><div class="value">{df["Active Partners"].iloc[-1]}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">Industry Partners</div><div class="value">{df["Industry"].iloc[-1]}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">Academic + Community</div><div class="value">{df["Academic"].iloc[-1] + df["Community"].iloc[-1]}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Charts ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    fig_growth = px.line(
        df, x="Year", y="Active Partners",
        markers=True, title="Partnership Growth Over Time"
    )
    fig_growth.update_traces(line_color="#2d7a5f", marker=dict(size=10, color="#2d7a5f"))
    fig_growth.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16, margin=dict(t=80, b=20)
    )
    st.plotly_chart(fig_growth, use_container_width=True)

with col_right:
    df_long = df.melt(id_vars="Year", value_vars=["Industry", "Academic", "Community"],
                       var_name="Type", value_name="Count")
    fig_mix = px.bar(
        df_long, x="Year", y="Count", color="Type",
        title="Partnership Mix by Type",
        color_discrete_map={"Industry": "#2d7a5f", "Academic": "#a8d5c2", "Community": "#d4ead9"}
    )
    fig_mix.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, title=""),
        margin=dict(t=80, b=20)
    )
    st.plotly_chart(fig_mix, use_container_width=True)

# ─── Table ────────────────────────────────────────────────────────────────────
st.markdown("#### Partnership Data")
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")