from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


DB_PATH = Path(__file__).parent / "pulseiq_public.duckdb"


st.set_page_config(
    page_title="PulseIQ | Workforce Intelligence",
    page_icon="📊",
    layout="wide",
)

# -------------------- Professional PulseIQ Theme --------------------
st.markdown("""
<style>
.stApp {
    background: #F0F6FC;
    color: #102A43;
}

[data-testid="stHeader"] {
    background: rgba(240, 246, 252, 0.95);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #17364D 0%, #102D43 100%);
}

/* Sidebar navigation page names - white text */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] p,
[data-testid="stSidebarNav"] span,
[data-testid="stSidebarNav"] div {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Selected page and hover text */
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNav"] a[aria-current="page"] span,
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a:hover span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p {
    color: #FFFFFF !important;
}

/* Department dropdown */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border-color: #D5E2EF !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #17364D !important;
    -webkit-text-fill-color: #17364D !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: #17364D !important;
    fill: #17364D !important;
}

/* Date filter */
[data-testid="stSidebar"] [data-testid="stDateInput"] {
    color-scheme: light !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: #FFFFFF !important;
    color: #17364D !important;
    -webkit-text-fill-color: #17364D !important;
    opacity: 1 !important;
    font-size: 14px !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] button {
    background: #FFFFFF !important;
    color: #17364D !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] button svg {
    color: #17364D !important;
    fill: #17364D !important;
}

[data-baseweb="popover"],
[data-baseweb="calendar"] {
    color-scheme: light !important;
    background: #FFFFFF !important;
}

[data-baseweb="calendar"] * {
    color: #17364D;
}

/* KPI cards */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2ECF5;
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 3px 12px rgba(25, 60, 90, 0.06);
}

[data-testid="stMetricLabel"] {
    color: #526A82 !important;
}

[data-testid="stMetricValue"] {
    color: #102A43 !important;
}

h1, h2, h3 {
    color: #102A43;
}

/* Insight cards */
.insight {
    background: #E5F6F0;
    color: #174E43;
    border: 1px solid #C8EBDD;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 4px 0 14px 0;
    font-size: 14px;
}

.insight b {
    color: #174E43;
}

.panel-title {
    color: #102A43;
    font-size: 20px;
    font-weight: 700;
    padding: 2px 0 10px 0;
}

.small-note {
    color: #526A82;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 PulseIQ | Workforce Intelligence")
st.caption("Workforce and headcount dashboard | Validated data views")

# Streamlit automatically lists dashboards stored in the pages/ folder.
if not DB_PATH.exists():
    st.error(f"DuckDB database not found: {DB_PATH}")
    st.stop()


# -------------------- Read approved views only --------------------
@st.cache_data
def load_view(view_name):
    allowed_views = {
        "dash_department_headcount",
        "m02_hires",
        "m03_exits",
        "m04_attrition_rate_monthly",
        "dash_current_work_mode",
        "dash_current_location_tier",
    }

    if view_name not in allowed_views:
        raise ValueError(f"Unapproved dashboard view: {view_name}")

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(
            f"SELECT * FROM main.{view_name}"
        ).df()


try:
    headcount = load_view("dash_department_headcount")
    hires = load_view("m02_hires")
    exits = load_view("m03_exits")
    attrition = load_view("m04_attrition_rate_monthly")
    work_modes = load_view("dash_current_work_mode")
    location_tiers = load_view("dash_current_location_tier")

except Exception as exc:
    st.error(f"Could not load dashboard views: {exc}")
    st.info("Check create_dashboard_views.py and metric view names.")
    st.stop()


required_columns = {
    "month_start_date",
    "department_id",
    "department_name",
    "headcount",
}

if not required_columns.issubset(headcount.columns):
    st.error(
        f"Headcount view is missing columns: "
        f"{required_columns - set(headcount.columns)}"
    )
    st.stop()

if headcount.empty:
    st.warning("No headcount data is available.")
    st.stop()

for frame in (headcount, hires, exits, attrition):
    if "month_start_date" in frame.columns:
        frame["month_start_date"] = pd.to_datetime(
            frame["month_start_date"],
            errors="coerce",
        )

months = sorted(headcount["month_start_date"].dropna().unique())

if not months:
    st.error("No valid reporting dates were found.")
    st.stop()

min_month = pd.Timestamp(months[0]).date()
max_month = pd.Timestamp(months[-1]).date()


# -------------------- Sidebar Filters --------------------
with st.sidebar:
    st.markdown("## Filters")

    departments = ["All departments"] + sorted(
        headcount["department_name"].dropna().unique().tolist()
    )

    selected_department = st.selectbox(
        "Department",
        departments,
        index=0,
        key="department_filter",
    )

    st.markdown("**Reporting period**")

    if "reporting_period" not in st.session_state:
        st.session_state["reporting_period"] = (
            min_month,
            max_month,
        )

    def reset_date_range():
        st.session_state["reporting_period"] = (
            min_month,
            max_month,
        )

    st.button(
        "↺ Reset Date Range",
        on_click=reset_date_range,
        use_container_width=True,
        key="reset_date_range_button",
    )

    date_range = st.date_input(
        "Reporting period",
        min_value=min_month,
        max_value=max_month,
        format="DD/MM/YYYY",
        key="reporting_period",
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("PulseIQ Workforce Analytics")
    st.caption("Source: DuckDB validated views")


# Process selected dates
if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        st.warning("Select a reporting date range.")
        st.stop()
else:
    start_date = end_date = date_range

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()


# -------------------- Apply Filters --------------------
filtered = headcount[
    headcount["month_start_date"].dt.date.between(
        start_date,
        end_date,
    )
].copy()

if selected_department != "All departments":
    filtered = filtered[
        filtered["department_name"] == selected_department
    ]

if filtered.empty:
    st.warning("No records match the selected department and date range.")
    st.stop()

latest_month = filtered["month_start_date"].max()

latest_rows = filtered[
    filtered["month_start_date"] == latest_month
]

latest_headcount = int(latest_rows["headcount"].sum())

previous_months = sorted(
    filtered.loc[
        filtered["month_start_date"] < latest_month,
        "month_start_date",
    ].dropna().unique()
)

previous_headcount = None

if previous_months:
    previous_month = previous_months[-1]
    previous_headcount = int(
        filtered.loc[
            filtered["month_start_date"] == previous_month,
            "headcount",
        ].sum()
    )

headcount_delta = (
    latest_headcount - previous_headcount
    if previous_headcount is not None
    else None
)

department_ids = latest_rows["department_id"].unique().tolist()

hires_latest = hires[
    hires["month_start_date"] == latest_month
].copy()

exits_latest = exits[
    exits["month_start_date"] == latest_month
].copy()

attrition_latest = attrition[
    attrition["month_start_date"] == latest_month
].copy()

if selected_department != "All departments":
    hires_latest = hires_latest[
        hires_latest["department_id"].isin(department_ids)
    ]

    exits_latest = exits_latest[
        exits_latest["department_id"].isin(department_ids)
    ]

    attrition_latest = attrition_latest[
        attrition_latest["department_id"].isin(department_ids)
    ]

hire_count = (
    int(hires_latest["hires"].sum())
    if "hires" in hires_latest.columns
    else 0
)

exit_count = (
    int(exits_latest["exits"].sum())
    if "exits" in exits_latest.columns
    else 0
)

rate_columns = [
    col for col in attrition_latest.columns
    if "attrition_rate_pct" in col.lower()
]

attrition_value = None

if rate_columns and not attrition_latest.empty:
    rates = pd.to_numeric(
        attrition_latest[rate_columns[0]],
        errors="coerce",
    ).dropna()

    if not rates.empty:
        attrition_value = float(rates.mean())


# -------------------- KPI Cards --------------------
st.markdown(f"**Reporting month: {latest_month:%B %Y}**")
st.caption(f"Data cut-off: {(latest_month + pd.offsets.MonthEnd(0)):%d %B %Y}")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Month-end Headcount",
    f"{latest_headcount:,}",
    delta=(
        f"{headcount_delta:+,} vs previous available month"
        if headcount_delta is not None
        else None
    ),
)

k2.metric("Hires in Month", f"{hire_count:,}")
k3.metric("Exits in Month", f"{exit_count:,}")

k4.metric(
    "Monthly Attrition",
    f"{attrition_value:.2f}%"
    if attrition_value is not None
    else "N/A",
)

teal = "#159A9C"
blue = "#438FE8"
purple = "#9860DE"
navy = "#17364D"


def show_insight(message):
    st.markdown(
        f'<div class="insight">💡 <b>Insight:</b> {message}</div>',
        unsafe_allow_html=True,
    )


# -------------------- 1. Headcount Trend --------------------
left, right = st.columns(2, gap="medium")

with left:
    st.markdown(
        '<div class="panel-title">1. Headcount Trend</div>',
        unsafe_allow_html=True,
    )

    trend = (
        filtered.groupby("month_start_date", as_index=False)["headcount"]
        .sum()
        .sort_values("month_start_date")
    )

    fig = px.line(
        trend,
        x="month_start_date",
        y="headcount",
        markers=True,
        labels={
            "month_start_date": "Month",
            "headcount": "Headcount",
        },
    )

    fig.update_traces(
        line_color=teal,
        line_width=3,
        marker_size=7,
    )

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=15, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font_color=navy,
    )

    st.plotly_chart(fig, use_container_width=True)

    if len(trend) >= 2:
        first = int(trend.iloc[0]["headcount"])
        last = int(trend.iloc[-1]["headcount"])
        change = last - first
        change_pct = change / first * 100 if first else 0

        direction = (
            "increased" if change > 0
            else "decreased" if change < 0
            else "remained unchanged"
        )

        insight = (
            f"Headcount {direction} by {abs(change):,} "
            f"({abs(change_pct):.1f}%) from "
            f"{trend.iloc[0]['month_start_date']:%b %Y} to "
            f"{trend.iloc[-1]['month_start_date']:%b %Y}."
        )
    else:
        insight = (
            "Choose a wider reporting period to compare headcount over time."
        )

    show_insight(insight)


# -------------------- 2. Department Breakdown --------------------
with right:
    st.markdown(
        '<div class="panel-title">2. Department Headcount Breakdown</div>',
        unsafe_allow_html=True,
    )

    dept = (
        latest_rows.groupby("department_name", as_index=False)["headcount"]
        .sum()
        .sort_values("headcount", ascending=True)
    )

    fig = px.bar(
        dept,
        x="headcount",
        y="department_name",
        orientation="h",
        labels={
            "headcount": "Headcount",
            "department_name": "Department",
        },
    )

    fig.update_traces(
        marker_color=blue,
        text=dept["headcount"],
        textposition="outside",
        cliponaxis=False,
    )

    max_value = int(dept["headcount"].max()) if not dept.empty else 1

    fig.update_layout(
        height=330,
        margin=dict(l=10, r=35, t=15, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font_color=navy,
        yaxis_title="",
        xaxis_range=[0, max_value * 1.18],
    )

    st.plotly_chart(fig, use_container_width=True)

    if not dept.empty:
        largest = dept.iloc[-1]
        insight = (
            f"{largest['department_name']} has the largest headcount "
            f"in {latest_month:%B %Y} "
            f"({int(largest['headcount']):,} employees)."
        )
    else:
        insight = "No department headcount data is available."

    show_insight(insight)


# -------------------- 3. Location Tier --------------------
left2, right2 = st.columns(2, gap="medium")

with left2:
    st.markdown(
        '<div class="panel-title">3. Workforce by Location Tier</div>',
        unsafe_allow_html=True,
    )

    st.caption("Current active-employee snapshot; not historical.")

    if not location_tiers.empty:
        tier = location_tiers.sort_values(
            "employee_count",
            ascending=False,
        )

        fig = px.bar(
            tier,
            x="city_tier",
            y="employee_count",
            labels={
                "city_tier": "Location Tier",
                "employee_count": "Employees",
            },
        )

        fig.update_traces(
            marker_color=teal,
            text=tier["employee_count"],
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            font_color=navy,
        )

        st.plotly_chart(fig, use_container_width=True)

        top_tier = tier.iloc[0]
        insight = (
            f"{top_tier['city_tier']} has the highest employee concentration "
            f"({int(top_tier['employee_count']):,} active employees)."
        )
    else:
        insight = "No location-tier data is available."

    show_insight(insight)


# -------------------- 4. Work Mode --------------------
with right2:
    st.markdown(
        '<div class="panel-title">4. Workforce by Work Mode</div>',
        unsafe_allow_html=True,
    )

    st.caption("Current active-employee snapshot; not historical.")

    if not work_modes.empty:
        mode = work_modes.sort_values(
            "employee_count",
            ascending=False,
        )

        mode_colors = [
            teal if str(value).lower() == "hybrid"
            else blue if str(value).lower() == "onsite"
            else purple
            for value in mode["work_mode"]
        ]

        fig = px.bar(
            mode,
            x="work_mode",
            y="employee_count",
            labels={
                "work_mode": "Work Mode",
                "employee_count": "Employees",
            },
        )

        fig.update_traces(
            marker_color=mode_colors,
            text=mode["employee_count"],
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#FFFFFF",
            font_color=navy,
        )

        st.plotly_chart(fig, use_container_width=True)

        top_mode = mode.iloc[0]
        insight = (
            f"{top_mode['work_mode']} is the most common work mode, with "
            f"{int(top_mode['employee_count']):,} active employees."
        )
    else:
        insight = "No work-mode data is available."

    show_insight(insight)


st.divider()

st.markdown(
    '<div class="small-note">PulseIQ | Workforce Intelligence · '
    'Historical headcount uses the metric layer. Location tier and work mode '
    'use current active-employee snapshot views in DuckDB.</div>',
    unsafe_allow_html=True,
)

