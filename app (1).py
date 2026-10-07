pip install streamlit pandas numpy openpyxl plotly
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Special Clinic Monitoring Dashboard",
    page_icon="🏥",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🏥 Special Clinic Monitoring Dashboard")

st.markdown(
    """
    **Wananchi Hospital — 2025 Special Clinic Visits**
    
    Monitor monthly attendance, new patients, revisits,
    clinic performance and data quality.
    """
)


# ============================================================
# DATA LOADING FUNCTION
# ============================================================

@st.cache_data
def load_data(file):

    # Read Excel workbook
    excel_file = pd.ExcelFile(file)

    all_data = []

    # Read every monthly sheet
    for sheet in excel_file.sheet_names:

        df = pd.read_excel(
            excel_file,
            sheet_name=sheet
        )

        # Clean column names
        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # Expected columns
        required_columns = [
            "SPECIAL CLINICS",
            "NEW",
            "REVISIT",
            "TOTAL"
        ]

        # Check columns
        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:
            continue

        # Keep required columns
        df = df[required_columns].copy()

        # Add month
        df["MONTH"] = str(sheet).strip().upper()

        # Add source sheet
        df["SOURCE_SHEET"] = sheet

        all_data.append(df)

    # Combine all sheets
    data = pd.concat(
        all_data,
        ignore_index=True
    )

    # --------------------------------------------------------
    # CLEAN CLINIC NAMES
    # --------------------------------------------------------

    data["SPECIAL CLINICS"] = (
        data["SPECIAL CLINICS"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # --------------------------------------------------------
    # CONVERT NUMERIC COLUMNS
    # --------------------------------------------------------

    for column in ["NEW", "REVISIT", "TOTAL"]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # CALCULATED TOTAL
    # --------------------------------------------------------

    data["CALCULATED_TOTAL"] = (
        data["NEW"].fillna(0)
        +
        data["REVISIT"].fillna(0)
    )

    # --------------------------------------------------------
    # CHECK TOTAL
    # --------------------------------------------------------

    data["TOTAL_DIFFERENCE"] = (
        data["TOTAL"]
        -
        data["CALCULATED_TOTAL"]
    )

    data["TOTAL_CHECK"] = np.where(
        data["TOTAL_DIFFERENCE"].abs() > 0.001,
        "CHECK",
        "OK"
    )

    # --------------------------------------------------------
    # ANALYSIS TOTAL
    # --------------------------------------------------------
    # We use NEW + REVISIT for analysis because some records
    # have discrepancies between TOTAL and NEW + REVISIT.

    data["ANALYSIS_TOTAL"] = (
        data["CALCULATED_TOTAL"]
    )

    # --------------------------------------------------------
    # MONTH ORDER
    # --------------------------------------------------------

    month_order = [
        "JANUARY",
        "FEBRUARY",
        "MARCH",
        "APRIL",
        "MAY",
        "JUNE",
        "JULY",
        "AUGUST",
        "SEPTEMBER",
        "OCTOBER",
        "NOVEMBER",
        "DECEMBER"
    ]

    data["MONTH"] = pd.Categorical(
        data["MONTH"],
        categories=month_order,
        ordered=True
    )

    # Month number
    data["MONTH_NUMBER"] = (
        data["MONTH"].cat.codes + 1
    )

    return data


# ============================================================
# UPLOAD EXCEL FILE
# ============================================================

st.sidebar.header("📂 Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload Special Clinic Excel file",
    type=["xlsx", "xls"]
)


# ============================================================
# LOAD DATA
# ============================================================

if uploaded_file is None:

    st.info(
        "Please upload the 2025 Special Clinic Excel workbook "
        "using the sidebar."
    )

    st.stop()


data = load_data(uploaded_file)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Filters")


# ------------------------------------------------------------
# MONTH FILTER
# ------------------------------------------------------------

available_months = [
    month
    for month in data["MONTH"].cat.categories
    if month in data["MONTH"].astype(str).unique()
]

selected_months = st.sidebar.multiselect(
    "Select month(s)",
    available_months,
    default=available_months
)


# ------------------------------------------------------------
# CLINIC FILTER
# ------------------------------------------------------------

available_clinics = sorted(
    data["SPECIAL CLINICS"]
    .dropna()
    .unique()
)

selected_clinics = st.sidebar.multiselect(
    "Select special clinic(s)",
    available_clinics,
    default=available_clinics
)


# ------------------------------------------------------------
# PATIENT TYPE
# ------------------------------------------------------------

patient_type = st.sidebar.selectbox(
    "Patient type",
    [
        "All Visits",
        "New",
        "Revisit"
    ]
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_data = data[
    data["MONTH"].astype(str).isin(
        selected_months
    )
    &
    data["SPECIAL CLINICS"].isin(
        selected_clinics
    )
].copy()


# ============================================================
# SELECT DISPLAY TOTAL
# ============================================================

if patient_type == "New":

    filtered_data["DISPLAY_TOTAL"] = (
        filtered_data["NEW"]
    )

elif patient_type == "Revisit":

    filtered_data["DISPLAY_TOTAL"] = (
        filtered_data["REVISIT"]
    )

else:

    filtered_data["DISPLAY_TOTAL"] = (
        filtered_data["ANALYSIS_TOTAL"]
    )


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_visits = (
    filtered_data["DISPLAY_TOTAL"]
    .sum()
)

new_visits = (
    filtered_data["NEW"]
    .sum()
)

revisit_visits = (
    filtered_data["REVISIT"]
    .sum()
)

number_of_clinics = (
    filtered_data["SPECIAL CLINICS"]
    .nunique()
)

number_of_months = (
    filtered_data["MONTH"]
    .nunique()
)

monthly_totals = (
    filtered_data
    .groupby(
        "MONTH",
        observed=True
    )["DISPLAY_TOTAL"]
    .sum()
)

if len(monthly_totals) > 0:

    average_monthly = (
        monthly_totals.mean()
    )

else:

    average_monthly = 0


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Total Visits",
        f"{total_visits:,.0f}"
    )


with col2:

    st.metric(
        "New Visits",
        f"{new_visits:,.0f}"
    )


with col3:

    st.metric(
        "Revisits",
        f"{revisit_visits:,.0f}"
    )


with col4:

    st.metric(
        "Special Clinics",
        f"{number_of_clinics}"
    )


with col5:

    st.metric(
        "Average Monthly",
        f"{average_monthly:,.1f}"
    )


st.divider()


# ============================================================
# MONTHLY SUMMARY
# ============================================================

monthly = (
    filtered_data
    .groupby(
        "MONTH",
        observed=True
    )
    .agg(
        NEW=("NEW", "sum"),
        REVISIT=("REVISIT", "sum"),
        TOTAL=("DISPLAY_TOTAL", "sum")
    )
    .reset_index()
)

monthly["MONTH_NAME"] = (
    monthly["MONTH"].astype(str)
)


# ============================================================
# MONTHLY TREND
# ============================================================

st.subheader("📈 Monthly Visit Trend")

fig_trend = go.Figure()


fig_trend.add_trace(
    go.Scatter(
        x=monthly["MONTH_NAME"],
        y=monthly["TOTAL"],
        mode="lines+markers",
        name="Visits",
        line=dict(width=3),
        marker=dict(size=8)
    )
)


fig_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Number of Visits",
    hovermode="x unified",
    height=450
)


st.plotly_chart(
    fig_trend,
    use_container_width=True
)


# ============================================================
# NEW VS REVISIT + CLINIC COMPARISON
# ============================================================

col1, col2 = st.columns(2)


# ============================================================
# NEW VS REVISIT
# ============================================================

with col1:

    st.subheader("👥 New vs Revisit")

    fig_patient = go.Figure()


    fig_patient.add_trace(
        go.Bar(
            x=monthly["MONTH_NAME"],
            y=monthly["NEW"],
            name="New"
        )
    )


    fig_patient.add_trace(
        go.Bar(
            x=monthly["MONTH_NAME"],
            y=monthly["REVISIT"],
            name="Revisit"
        )
    )


    fig_patient.update_layout(
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="Visits",
        height=450
    )


    st.plotly_chart(
        fig_patient,
        use_container_width=True
    )


# ============================================================
# CLINIC COMPARISON
# ============================================================

with col2:

    st.subheader("🏥 Visits by Special Clinic")


    clinic_summary = (
        filtered_data
        .groupby(
            "SPECIAL CLINICS"
        )["DISPLAY_TOTAL"]
        .sum()
        .reset_index()
        .sort_values(
            "DISPLAY_TOTAL",
            ascending=True
        )
    )


    fig_clinic = px.bar(
        clinic_summary,
        x="DISPLAY_TOTAL",
        y="SPECIAL CLINICS",
        orientation="h",
        labels={
            "DISPLAY_TOTAL": "Visits",
            "SPECIAL CLINICS": "Special Clinic"
        }
    )


    fig_clinic.update_layout(
        height=450
    )


    st.plotly_chart(
        fig_clinic,
        use_container_width=True
    )


# ============================================================
# HEATMAP
# ============================================================

st.subheader("🔥 Clinic Attendance Heatmap")


heatmap_data = pd.pivot_table(
    filtered_data,
    index="MONTH",
    columns="SPECIAL CLINICS",
    values="DISPLAY_TOTAL",
    aggfunc="sum",
    fill_value=0,
    observed=False
)


fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=True,
    aspect="auto",
    labels={
        "x": "Special Clinic",
        "y": "Month",
        "color": "Visits"
    }
)


