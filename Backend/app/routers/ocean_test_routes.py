# --------------------------
# app/routers/ocean_heatmap_routes.py
# --------------------------
from fastapi import APIRouter, Query
from fastapi.responses import Response
import pandas as pd
import numpy as np
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from app.database import supabase

router = APIRouter(prefix="/ocean-heatmap", tags=["Heatmap Visualization"])

Y_PARAMETERS = [
    "dic", "mld", "pco2_original", "chl",
    "no3", "sss", "sst", "deviant_uncertainty"
]

# valid scientific ranges for cleaning
RANGE_LIMITS = {
    "dic": (1950, 2100),
    "mld": (0, 100),
    "pco2_original": (250, 550),
    "chl": (5e-8, 4e-7),
    "no3": (0.00, 0.06),
    "sss": (30, 40),
    "sst": (20, 35),
    "deviant_uncertainty": (0, 5)
}

def load_heatmap_data():
    res = supabase.table("ocean_data").select("*").execute()
    if not res.data:
        return None
    df = pd.DataFrame(res.data)

    # convert datetime safely
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


@router.get("/plot")
def heatmap_plot(
    param: str = Query(..., enum=Y_PARAMETERS)
):
    df = load_heatmap_data()
    if df is None:
        return {"error": "No ocean data available"}

    # --------------------------------------
    # STRICT FLATTEN & NUMERIC CONVERSION
    # --------------------------------------
    for col in ["lat", "lon", param]:
        df[col] = df[col].apply(lambda v: v[0] if isinstance(v, (list, tuple)) else v)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["lat", "lon", param])

    if df.empty:
        return {"error": "No valid lat/lon grid for heatmap"}

    # --------------------------------------
    # SCIENTIFIC VALID RANGE FILTER
    # --------------------------------------
    low, high = RANGE_LIMITS[param]
    df = df[(df[param] >= low) & (df[param] <= high)]

    if df.empty:
        return {"error": f"No valid scientific-range data for {param}"}

    # --------------------------------------
    # GRID BINNING (STABLE 2D HEATMAP)
    # --------------------------------------
    lat_bins = np.linspace(df["lat"].min(), df["lat"].max(), 70)
    lon_bins = np.linspace(df["lon"].min(), df["lon"].max(), 70)

    df["lat_bin"] = pd.cut(df["lat"], bins=lat_bins)
    df["lon_bin"] = pd.cut(df["lon"], bins=lon_bins)

    pivot = df.pivot_table(
        index="lat_bin",
        columns="lon_bin",
        values=param,
        aggfunc="mean"
    )

    # --------------------------------------
    # HEATMAP VISUALIZATION
    # --------------------------------------
    plt.figure(figsize=(12, 6))
    sns.heatmap(
        pivot,
        cmap="turbo",
        cbar_kws={"label": f"{param.upper()}"},
        robust=True
    )

    plt.title(f"{param.upper()} Spatial Heatmap", fontsize=14)
    plt.ylabel("Latitude Bins")
    plt.xlabel("Longitude Bins")

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=200)
    plt.close()
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")
