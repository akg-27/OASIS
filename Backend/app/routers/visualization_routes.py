from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import plotly.express as px
import os

router = APIRouter(prefix="/visualize", tags=["Visualization"])


# ===============================
# Load Latest Uploaded Ocean File
# ===============================
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
print("USING UPLOAD_DIR:", UPLOAD_DIR)



def load_ocean_data():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".csv")]
    if not files:
        return None
    latest = sorted(files)[-1]
    full_path = os.path.join(UPLOAD_DIR, latest)
    print("LOADING FILE:", full_path)
    return pd.read_csv(full_path)



# ============================
# LIST OF VALID PARAMETERS
# ============================
PARAMETERS = ["DIC", "MLD", "PCO2_ORIGINAL", "CHL", "NO3", "SSS", "SST", "DEVIANT_UNCERTAINTY"]

UNITS = {
    "DIC" : "milimole/m3",
    "MLD" : "m",
    "PCO2_ORIGINAL" : "micro_atm",
    "CHL" : "kg/m3",
    "NO3" : "milimole/m3",
    "SSS" : "PSU",
    "SST" : "deg C",
    "DEVIANT_UNCERTAINTY" : "micro atm"
}


# ================================
# Helper: Nearest Location Lookup
# ================================
def get_nearest_row(df, LAT, LON):
    df["dist"] = np.sqrt((df["LAT"] - LAT)**2 + (df["LON"] - LON)**2)
    nearest_index = df["dist"].idxmin()
    return df.iloc[nearest_index]


# ==================================================
# 1) GET VALUE BY LAT/LON + PARAMETER (JSON OUTPUT)
# ==================================================
@router.get("/get_value")
def get_value(
    LAT: float,
    LON: float,
    parameter: str = Query(..., enum=PARAMETERS)
):
    df = load_ocean_data()
    if df is None:
        return {"error": "No ocean file uploaded"}

    row = get_nearest_row(df, LAT, LON)
    value = row[parameter]
    unit = UNITS.get(parameter, "")

    return {
        "input_lat": LAT,
        "input_lon": LON,
        "nearest_data_lat": float(row["LAT"]),
        "nearest_data_lon": float(row["LON"]),
        "parameter": parameter,
        "value": float(value),
        "unit": unit
    }


# ============================================
# 2) BUBBLE MAP VISUALIZATION (HTML Plot)
# ============================================
@router.get("/map", response_class=HTMLResponse)
def generate_map(parameter: str = Query(..., enum=PARAMETERS)):

    df = load_ocean_data()
    if df is None:
        return HTMLResponse("<h3>No ocean data uploaded yet</h3>")

    sub_df = df[["LAT", "LON", parameter]].copy().dropna()

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

    vmin, vmax = RANGE_LIMITS.get(parameter, (sub_df[parameter].min(), sub_df[parameter].max()))

    fig = px.scatter_geo(
        sub_df,
        lon="LON",
        lat="LAT",
        color=parameter,
        hover_data={"LAT": True, "LON": True, parameter: True},
        color_continuous_scale="Viridis",
        range_color=(vmin, vmax),
        title=f"{parameter} ({UNITS.get(parameter, '')}) Bubble Map",
        projection="natural earth"
    )

    fig.update_geos(
        showcountries=True,
        showcoastlines=True,
        lonaxis_range=[df["LON"].min() - 2, df["LON"].max() + 2],
        lataxis_range=[df["LAT"].min() - 2, df["LAT"].max() + 2],
    )

    fig.update_coloraxes(colorbar_title=f"{parameter} ({UNITS.get(parameter, '')})")

    return HTMLResponse(fig.to_html(full_html=True))
