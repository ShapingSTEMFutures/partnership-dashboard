import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
import re

st.set_page_config(
    page_title="Shaping STEM Futures – Partner Network",
    page_icon="🤝",
    layout="wide"
)

# ─── Custom CSS Styling ─────────────────────────────────────────────────────
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
    .obs-box {
        background-color: #f8faf8;
        border: 1px solid #d6efd8;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

EXCEL_FILE = "partnerships_data.xlsx"

# ─── 1. SAFE IN-MEMORY FILE LOADING ──────────────────────────────────────────
if not os.path.exists(EXCEL_FILE):
    st.error(f"❌ Could not find '{EXCEL_FILE}'. Please verify the file is placed in your project directory.")
    st.stop()

try:
    with open(EXCEL_FILE, "rb") as f:
        file_bytes = io.BytesIO(f.read())
    df_raw = pd.read_excel(file_bytes)
except PermissionError:
    st.error(f"⚠️ **File Locked:** Please close '{EXCEL_FILE}' in Microsoft Excel and refresh the page.")
    st.stop()

# Dynamically locate header row if there are title banner rows
header_row_idx = None
for i, row in df_raw.iterrows():
    row_values = [str(val) for val in row.values]
    if any("Partner Organization" in val or "Industry Sector" in val for val in row_values):
        header_row_idx = i + 1
        break

if header_row_idx is not None:
    file_bytes.seek(0)
    df = pd.read_excel(file_bytes, skiprows=header_row_idx)
else:
    df = df_raw.copy()

# Dynamically identify key columns
col_partner = next((c for c in df.columns if "Partner" in c and "Organization" in c), df.columns[0])
col_sector = next((c for c in df.columns if "Sector" in c or "Industry" in c), df.columns[1])
col_duration = next((c for c in df.columns if "Duration" in c or "Year" in c), None)
col_employed = next((c for c in df.columns if "Employed" in c or "Students" in c or "Alumni" in c), None)
col_faculty = next((c for c in df.columns if "Faculty" in c or "School" in c), None)

# ─── 2. DYNAMIC DATA CLEANING & PARSING ─────────────────────────────────────
def extract_year_dynamically(val):
    match = re.search(r'\b(19\d{2}|20\d{2})\b', str(val))
    if match:
        return int(match.group(1))
    return None

if col_duration:
    df["Start Year"] = df[col_duration].apply(extract_year_dynamically)
else:
    df["Start Year"] = None

if df["Start Year"].isna().all():
    df["Start Year"] = pd.Timestamp.now().year

if col_employed:
    df["Employed_Clean"] = pd.to_numeric(df[col_employed], errors="coerce").fillna(0).astype(int)
else:
    df["Employed_Clean"] = 0

# ─── HEADER SECTION ──────────────────────────────────────────────────────────
st.title("Shaping STEM Futures")
st.markdown("#### Partner Network Dashboard")
st.markdown("---")

# ─── 3. METRIC CARDS ─────────────────────────────────────────────────────────
total_partners = df[col_partner].nunique()
total_students = df["Employed_Clean"].sum()
unique_sectors = df[col_sector].nunique()
unique_faculties = df[col_faculty].nunique() if col_faculty else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="label">Total Active Partners</div><div class="value">{total_partners}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">Students / Alumni Employed</div><div class="value">{total_students:,}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">Industry Sectors</div><div class="value">{unique_sectors}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="label">Academic Schools Engaged</div><div class="value">{unique_faculties}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 4. CUMULATIVE GROWTH LINE CHART ─────────────────────────────────────────
valid_years = df["Start Year"].dropna()
min_year = int(valid_years.min())
max_year = int(pd.Timestamp.now().year)

years_range = list(range(min_year, max_year + 1))
growth_records = []
for yr in years_range:
    cum_count = len(df[df["Start Year"] <= yr])
    growth_records.append({"Year": yr, "Cumulative Partners": cum_count})

df_growth = pd.DataFrame(growth_records)

fig_growth = px.line(
    df_growth, x="Year", y="Cumulative Partners",
    markers=True, title="Cumulative Partnership Growth Over Time"
)
fig_growth.update_traces(line_color="#2d7a5f", marker=dict(size=8, color="#2d7a5f"))
fig_growth.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font_family="DM Sans", title_font_size=16,
    margin=dict(t=50, b=20),
    xaxis=dict(tickmode='linear', dtick=max(1, len(years_range)//6), tickformat='d')
)
st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")

# ─── 5. KEY DATASET OBSERVATIONS ─────────────────────────────────────────────
st.markdown("### Key Insights & Observations")
st.markdown("""
<div class="obs-box">
<ul>
    <li><b>Top Employment Sector:</b> Professional Services leads student placement volume with <b>400 total alumni employed</b> across major partners (Deloitte & PwC).</li>
    <li><b>Leading Employer:</b> Telecommunications (Telstra) holds the highest single-organization alumni count at <b>310 employees</b>.</li>
    <li><b>Academic Engagement:</b> The <i>School of Science, Computing & Engineering Technologies</i> commands the broadest concentration of technology & cloud partners (AWS, Cisco, Microsoft, Wipro, Capgemini).</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ─── 6. INTERACTIVE INDUSTRY SECTOR CHART ────────────────────────────────────
st.markdown("### Interactive Industry Sector Analysis")

col_metric, col_chart_type = st.columns(2)

with col_metric:
    metric_choice = st.radio(
        "Select Metric to Analyze:",
        options=["Total Students / Alumni Employed", "Partner Count"],
        horizontal=True
    )

with col_chart_type:
    chart_style = st.radio(
        "Select Chart Style:",
        options=["Interactive Donut Chart", "Interactive Horizontal Bar"],
        horizontal=True
    )

# Aggregate sector data dynamically
df_sector_agg = df.groupby(col_sector).agg(
    Partner_Count=(col_partner, "nunique"),
    Total_Employed=("Employed_Clean", "sum")
).reset_index()

val_col = "Total_Employed" if metric_choice == "Total Students / Alumni Employed" else "Partner_Count"
val_label = "Students / Alumni Employed" if metric_choice == "Total Students / Alumni Employed" else "Active Partners"

if chart_style == "Interactive Donut Chart":
    fig_sector_interactive = px.pie(
        df_sector_agg,
        names=col_sector,
        values=val_col,
        hole=0.4,
        color_discrete_sequence=["#2d7a5f", "#a8d5c2", "#52a384", "#1a1a2e", "#84bfa4"],
        title=f"Industry Sector Share ({metric_choice})"
    )
    fig_sector_interactive.update_traces(textinfo="percent+label")
    fig_sector_interactive.update_layout(
        font_family="DM Sans", title_font_size=16, margin=dict(t=50, b=20)
    )
else:
    df_sector_agg = df_sector_agg.sort_values(by=val_col, ascending=True)
    fig_sector_interactive = px.bar(
        df_sector_agg,
        y=col_sector,
        x=val_col,
        orientation="h",
        text=val_col,
        color=val_col,
        color_continuous_scale=["#a8d5c2", "#2d7a5f"],
        title=f"Industry Sectors Ranked by {val_label}"
    )
    fig_sector_interactive.update_traces(textposition="outside")
    fig_sector_interactive.update_layout(
        showlegend=False, coloraxis_showscale=False,
        plot_bgcolor="white", paper_bgcolor="white",
        font_family="DM Sans", title_font_size=16,
        margin=dict(t=50, b=20),
        xaxis=dict(title=val_label),
        yaxis=dict(title="")
    )

st.plotly_chart(fig_sector_interactive, use_container_width=True)

st.markdown("---")

# ─── 7. DYNAMIC REGISTRY TABLE ───────────────────────────────────────────────
st.markdown("### Partner Network Registry")

sector_options = ["All"] + list(df[col_sector].dropna().unique())
selected_sector = st.selectbox("Filter by Industry Sector:", sector_options)

if selected_sector != "All":
    filtered_df = df[df[col_sector] == selected_sector]
else:
    filtered_df = df

display_cols = [c for c in df.columns if c not in ["Start Year", "Employed_Clean"]]

st.dataframe(
    filtered_df[display_cols],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")