fig_heatmap.update_layout(
    height=650
)


st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)


# ============================================================
# CLINIC RANKING
# ============================================================

st.subheader("🏆 Special Clinic Performance Ranking")


ranking = (
    filtered_data
    .groupby("SPECIAL CLINICS")
    .agg(
        New=("NEW", "sum"),
        Revisit=("REVISIT", "sum"),
        Total=("DISPLAY_TOTAL", "sum")
    )
    .reset_index()
)


total_ranking_visits = (
    ranking["Total"].sum()
)


if total_ranking_visits > 0:

    ranking["Share (%)"] = (
        ranking["Total"]
        /
        total_ranking_visits
        *
        100
    )

else:

    ranking["Share (%)"] = 0


ranking = ranking.sort_values(
    "Total",
    ascending=False
)


ranking.insert(
    0,
    "Rank",
    range(1, len(ranking) + 1)
)


st.dataframe(
    ranking.style.format({
        "New": "{:,.0f}",
        "Revisit": "{:,.0f}",
        "Total": "{:,.0f}",
        "Share (%)": "{:.1f}%"
    }),
    use_container_width=True
)


# ============================================================
# HIGHEST AND LOWEST MONTH
# ============================================================

if len(monthly) > 0:

    highest = monthly.loc[
        monthly["TOTAL"].idxmax()
    ]

    lowest = monthly.loc[
        monthly["TOTAL"].idxmin()
    ]


    col1, col2 = st.columns(2)


    with col1:

        st.success(
            f"### 🟢 Highest Attendance\n"
            f"**{highest['MONTH_NAME']}** — "
            f"{highest['TOTAL']:,.0f} visits"
        )


    with col2:

        st.warning(
            f"### 🟡 Lowest Attendance\n"
            f"**{lowest['MONTH_NAME']}** — "
            f"{lowest['TOTAL']:,.0f} visits"
        )


