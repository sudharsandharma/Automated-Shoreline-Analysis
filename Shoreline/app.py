import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------- CUSTOM BACKGROUND ----------
st.markdown(
    """
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: white;
    }

    /* Titles */
    h1, h2, h3, h4 {
        color: #e0f7fa;
    }

    /* File uploader box */
    section[data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px;
        color: white;
    }

    /* Select boxes */
    div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Automated Shoreline Analysis",
    layout="centered"
)

st.title("🌊 Automated Shoreline Analysis")
st.caption("Multi-beach shoreline change analysis with tidal correction")

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader(
    "Upload Shoreline & Tide Data (Excel)",
    type=["xlsx"]
)

if uploaded_file:

    # Read Excel
    df = pd.read_excel(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip()

    required_cols = ["Date", "Beach", "Shoreline_Position", "Tide_Level"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # Type conversion
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Shoreline_Position"] = pd.to_numeric(df["Shoreline_Position"], errors="coerce")
    df["Tide_Level"] = pd.to_numeric(df["Tide_Level"], errors="coerce")

    df = df.dropna(subset=required_cols)

    if df.empty:
        st.error("No valid data after cleaning.")
        st.stop()

    # ------------------ BEACH SELECTION ------------------
    selected_beach = st.selectbox(
        "Select Beach",
        sorted(df["Beach"].unique())
    )

    beach_df = df[df["Beach"] == selected_beach].sort_values("Date")

    if len(beach_df) < 2:
        st.warning("Not enough temporal data for shoreline change analysis.")
        st.stop()

    # ------------------ TIDAL NORMALIZATION ------------------
    beach_df["Normalized_Shoreline"] = (
        beach_df["Shoreline_Position"] - beach_df["Tide_Level"]
    )

    # ------------------ VISUALIZATION ------------------
    st.subheader("📈 Shoreline Change Over Time")

    fig, ax = plt.subplots()
    ax.plot(
        beach_df["Date"],
        beach_df["Normalized_Shoreline"],
        marker="o",
        linewidth=2
    )
    ax.set_xlabel("Time")
    ax.set_ylabel("Normalized Shoreline Position (m)")
    ax.set_title(f"{selected_beach} – Temporal Shoreline Variability")
    ax.grid(True)

    st.pyplot(fig)

    # ------------------ NET CHANGE ------------------
    net_change = (
        beach_df["Normalized_Shoreline"].iloc[-1]
        - beach_df["Normalized_Shoreline"].iloc[0]
    )

    st.subheader("📊 Automated Change Statistics")

    if net_change < 0:
        st.error("⚠ Net shoreline retreat detected (Erosion)")
    else:
        st.success("✅ Net shoreline advancement detected (Accretion)")

    st.metric("Net Shoreline Change (m)", round(net_change, 2))

    # ------------------ EARLY WARNING INDICATOR ------------------
    early_warning = False

    if net_change < 0 and net_change > -1.0:
        diffs = beach_df["Normalized_Shoreline"].diff().dropna()

        if len(diffs) > 0 and (diffs < 0).sum() >= len(diffs) * 0.6:
            early_warning = True

    if early_warning:
        st.warning(
            "⚠ Early Warning: Consistent shoreline retreat detected. "
            "This beach may face increased erosion risk in the near future."
        )

    # ------------------ AI-STYLE INTERPRETATION ------------------
    st.subheader("🤖 AI-Assisted Interpretation")

    if net_change < 0:
        st.info(
            "The tidally normalized shoreline shows a landward shift over time, "
            "indicating erosion. Continued monitoring and mitigation strategies "
            "are recommended."
        )
    else:
        st.info(
            "The shoreline shows stability or seaward advancement, suggesting "
            "lower erosion risk under current conditions."
        )

    # ------------------ CONSTANT REFERENCE TABLE ------------------
    st.subheader("📋 Shoreline Change Classification Reference")

    reference_df = pd.DataFrame({
        "Net Shoreline Change (m)": [
            "< -1.0",
            "-1.0 to -0.5",
            "-0.5 to -0.1",
            "-0.1 to +0.1",
            "+0.1 to +0.5",
            "+0.5 to +1.0",
            "> +1.0"
        ],
        "Classification": [
            "Severe Erosion",
            "Moderate Erosion",
            "Mild Erosion",
            "Stable",
            "Mild Accretion",
            "Moderate Accretion",
            "Strong Accretion"
        ],
        "Interpretation": [
            "High shoreline retreat",
            "Significant erosion",
            "Low erosion",
            "No significant change",
            "Slight land gain",
            "Noticeable land gain",
            "High shoreline advancement"
        ]
    })

    st.table(reference_df)

else:
    st.warning("Please upload an Excel file to begin analysis.")






