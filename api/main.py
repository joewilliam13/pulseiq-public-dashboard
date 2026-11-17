
from pathlib import Path
import duckdb

from fastapi import FastAPI, HTTPException

# Project paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "pulseiq_public.duckdb"

app = FastAPI(
    title="PulseIQ Metrics API",
    description="API for accessing trusted PulseIQ workforce metrics.",
    version="1.0.0"
)

METRICS = {
    "headcount": {
        "metric_id": "M01",
        "name": "Headcount",
        "view": "dash_department_headcount",
        "value_column": "headcount",
        "date_column": "month_start_date",
        "definition": "Active employees on the last day of the month.",
        "source": "dash_department_headcount",
        "unit": "count"
    },
    "hires": {
        "metric_id": "M02",
        "name": "Hires",
        "view": "m02_hires",
        "value_column": "hires",
        "date_column": "month_start_date",
        "definition": "Employees whose hire date falls in the month.",
        "source": "m02_hires",
        "unit": "count"
    },
    "exits": {
        "metric_id": "M03",
        "name": "Exits",
        "view": "m03_exits",
        "value_column": "exits",
        "date_column": "month_start_date",
        "definition": "Employees whose exit date falls in the month.",
        "source": "m03_exits",
        "unit": "count"
    },
    "attrition": {
        "metric_id": "M04",
        "name": "Monthly Attrition Rate",
        "view": "m04_attrition_rate_monthly",
        "value_column": "attrition_rate_pct",
        "date_column": "month_start_date",
        "definition": "Share of employees who left during the month.",
        "source": "m04_attrition_rate_monthly",
        "unit": "percent"
    },
    "attendance": {
        "metric_id": "M13",
        "name": "Attendance Rate",
        "view": "m13_attendance_rate",
        "value_column": "attendance_rate_pct",
        "date_column": "period_end_date",
        "definition": "Present days plus half-weighted unpaid half-days divided by scheduled working days. Only groups with at least 5 employees are included.",
        "source": "m13_attendance_rate",
        "unit": "percent"
    }
}


def get_metric_data(metric_key: str):
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="PulseIQ public database not found."
        )

    metric = METRICS[metric_key]
    con = None

    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)

        query = f"""
            SELECT
                {metric['date_column']} AS period,
                department_id,
                {metric['value_column']} AS value
            FROM {metric['view']}
            ORDER BY {metric['date_column']} DESC
        """

        rows = con.execute(query).fetchall()

        # Public database does not contain the private ETL log.
        refresh = None

        return {
            "metric_id": metric["metric_id"],
            "metric": metric["name"],
            "definition": metric["definition"],
            "source": metric["source"],
            "unit": metric["unit"],
            "last_refresh": None,
            "data_freshness": (
                "Refresh timestamp unavailable in public database"
            ),
            "data": [
                {
                    "period": str(row[0]),
                    "department_id": row[1],
                    "value": row[2]
                }
                for row in rows
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve metric: {str(e)}"
        )

    finally:
        if con is not None:
            con.close()


@app.get("/")
def home():
    return {
        "message": "Welcome to PulseIQ Metrics API",
        "documentation": "/docs",
        "available_metrics": list(METRICS.keys())
    }


@app.get("/metrics")
def list_metrics():
    return {
        "total_metrics": len(METRICS),
        "metrics": [
            {
                "metric_id": metric["metric_id"],
                "name": metric["name"],
                "definition": metric["definition"],
                "source": metric["source"]
            }
            for metric in METRICS.values()
        ]
    }


@app.get("/metrics/headcount")
def headcount():
    return get_metric_data("headcount")


@app.get("/metrics/hires")
def hires():
    return get_metric_data("hires")


@app.get("/metrics/exits")
def exits():
    return get_metric_data("exits")


@app.get("/metrics/attrition")
def attrition():
    return get_metric_data("attrition")


@app.get("/metrics/attendance")
def attendance():
    return get_metric_data("attendance")
