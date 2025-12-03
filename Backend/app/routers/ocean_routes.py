from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
from app.database import supabase

router = APIRouter(prefix="/ocean", tags=["Ocean Visualization"])


# ===========================================================
# 1) DIRECT SUPABASE LOADER (NO db_reader_service required)
# ===========================================================

def load_ocean_data(sample_size=3000):
    rows = []
    limit = 2000
    offset = 0

    while True:
        res = (
            supabase.table("ocean_data")
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )

        if not res.data:
            break

        rows.extend(res.data)
        offset += limit

    if not rows:
        return None

    df = pd.DataFrame(rows)

    # Normalize None/NaN
    df = df.where(pd.notnull(df), None)

    # Ensure column names are upper-case for visualization consistency
    rename_map = {
        "lat": "LAT",
        "lon": "LON",
        "dic": "DIC",
        "mld": "MLD",
        "pco2_original": "PCO2_ORIGINAL",
        "chl": "CHL",
        "no3": "NO3",
        "sss": "SSS",
        "sst": "SST",
        "deviant_uncertainty": "DEVIANT_UNCERTAINTY"
    }
    df = df.rename(columns=rename_map)

    # Normalize datetime column if available
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # Sample for performance
    if len(df) > sample_size:
        df = df.sample(n=sample_size)

    return df


# ===========================================================
# VALID PARAMETERS & UNITS
# ===========================================================

PARAMETERS = [
    "DIC", "MLD", "PCO2_ORIGINAL", "CHL",
    "NO3", "SSS", "SST", "DEVIANT_UNCERTAINTY"
]

UNITS = {
    "DIC": "milimole/m3",
    "MLD": "m",
    "PCO2_ORIGINAL": "micro_atm",
    "CHL": "kg/m3",
    "NO3": "milimole/m3",
    "SSS": "PSU",
    "SST": "deg C",
    "DEVIANT_UNCERTAINTY": "micro atm"
}


# ===========================================================
# HELPER: NEAREST ROW
# ===========================================================

def get_nearest_row(df, LAT, LON):
    df["dist"] = np.sqrt((df["LAT"] - LAT)**2 + (df["LON"] - LON)**2)
    nearest_idx = df["dist"].idxmin()
    return df.loc[nearest_idx]


# ===========================================================
# 1) GET VALUE BY LAT/LON
# ===========================================================

@router.get("/get_value")
def get_value(LAT: float, LON: float,
              parameter: str = Query(..., enum=PARAMETERS)):

    df = load_ocean_data()
    if df is None:
        return {"error": "No ocean data found"}

    row = get_nearest_row(df, LAT, LON)
    value = row[parameter]
    unit = UNITS.get(parameter, "")

    return {
        "input_lat": LAT,
        "input_lon": LON,
        "nearest_lat": float(row["LAT"]),
        "nearest_lon": float(row["LON"]),
        "parameter": parameter,
        "value": float(value),
        "unit": unit
    }


# ===========================================================
# 2) BUBBLE MAP (HTML PLOT)
# ===========================================================

@router.get("/map", response_class=HTMLResponse)
def bubble_map(parameter: str = Query(..., enum=PARAMETERS)):
    df = load_ocean_data()
    if df is None:
        return HTMLResponse("<h3>No ocean data</h3>")

    if parameter not in df.columns:
        return HTMLResponse(f"<h3>Parameter '{parameter}' not found</h3>")

    df = df[["LAT", "LON", parameter]].dropna()

    RANGE_LIMITS = {
        "DIC": (1950, 2100),
        "MLD": (0, 100),
        "PCO2_ORIGINAL": (250, 550),
        "CHL": (5e-8, 4e-7),
        "NO3": (0.00, 0.06),
        "SSS": (30, 40),
        "SST": (20, 35),
        "DEVIANT_UNCERTAINTY": (0, 5)
    }

    vmin, vmax = RANGE_LIMITS.get(
        parameter,
        (df[parameter].min(), df[parameter].max())
    )

    fig = px.scatter_geo(
        df,
        lat="LAT", lon="LON",
        color=parameter,
        range_color=(vmin, vmax),
        hover_data={"LAT": True, "LON": True, parameter: True},
        color_continuous_scale="Viridis",
        projection="natural earth",
        title=f"{parameter} Bubble Map"
    )

    return HTMLResponse(fig.to_html(full_html=True))


# ===========================================================
# 3) SINGLE-PARAMETER LINE PLOT (DATE RANGE)
# ===========================================================

@router.get("/line", response_class=HTMLResponse)
def line_plot(
    parameter: str = Query(..., enum=PARAMETERS),
    start_date: str = None,
    end_date: str = None
):
    df = load_ocean_data()
    if df is None:
        return HTMLResponse("<h3>No ocean data</h3>")

    if "datetime" not in df.columns:
        return HTMLResponse("<h3>No datetime column found in DB</h3>")

    df = df.dropna(subset=["datetime"])

    if start_date:
        df = df[df["datetime"] >= pd.to_datetime(start_date)]

    if end_date:
        df = df[df["datetime"] <= pd.to_datetime(end_date)]

    if df.empty:
        return HTMLResponse("<h3>No records found for the given date range</h3>")

    fig = px.line(
        df,
        x="datetime",
        y=parameter,
        title=f"{parameter} over time",
        markers=True
    )
    return HTMLResponse(fig.to_html(full_html=True))


# ===========================================================
# 4) MULTIPLE PARAMETERS LINE PLOT
# ===========================================================

@router.get("/multi", response_class=HTMLResponse)
def multi_line_plot(
    params: str = Query(..., description="Comma separated, e.g. DIC,MLD,SST")
):
    df = load_ocean_data()
    if df is None:
        return HTMLResponse("<h3>No ocean data</h3>")

    if "datetime" not in df.columns:
        return HTMLResponse("<h3>No datetime column found in DB</h3>")

    selected = [p.strip() for p in params.split(",")]

    for p in selected:
        if p not in PARAMETERS:
            return HTMLResponse(f"<h3>Invalid parameter: {p}</h3>")

    df = df.dropna(subset=["datetime"])

    # Melt to long-form so Plotly can plot multiple lines
    melted = df.melt(id_vars="datetime", value_vars=selected,
                     var_name="Parameter", value_name="Value")

    fig = px.line(
        melted,
        x="datetime",
        y="Value",
        color="Parameter",
        title="Multi-Parameter Time Plot",
        markers=True
    )

    return HTMLResponse(fig.to_html(full_html=True))
