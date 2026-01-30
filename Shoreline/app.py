import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import linregress
from statsmodels.tsa.seasonal import seasonal_decompose

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Global Shoreline Intelligence System", layout="centered")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
h1, h2, h3 { color: #e0f7fa; }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Global Shoreline Intelligence System")
st.caption("Research-grade shoreline change analytics for global coastal datasets")

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload Shoreline & Tide Data (Excel)", type=["xlsx"])

if not uploaded_file:
    st.warning("Please upload an Excel file to begin analysis.")
    st.stop()

df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()

required_cols = ["Date", "Beach", "Shoreline_Position", "Tide_Level"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# ---------------- CLEANING ----------------
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Shoreline_Position"] = pd.to_numeric(df["Shoreline_Position"], errors="coerce")
df["Tide_Level"] = pd.to_numeric(df["Tide_Level"], errors="coerce")
df = df.dropna(subset=required_cols)

if df.empty:
    st.error("No valid data after cleaning.")
    st.stop()

# ---------------- BEACH SELECTION ----------------
mode = st.radio("Analysis Mode", ["Single Beach (Detailed)", "Multiple Beaches (Comparison)"])

beaches = sorted(df["Beach"].unique())

if mode == "Single Beach (Detailed)":
    selected_beaches = [st.selectbox("Select Beach", beaches)]
else:
    selected_beaches = st.multiselect("Select Beaches", beaches, default=beaches[:1])

threshold = st.number_input("Projection Threshold (m retreat)", value=-10.0)

results = []

# ---------------- PROCESS ----------------
for beach in selected_beaches:

    beach_df = df[df["Beach"] == beach].sort_values("Date")
    if len(beach_df) < 3:
        continue

    beach_df["Normalized_Shoreline"] = beach_df["Shoreline_Position"] - beach_df["Tide_Level"]

    t_years = (beach_df["Date"] - beach_df["Date"].min()).dt.days / 365.25

    slope, intercept, r, p, stderr = linregress(t_years, beach_df["Normalized_Shoreline"])
    rate = slope
    r2 = r ** 2

    net_change = beach_df["Normalized_Shoreline"].iloc[-1] - beach_df["Normalized_Shoreline"].iloc[0]

    # ---------------- CLASSIFICATION ----------------
    if net_change < -1:
        trend = "Severe Erosion"
    elif -1 <= net_change < -0.5:
        trend = "Moderate Erosion"
    elif -0.5 <= net_change <= 0.1:
        trend = "Stable Shoreline"
    elif 0.1 < net_change <= 0.5:
        trend = "Moderate Accretion"
    else:
        trend = "Strong Accretion"

    # ---------------- EARLY WARNING ----------------
    diffs = beach_df["Normalized_Shoreline"].diff().dropna()
    early_warning = bool((rate < 0) and ((diffs < 0).mean() >= 0.6))

    # ---------------- DATA QUALITY (FIXED) ----------------
    missing_pct = beach_df.isna().mean().mean()
    data_quality = round(100 - missing_pct * 100, 1)

    # ---------------- RISK INDEX ----------------
    variability = beach_df["Normalized_Shoreline"].std()
    consistency = (diffs < 0).mean()

    risk_index = min(100, round(
        abs(rate) * 30 +
        (1 - r2) * 20 +
        variability * 10 +
        consistency * 40
    , 1))

    # ---------------- PROJECTION ----------------
    years_to_threshold = abs(threshold / rate) if rate < 0 else np.nan

    results.append({
        "Beach": beach,
        "Net Change (m)": round(net_change, 2),
        "Rate (m/year)": round(rate, 3),
        "R²": round(r2, 2),
        "Trend": trend,
        "Risk Index": risk_index,
        "Early Warning": "Yes" if early_warning else "No",
        "Data Quality (%)": data_quality,
        "Years to Threshold": round(years_to_threshold, 1) if rate < 0 else "N/A"
    })

    # ---------------- DETAILED VISUALS ----------------
    if mode == "Single Beach (Detailed)":

        st.subheader(f"📈 {beach} Shoreline Trend")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(beach_df["Date"], beach_df["Normalized_Shoreline"], marker="o", label="Observed")

        trend_line = intercept + slope * t_years
        ax.plot(beach_df["Date"], trend_line, "--", label="Trend")

        ax.fill_between(
            beach_df["Date"],
            trend_line - stderr,
            trend_line + stderr,
            alpha=0.2,
            label="Confidence Band"
        )

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%Y"))
        plt.xticks(rotation=45, ha="right")

        ax.set_ylabel("Normalized Shoreline (m)")
        ax.set_xlabel("Date")
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        st.pyplot(fig)

        # ---------------- SEASONALITY ----------------
        if len(beach_df) >= 12:
            st.subheader("🌦 Seasonal Decomposition")
            decomp = seasonal_decompose(
                beach_df.set_index("Date")["Normalized_Shoreline"],
                model="additive",
                period=12
            )
            st.line_chart(decomp.trend)

# ---------------- SUMMARY ----------------
summary_df = pd.DataFrame(results)
st.subheader("📊 Shoreline Change Summary")
st.dataframe(summary_df, use_container_width=True)

st.download_button(
    "📥 Download Summary (CSV)",
    summary_df.to_csv(index=False),
    "shoreline_summary.csv"
)

# ---------------- INTERPRETATION ----------------
st.subheader("🤖 AI-Assisted Interpretation")

for _, row in summary_df.iterrows():
    if row["Risk Index"] > 70:
        st.error(f"{row['Beach']}: High erosion risk. Immediate monitoring advised.")
    elif row["Risk Index"] > 40:
        st.warning(f"{row['Beach']}: Moderate erosion trend detected.")
    else:
        st.success(f"{row['Beach']}: Currently stable under observed conditions.")

# ---------------- REFERENCE TABLE ----------------
st.subheader("📋 Classification Reference")

st.table(pd.DataFrame({
    "Net Change (m)": ["< -1", "-1 to -0.5", "-0.5 to 0.1", "0.1 to 0.5", "> 0.5"],
    "Classification": [
        "Severe Erosion",
        "Moderate Erosion",
        "Stable",
        "Moderate Accretion",
        "Strong Accretion"
    ]
}))

# ---------------- METHODOLOGY ----------------
with st.expander("📘 Methodology & Limitations"):
    st.markdown("""
- Shoreline normalized using linear tidal subtraction  
- Trend estimated via ordinary least squares regression  
- Risk index combines rate, confidence, variability & consistency  
- Seasonal decomposition assumes regular temporal spacing  
- Projections assume no regime shift or extreme events  
- Tool supports *decision guidance*, not deterministic prediction
""")