# ============================================================
# DATA QUALITY
# ============================================================

st.divider()

st.subheader("🔍 Data Quality")


number_of_records = (
    len(filtered_data)
)

number_of_problems = (
    filtered_data[
        filtered_data["TOTAL_CHECK"] == "CHECK"
    ].shape[0]
)


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "Records analysed",
        f"{number_of_records:,}"
    )


with col2:

    st.metric(
        "Records requiring review",
        f"{number_of_problems:,}"
    )


if number_of_problems > 0:

    st.warning(
        "Some records have TOTAL different from "
        "NEW + REVISIT."
    )


    problems = filtered_data[
        filtered_data["TOTAL_CHECK"] == "CHECK"
    ]


    st.dataframe(
        problems[
            [
                "MONTH",
                "SPECIAL CLINICS",
                "NEW",
                "REVISIT",
                "TOTAL",
                "CALCULATED_TOTAL",
                "TOTAL_DIFFERENCE"
            ]
        ],
        use_container_width=True
    )

else:

    st.success(
        "No total inconsistencies found in the "
        "selected records."
    )


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

st.divider()

st.subheader("⬇️ Download Filtered Data")


csv_file = (
    filtered_data
    .to_csv(index=False)
    .encode("utf-8")
)


st.download_button(
    label="Download CSV",
    data=csv_file,
    file_name="special_clinic_filtered_data.csv",
    mime="text/csv"
)


# ============================================================
# RAW DATA
# ============================================================

with st.expander("View Raw/Filtered Data"):

    st.dataframe(
        filtered_data,
        use_container_width=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Wananchi Hospital Special Clinic Monitoring Dashboard | "
    "2025 | Python + Streamlit + Plotly"
)
