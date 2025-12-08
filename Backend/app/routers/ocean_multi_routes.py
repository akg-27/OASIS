# app/routers/ocean_overlay_routes.py

from fastapi import APIRouter, Query
from fastapi.responses import Response
import pandas as pd
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from app.database import supabase

router = APIRouter(prefix="/ocean-overlay", tags=["LAS Overlay"])

Y_PARAMETERS = [
    "dic", "mld", "pco2_original", "chl",
    "no3", "sss", "sst", "deviant_uncertainty"
]

X_OPTIONS = ["lat", "lon", "datetime"]

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


def load_overlay_data():
    res = supabase.table("ocean_data").select("*").execute()
    if not res.data:
        return None
    df = pd.DataFrame(res.data)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


@router.get("/multi")
def las_overlay(
    x: str = Query(..., enum=X_OPTIONS),
    y: list[str] = Query(...),
    start_date: str | None = None,
    end_date: str | None = None
):
    df = load_overlay_data()
    if df is None:
        return {"error": "No ocean data available"}

    invalid = [p for p in y if p not in Y_PARAMETERS]
    if invalid:
        return {"error": f"Invalid parameters: {invalid}"}

    if x == "datetime":
        if start_date:
            df = df[df["datetime"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["datetime"] <= pd.to_datetime(end_date)]

    df = df[[x] + y].dropna()
    if df.empty:
        return {"error": "No valid data for selected range"}

    # =====================================
    # LIMIT STATS CALCULATION TO FIRST 1000
    # (NO change in overlay visualization)
    # =====================================
    # ===============================
    # Filter only for stats (not plot)
    # ===============================
    stat_df = df.head(1000)  # limit first 1000 rows

    cleansed_stats = {}
    for param in y:
        low, high = RANGE_LIMITS.get(param, (None, None))

        valid = stat_df[(stat_df[param] >= low) & (stat_df[param] <= high)]

        cleansed_stats[param] = {
            "min": valid[param].min() if not valid.empty else None,
            "max": valid[param].max() if not valid.empty else None,
            "avg": valid[param].mean() if not valid.empty else None
        }

    # ===============================
    # LAS STYLE MULTI AXIS OVERLAY (unchanged)
    # ===============================
    plt.figure(figsize=(12, 6))
    ax = plt.gca()

    colors = sns.color_palette("tab10", len(y))
    ax.set_xlabel(x.upper())

    base = y[0]
    ax.plot(df[x], df[base], color=colors[0], linewidth=2, label=base.upper())
    ax.set_ylabel(base.upper(), color=colors[0])
    ax.set_ylim(RANGE_LIMITS[base])

    axes = [ax]

    for i, param in enumerate(y[1:], start=1):
        twin = ax.twinx()
        axes.append(twin)

        twin.spines["right"].set_position(("axes", 1 + 0.15 * i))
        twin.plot(df[x], df[param], color=colors[i], linewidth=2, label=param.upper())
        twin.set_ylabel(param.upper(), color=colors[i])
        twin.set_ylim(RANGE_LIMITS[param])

    ax.grid(True, linestyle="--", alpha=0.4)
    plt.title("LAS Style Multi-Parameter Overlay")

    # ==============================
    # Bottom legend (unchanged)
    # ==============================
    handles = []
    for ax_i in axes:
        h, _ = ax_i.get_legend_handles_labels()
        handles.extend(h)

    plt.legend(
        handles,
        [p.upper() for p in y],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.35),
        ncol=len(y),
        frameon=True,
    )

    # ==============================
    # STATS TEXT BELOW LEGEND (NEW)
    # using only first 1000 rows, no visual disruption
    # ==============================
    stats_text = "\n".join([
        f"{param.upper()} → Min: {v['min']:.3f} | Max: {v['max']:.3f} | Avg: {v['avg']:.3f}"
        if v['min'] is not None else f"{param.upper()} → No valid range data"
        for param, v in cleansed_stats.items()
    ])

    plt.text(
        0.5, -0.65,
        stats_text,
        ha="center",
        va="center",
        fontsize=10,
        color="#000",
        transform=plt.gca().transAxes,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffffff", edgecolor="#cccccc")
    )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=250, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")
