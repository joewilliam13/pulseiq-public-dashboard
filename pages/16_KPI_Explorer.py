
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# 1. CONFIGURATION
# =====================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "pulseiq_public.duckdb"
USERS_PATH = ROOT_DIR / "demo_users.csv"

st.set_page_config(
    page_title="PulseIQ | KPI Explorer",
    page_icon="📊",
    layout="wide",
)


# =====================================================
# 2. PULSEIQ THEME
# =====================================================

st.markdown("""
<style>
.stApp {
    background: #F0F6FC;
    color: #102A43;
}

[data-testid="stHeader"] {
    background: rgba(240,246,252,0.95);
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg, #102F46 0%, #09263B 100%
    ) !important;
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

[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #35536B !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1px solid #D5E2EF !important;
    border-radius: 8px !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] input {
    color: #17364D !important;
    -webkit-text-fill-color: #17364D !important;
}

[data-testid="stSidebar"] button {
    background: #F7FAFD !important;
    border: 1px solid #D5E2EF !important;
    border-radius: 8px !important;
}

[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span {
    color: #17364D !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2ECF5;
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 3px 12px rgba(25,60,90,0.06);
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

/* Compact sidebar spacing */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.8rem;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.45rem;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    margin-top: 0.15rem;
    margin-bottom: 0.15rem;
    padding-bottom: 0;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.15rem;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] {
    margin-bottom: 0.1rem;
}

[data-testid="stSidebar"] [data-testid="stButton"] {
    margin-top: 0.15rem;
}

[data-testid="stSidebarNav"] a {
    padding-top: 0.25rem !important;
    padding-bottom: 0.25rem !important;
    min-height: 2rem !important;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. HEADER
# =====================================================

st.title("📊 Self-Service KPI Explorer")
st.caption(
    "Task 18 | Role-based KPI exploration with privacy protection"
)

st.info(
    "Demo role simulation only. This page does not provide "
    "password-based authentication or verify real user identity."
)


# =====================================================
# 4. FILE VALIDATION
# =====================================================

if not DB_PATH.exists():
    st.error(f"Public database not found: {DB_PATH}")
    st.stop()

if not USERS_PATH.exists():
    st.error(f"Demo users file not found: {USERS_PATH}")
    st.stop()

users = pd.read_csv(USERS_PATH)

required_columns = {"username", "role", "sees"}

if not required_columns.issubset(users.columns):
    st.error("Invalid demo_users.csv structure.")
    st.stop()

if users.empty:
    st.error("No demo users found.")
    st.stop()


# =====================================================
# 5. LOAD APPROVED PUBLIC DATA
# =====================================================

@st.cache_data
def load_public_data(db_path):

    with duckdb.connect(db_path, read_only=True) as con:

        headcount = con.execute("""
            SELECT
                month_start_date,
                department_id,
                department_name,
                headcount
            FROM dash_department_headcount
        """).df()

        hires = con.execute("""
            SELECT
                month_start_date,
                department_id,
                hires
            FROM m02_hires
        """).df()

        exits = con.execute("""
            SELECT
                month_start_date,
                department_id,
                exits
            FROM m03_exits
        """).df()

        attrition = con.execute("""
            SELECT
                month_start_date,
                department_id,
                exits,
                headcount_start,
                attrition_rate_pct
            FROM m04_attrition_rate_monthly
        """).df()

        work_mode = con.execute("""
            SELECT work_mode, employee_count
            FROM dash_current_work_mode
        """).df()

        location = con.execute("""
            SELECT city_tier, employee_count
            FROM dash_current_location_tier
        """).df()

    return (
        headcount,
        hires,
        exits,
        attrition,
        work_mode,
        location,
    )


try:
    (
        headcount_df,
        hires_df,
        exits_df,
        attrition_df,
        work_mode_df,
        location_df,
    ) = load_public_data(str(DB_PATH))

except Exception as error:
    st.error(f"Unable to load public data: {error}")
    st.stop()

if headcount_df.empty:
    st.warning("No headcount data available.")
    st.stop()

headcount_df["month_start_date"] = pd.to_datetime(
    headcount_df["month_start_date"]
)

available_months = sorted(
    headcount_df["month_start_date"].dropna().unique()
)

if not available_months:
    st.error("No reporting months available.")
    st.stop()


# =====================================================
# 6. ROLE PERMISSIONS
# =====================================================

ROLE_PERMISSIONS = {

    "ADMIN": {
        "metrics": [
            "Headcount",
            "Hires",
            "Exits",
            "Monthly Attrition Rate",
            "Work Mode",
            "Location Tier",
        ],
        "dimensions": ["Company", "Department", "Team"],
    },

    "HR": {
        "metrics": [
            "Headcount",
            "Hires",
            "Exits",
            "Monthly Attrition Rate",
            "Work Mode",
            "Location Tier",
        ],
        "dimensions": ["Company", "Department", "Team"],
    },

    "MANAGER": {
        "metrics": [
            "Headcount",
            "Hires",
            "Exits",
            "Monthly Attrition Rate",
        ],
        "dimensions": ["Team"],
    },

    "EXECUTIVE": {
        "metrics": [
            "Headcount",
            "Hires",
            "Exits",
            "Monthly Attrition Rate",
            "Work Mode",
            "Location Tier",
        ],
        "dimensions": ["Company"],
    },
}


# =====================================================
# 7. RESET FILTERS
# =====================================================

def reset_filters():
    for key in [
        "kpi_metric",
        "kpi_dimension",
        "kpi_month",
    ]:
        st.session_state.pop(key, None)


# =====================================================
# 8. SIDEBAR FILTERS
# =====================================================

with st.sidebar:

    # Compact sidebar without PulseIQ logo or branding text
    st.markdown("## KPI Explorer")
    st.markdown("### Demo User")

    selected_username = st.selectbox(
        "Select Demo User",
        users["username"].astype(str).tolist(),
        key="demo_username",
    )

    user_row = users[
        users["username"].astype(str) == selected_username
    ].iloc[0]

    role = str(user_row["role"]).strip().upper()

    if role not in ROLE_PERMISSIONS:
        st.error("Unknown role. Access denied.")
        st.stop()

    st.success(f"Role: {role}")
    st.caption(str(user_row["sees"]))

    permissions = ROLE_PERMISSIONS[role]
    allowed_metrics = permissions["metrics"]
    allowed_dimensions = permissions["dimensions"]

    if st.session_state.get("kpi_metric") not in allowed_metrics:
        st.session_state.pop("kpi_metric", None)

    if st.session_state.get("kpi_dimension") not in allowed_dimensions:
        st.session_state.pop("kpi_dimension", None)

    st.divider()
    st.markdown("### Filters")

    selected_metric = st.selectbox(
        "Choose a Metric",
        allowed_metrics,
        key="kpi_metric",
    )

    selected_dimension = st.selectbox(
        "Choose a Dimension",
        allowed_dimensions,
        key="kpi_dimension",
    )

    monthly_metrics = [
        "Headcount",
        "Hires",
        "Exits",
        "Monthly Attrition Rate",
    ]

    selected_month = None

    if selected_metric in monthly_metrics:

        if "kpi_month" not in st.session_state:
            st.session_state["kpi_month"] = available_months[-1]

        if st.session_state["kpi_month"] not in available_months:
            st.session_state["kpi_month"] = available_months[-1]

        selected_month = st.selectbox(
            "Reporting Month",
            available_months,
            index=available_months.index(
                st.session_state["kpi_month"]
            ),
            format_func=lambda value: pd.Timestamp(
                value
            ).strftime("%B %Y"),
            key="kpi_month",
        )

    st.button(
        "↻ Reset Filters",
        use_container_width=True,
        on_click=reset_filters,
    )

# =====================================================
# 9. HELPER FUNCTIONS
# =====================================================

def get_month_data(df, month):

    data = df.copy()

    data["month_start_date"] = pd.to_datetime(
        data["month_start_date"]
    )

    return data[
        data["month_start_date"] == pd.Timestamp(month)
    ].copy()


def get_department_metric(metric, month):

    current_headcount = get_month_data(
        headcount_df, month
    )

    if metric == "Headcount":

        result = current_headcount[
            [
                "department_id",
                "department_name",
                "headcount",
            ]
        ].copy()

        result = result.rename(
            columns={"headcount": "Value"}
        )

        result["Group Size"] = result["Value"]
        threshold = 5

    elif metric == "Hires":

        current = get_month_data(hires_df, month)

        result = current.merge(
            current_headcount[
                [
                    "department_id",
                    "department_name",
                    "headcount",
                ]
            ],
            on="department_id",
            how="inner",
        )

        result = result[
            [
                "department_id",
                "department_name",
                "headcount",
                "hires",
            ]
        ].rename(
            columns={"hires": "Value"}
        )

        result["Group Size"] = result["headcount"]
        threshold = 5

    elif metric == "Exits":

        current = get_month_data(exits_df, month)

        result = current.merge(
            current_headcount[
                [
                    "department_id",
                    "department_name",
                    "headcount",
                ]
            ],
            on="department_id",
            how="inner",
        )

        result = result[
            [
                "department_id",
                "department_name",
                "headcount",
                "exits",
            ]
        ].rename(
            columns={"exits": "Value"}
        )

        result["Group Size"] = result["headcount"]
        threshold = 5

    else:

        current = get_month_data(
            attrition_df, month
        )

        result = current.merge(
            current_headcount[
                ["department_id", "department_name"]
            ],
            on="department_id",
            how="inner",
        )

        result = result[
            [
                "department_id",
                "department_name",
                "headcount_start",
                "attrition_rate_pct",
            ]
        ].rename(
            columns={"attrition_rate_pct": "Value"}
        )

        result["Group Size"] = result["headcount_start"]
        threshold = 10

    safe_data = result[
        result["Group Size"] >= threshold
    ].copy()

    hidden_count = len(result) - len(safe_data)

    return safe_data, threshold, hidden_count


# =====================================================
# 10. TEAM PRIVACY
# =====================================================

if selected_dimension == "Team":

    st.warning(
        "Team-level results are unavailable because the "
        "approved public database does not contain team-level "
        "records or manager-to-team mapping. No team data is displayed."
    )

    st.stop()


# =====================================================
# 11. PREPARE SELECTED METRIC
# =====================================================

if selected_metric in monthly_metrics:

    metric_data, threshold, hidden_count = get_department_metric(
        selected_metric,
        selected_month,
    )

    month_label = pd.Timestamp(
        selected_month
    ).strftime("%B %Y")

else:

    metric_data = pd.DataFrame()
    threshold = 5
    hidden_count = 0
    month_label = "Current"


# =====================================================
# 12. WORKFORCE KPI SUMMARY
# =====================================================

st.subheader("Workforce KPI Summary")

if selected_metric in monthly_metrics:

    hc_data, _, hc_hidden = get_department_metric(
        "Headcount", selected_month
    )

    hire_data, _, hire_hidden = get_department_metric(
        "Hires", selected_month
    )

    exit_data, _, exit_hidden = get_department_metric(
        "Exits", selected_month
    )

    attr_data, _, attr_hidden = get_department_metric(
        "Monthly Attrition Rate", selected_month
    )

    c1, c2, c3, c4 = st.columns(4)

    # Total Headcount

    with c1:

        if hc_hidden > 0:
            value = "Suppressed"
        else:
            value = f"{hc_data['Value'].sum():,.0f}"

        st.metric(
            "Total Headcount",
            value,
        )

    # Total Hires

    with c2:

        if hire_hidden > 0:
            value = "Suppressed"
        else:
            value = f"{hire_data['Value'].sum():,.0f}"

        st.metric(
            "Total Hires",
            value,
        )

    # Total Exits

    with c3:

        if exit_hidden > 0:
            value = "Suppressed"
        else:
            value = f"{exit_data['Value'].sum():,.0f}"

        st.metric(
            "Total Exits",
            value,
        )

    # Attrition Rate

    with c4:

        if attr_hidden > 0:

            value = "Suppressed"

        else:

            attr_month = get_month_data(
                attrition_df,
                selected_month,
            )

            start_total = attr_month[
                "headcount_start"
            ].sum()

            exit_total = attr_month[
                "exits"
            ].sum()

            rate = (
                exit_total / start_total * 100
                if start_total > 0 else 0
            )

            value = f"{rate:.2f}%"

        st.metric(
            "Attrition Rate",
            value,
        )

    st.caption(
        f"Reporting period: {month_label}"
    )


# =====================================================
# 13. DEPARTMENT LEVEL CHARTS
# =====================================================

if selected_dimension == "Department":

    st.subheader(
        f"{selected_metric} by Department"
    )

    if metric_data.empty:

        st.warning(
            "No department groups meet the minimum "
            "group-size requirement."
        )

    else:

        chart_data = metric_data[
            ["department_name", "Value"]
        ].sort_values(
            "Value",
            ascending=False,
        )

        left, right = st.columns([1.5, 1])

        # BAR CHART

        with left:

            fig = px.bar(
                chart_data,
                x="department_name",
                y="Value",
                text_auto=".2f",
                title=f"{selected_metric} by Department",
                color_discrete_sequence=["#15965B"],
            )

            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_color="#17364D",
                xaxis_title="Department",
                yaxis_title=selected_metric,
                margin=dict(
                    l=20,
                    r=20,
                    t=55,
                    b=20,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        # DONUT CHART

        with right:

            st.subheader(
                f"{selected_metric} Share by Department"
            )

            if chart_data["Value"].sum() > 0:

                fig = px.pie(
                    chart_data,
                    names="department_name",
                    values="Value",
                    hole=0.48,
                )

                fig.update_layout(
                    paper_bgcolor="white",
                    font_color="#17364D",
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10,
                    ),
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            else:

                st.info(
                    "No positive values available."
                )

        # DEPARTMENT DETAILS TABLE

        st.subheader(
            "Department KPI Details"
        )

        detail = chart_data.copy()

        total = detail["Value"].sum()

        detail["Share (%)"] = (
            detail["Value"] / total * 100
            if total > 0 else 0
        )

        detail["Value"] = detail["Value"].round(2)

        detail["Share (%)"] = (
            detail["Share (%)"].round(2)
        )

        st.dataframe(
            detail,
            use_container_width=True,
            hide_index=True,
        )

    # SMALL GROUP WARNING

    if hidden_count > 0:

        st.warning(
            f"{hidden_count} department group(s) hidden "
            f"because they are below the minimum group "
            f"size of {threshold}."
        )

# =====================================================
# 14. COMPANY LEVEL DASHBOARD
# =====================================================

elif selected_dimension == "Company":

    st.subheader("Company-Level KPI")

    # -------------------------------------------------
    # WORK MODE DISTRIBUTION
    # -------------------------------------------------

    if selected_metric == "Work Mode":

        safe = work_mode_df[
            work_mode_df["employee_count"] >= 5
        ].copy()

        hidden = len(work_mode_df) - len(safe)

        if hidden > 0:

            st.warning(
                f"{hidden} work-mode group(s) below "
                "5 employees are hidden."
            )

        if safe.empty:

            st.warning(
                "No work-mode groups meet the minimum group size."
            )

        else:

            left, right = st.columns([1.4, 1])

            with left:

                fig = px.pie(
                    safe,
                    names="work_mode",
                    values="employee_count",
                    hole=0.48,
                    title="Work Mode Distribution",
                )

                fig.update_layout(
                    paper_bgcolor="white",
                    font_color="#17364D",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            with right:

                st.subheader("Work Mode Details")

                st.dataframe(
                    safe,
                    use_container_width=True,
                    hide_index=True,
                )

    # -------------------------------------------------
    # LOCATION TIER DISTRIBUTION
    # -------------------------------------------------

    elif selected_metric == "Location Tier":

        safe = location_df[
            location_df["employee_count"] >= 5
        ].copy()

        hidden = len(location_df) - len(safe)

        if hidden > 0:

            st.warning(
                f"{hidden} location group(s) below "
                "5 employees are hidden."
            )

        if safe.empty:

            st.warning(
                "No location groups meet the minimum group size."
            )

        else:

            left, right = st.columns([1.4, 1])

            with left:

                fig = px.bar(
                    safe,
                    x="city_tier",
                    y="employee_count",
                    text_auto=True,
                    title="Employees by Location Tier",
                    color_discrete_sequence=["#15965B"],
                )

                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font_color="#17364D",
                    xaxis_title="Location Tier",
                    yaxis_title="Employee Count",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            with right:

                st.subheader("Location Details")

                st.dataframe(
                    safe,
                    use_container_width=True,
                    hide_index=True,
                )

    # -------------------------------------------------
    # MONTHLY COMPANY KPI
    # -------------------------------------------------

    else:

        if metric_data.empty:

            st.warning(
                "No approved company data available."
            )

        elif hidden_count > 0:

            st.warning(
                "Company total is hidden because one or more "
                "departments are suppressed. This prevents "
                "reverse calculation of small groups."
            )

        else:

            company_value = metric_data["Value"].sum()

            if selected_metric == "Monthly Attrition Rate":

                attr_month = get_month_data(
                    attrition_df,
                    selected_month,
                )

                start_total = attr_month["headcount_start"].sum()
                exit_total = attr_month["exits"].sum()

                company_value = (
                    exit_total / start_total * 100
                    if start_total > 0 else 0
                )

                st.metric(
                    selected_metric,
                    f"{company_value:.2f}%",
                )
            else:

                st.metric(
                    selected_metric,
                    f"{company_value:,.0f}",
                )


# =====================================================
# 15. PRIVACY AND DATA AVAILABILITY
# =====================================================

with st.expander(
    "🛡️ Privacy and Data Availability",
    expanded=True,
):

    st.write(
        "1. Only approved public database views are used."
    )

    st.write(
        "2. Headcount, Hires and Exits use a minimum "
        "group size of 5."
    )

    st.write(
        "3. Monthly Attrition uses a minimum group size of 10."
    )

    st.write(
        "4. Small groups are suppressed."
    )

    st.write(
        "5. Company totals are withheld when necessary "
        "to prevent reverse calculation."
    )

    st.write(
        "6. Team-level data and manager-to-team mapping "
        "are unavailable in the approved public database."
    )

    st.write(
        "7. Individual employee and salary-level records "
        "are not displayed."
    )

    st.write(
        "8. Demo role selection is not real authentication."
    )

    st.write(
        "9. HR department-specific salary detail is unavailable "
        "because salary-level data and HR department mapping "
        "are not present in the public database."
    )


# =====================================================
# 16. FOOTER
# =====================================================

st.divider()

st.caption(
    "PulseIQ | Self-Service KPI Explorer | Task 18"
)
