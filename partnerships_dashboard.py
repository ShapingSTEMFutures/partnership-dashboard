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
    .obs-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-top: 4px solid #2d7a5f;
        border-radius: 8px;
        padding: 1.2rem;
        height: 100%;
    }
    .obs-card h4 {
        color: #2d7a5f;
        margin-top: 0;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .obs-card p {
        color: #4b5563;
        font-size: 0.92rem;
        line-height: 1.4;
        margin-bottom: 0;
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

def extract_duration_years(val):
    match = re.search(r'(\d+)', str(val))
    if match:
        return int(match.group(1))
    return 1

if col_duration:
    df["Start Year"] = df[col_duration].apply(extract_year_dynamically)
    df["Tenure_Num"] = df[col_duration].apply(extract_duration_years)
else:
    df["Start Year"] = None
    df["Tenure_Num"] = 1

if df["Start Year"].isna().all():
    df["Start Year"] = pd.Timestamp.now().year

if col_employed:
    df["Employed_Clean"] = pd.to_numeric(df[col_employed], errors="coerce").fillna(0).astype(int)
else:
    df["Employed_Clean"] = 0

# Calculate hiring rate per year per partner
df["Hires_Per_Year"] = df["Employed_Clean"] / df["Tenure_Num"]

# Compare older cohorts vs recent cohorts
avg_hires_recent = df[df["Tenure_Num"] <= 6]["Hires_Per_Year"].mean()
avg_hires_older = df[df["Tenure_Num"] > 6]["Hires_Per_Year"].mean()
pct_increase = ((avg_hires_recent - avg_hires_older) / avg_hires_older) * 100

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

# ─── 5. UPDATED OBSERVATIONS WITH ANNUAL HIRING TREND ─────────────────────────
st.markdown("### Key Partner Network Observations")

top_emp_partner = df.loc[df["Employed_Clean"].idxmax()][col_partner]
top_emp_val = df["Employed_Clean"].max()

top_faculty = df[col_faculty].mode()[0] if col_faculty else "Engineering & Tech"
top_faculty_count = df[df[col_faculty] == top_faculty][col_partner].nunique() if col_faculty else 0

col_obs1, col_obs2, col_obs3 = st.columns(3)

with col_obs1:
    st.markdown(f"""
    <div class="obs-card">
        <h4>📈 Annual Hiring Efficiency Trend</h4>
        <p>Partners hire an average of <b>{df['Hires_Per_Year'].mean():.1f} students per year</b>. Newer partners (established ≤ 6 years) show a <b>▲ {pct_increase:.1f}% increase</b> in annual hiring velocity compared to legacy cohorts.</p>
    </div>
    """, unsafe_allow_html=True)

with col_obs2:
    st.markdown(f"""
    <div class="obs-card">
        <h4>🏆 Top Individual Employer</h4>
        <p><b>{top_emp_partner}</b> represents the single largest enterprise employer, accounting for <b>{top_emp_val:,} Swinburne alumni and student placements</b>.</p>
    </div>
    """, unsafe_allow_html=True)

with col_obs3:
    st.markdown(f"""
    <div class="obs-card">
        <h4>🎓 Faculty Engagement Hub</h4>
        <p><b>{top_faculty}</b> commands the highest density of active industry collaborations, hosting <b>{top_faculty_count} core strategic partners</b>.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── 6. REFINED BAR CHART: LEGEND ON BOTTOM, CUSTOM HOVER, RAW NUMBERS ────────
st.markdown("### Partner Placement Impact & Longevity Rankings")
st.markdown("_Partners are grouped by high-level sector clusters. Long-standing partners (10+ years) are highlighted with ⭐._")

def generalize_sector(sector):
    sec = str(sector).lower()
    if any(k in sec for k in ["tech", "software", "cloud", "ai", "networking", "it"]):
        return "Technology & Digital Services"
    elif any(k in sec for k in ["professional", "accounting", "advisory", "consulting"]):
        return "Business & Professional Services"
    elif any(k in sec for k in ["health", "medical"]):
        return "Health & Medical Research"
    return "Engineering, Innovation & Govt"

df["Sector Cluster"] = df[col_sector].apply(generalize_sector)

# Label formatting
df["Display_Label"] = df.apply(
    lambda r: f"⭐ {r[col_partner]} ({r['Tenure_Num']} yrs)" if r["Tenure_Num"] >= 10 else f"{r[col_partner]} ({r['Tenure_Num']} yrs)",
    axis=1
)

df_sorted = df.sort_values(by="Employed_Clean", ascending=True)

fig_impact = px.bar(
    df_sorted,
    y="Display_Label",
    x="Employed_Clean",
    color="Sector Cluster",
    orientation="h",
    text="Employed_Clean",
    title="Students / Alumni Employed by Partner (Tenure Noted)",
    hover_data={
        col_sector: True,
        "Employed_Clean": True,
        "Display_Label": False,
        "Sector Cluster": False
    },
    labels={
        "Display_Label": "Partner Organization",
        "Employed_Clean": "students employed",
        col_sector: "industry",
        "Sector Cluster": "Industry Domain"
    },
    color_discrete_map={
        "Technology & Digital Services": "#2d7a5f",
        "Business & Professional Services": "#52a384",
        "Health & Medical Research": "#a8d5c2",
        "Engineering, Innovation & Govt": "#1a1a2e"
    }
)

# Show raw integer numbers (e.g., 310)
fig_impact.update_traces(
    textposition="outside",
    texttemplate="%{text}",
    hovertemplate="<b>industry:</b> %{customdata[0]}<br><b>students employed:</b> %{x}<extra></extra>"
)

fig_impact.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font_family="DM Sans",
    title_font_size=16,
    height=580,
    margin=dict(t=40, b=80, l=10, r=60),
    # Moved legend directly to the bottom
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="center",
        x=0.5,
        title=""
    ),
    xaxis=dict(title="Total Students / Alumni Employed", showgrid=True, gridcolor="#f0f0f0"),
    yaxis=dict(title="")
)

st.plotly_chart(fig_impact, use_container_width=True)

st.markdown("---")

# ─── 7. DYNAMIC REGISTRY TABLE ───────────────────────────────────────────────
st.markdown("### Partner Network Registry")

sector_options = ["All"] + list(df[col_sector].dropna().unique())
selected_sector = st.selectbox("Filter by Industry Sector:", sector_options)

if selected_sector != "All":
    filtered_df = df[df[col_sector] == selected_sector]
else:
    filtered_df = df

display_cols = [c for c in df.columns if c not in ["Start Year", "Employed_Clean", "Tenure_Num", "Hires_Per_Year", "Sector Cluster", "Display_Label"]]

st.dataframe(
    filtered_df[display_cols],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.caption("Data: Shaping STEM Futures · Swinburne University of Technology")