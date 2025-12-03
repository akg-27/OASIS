# app/routers/ocean_routes.py
from fastapi import APIRouter, Query
import pandas as pd
import numpy as np
from app.database import supabase

router = APIRouter(prefix="/ocean", tags=["Ocean Visualization"])

PARAMETERS = [
    "dic", "mld", "pco2_original", "chl", "no3",
    "sss", "sst", "deviant_uncertainty"
]

UNITS = {
    "dic": "milimole/m3",
    "mld": "m",
    "pco2_original": "micro_atm",
    "chl": "kg/m3",
    "no3": "milimole/m3",
    "sss": "PSU",
    "sst": "deg C",
    "deviant_uncertainty": "micro atm"
}

# ---------------------------------------------------------------
# LOAD OCEAN DF
# ---------------------------------------------------------------
def load_ocean_df():
    rows = supabase.table("ocean_data").select("*").execute().data
    if not rows:
        return None

    df = pd.DataFrame(rows)

    for col in ["lat", "lon", "dic", "mld", "pco2_original",
                "chl", "no3", "sss", "sst", "deviant_uncertainty"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    return df


# ---------------------------------------------------------------
# 1) VALUE BY COORDINATE
# ---------------------------------------------------------------
@router.get("/get_value")
def get_value(
    lat: float,
    lon: float,
    parameter: str = Query(..., enum=PARAMETERS)
):
    df = load_ocean_df()
    if df is None:
        return {"error": "No ocean data found"}

    df = df.dropna(subset=["lat", "lon", parameter])

    df["dist"] = np.sqrt((df["lat"] - lat)**2 + (df["lon"] - lon)**2)
    nearest = df.iloc[df["dist"].idxmin()]

    return {
        "input_lat": lat,
        "input_lon": lon,
        "nearest_lat": float(nearest["lat"]),
        "nearest_lon": float(nearest["lon"]),
        "parameter": parameter,
        "value": float(nearest[parameter]),
        "unit": UNITS.get(parameter, "")
    }


# ---------------------------------------------------------------
# 2) BUBBLE MAP — JSON OUTPUT
# ---------------------------------------------------------------
@router.get("/map_json")
def bubble_map_json(parameter: str = Query(..., enum=PARAMETERS)):

    df = load_ocean_df()
    if df is None:
        return {"error": "No ocean data found"}

    df = df.dropna(subset=["lat", "lon", parameter])

    return {
        "parameter": parameter,
        "unit": UNITS.get(parameter, ""),
        "bounds": {
            "lat_min": float(df["lat"].min()),
            "lat_max": float(df["lat"].max()),
            "lon_min": float(df["lon"].min()),
            "lon_max": float(df["lon"].max())
        },
        "data": [
            {
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "value": float(row[parameter])
            }
            for _, row in df.iterrows()
        ]
    }


# ---------------------------------------------------------------
# 3) LINE CHART — JSON OUTPUT
# ---------------------------------------------------------------
@router.get("/line_json")
def line_chart_json(
    parameter: str = Query(..., enum=PARAMETERS),
    start_date: str = None,
    end_date: str = None
):
    df = load_ocean_df()
    if df is None:
        return {"error": "No ocean data found"}

    if "datetime" not in df.columns:
        return {"error": "No datetime column found"}

    df = df.dropna(subset=["datetime", parameter])

    if start_date:
        df = df[df["datetime"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["datetime"] <= pd.to_datetime(end_date)]

    df = df.sort_values("datetime")

    return {
        "parameter": parameter,
        "unit": UNITS.get(parameter, ""),
        "data": [
            {
                "date": row["datetime"].strftime("%Y-%m-%d"),
                "value": float(row[parameter])
            }
            for _, row in df.iterrows()
        ]
    }
