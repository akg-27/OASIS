from fastapi import APIRouter, Query
from fastapi.responses import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import io
from enum import Enum
from app.database import supabase


router = APIRouter(prefix="/ocean-dist", tags=["Ocean Statistical Plots"])

Y_PARAMETERS = [
    "dic", "mld", "pco2_original", "chl",
    "no3", "sss", "sst", "deviant_uncertainty"
]

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

LOG_ALLOWED = ["chl", "no3"]


class DistPlot(str, Enum):
    violin = "violin"
    box = "box"
    corr = "corr"
    scatter_matrix = "scatter_matrix"
    relation = "relation"


def load_ocean_data():
    res = supabase.table("ocean_data").select("*").execute()
    if not res.data:
        return None
    
    df = pd.DataFrame(res.data)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


@router.get("/plot")
def ocean_stats_plot(
    plot: DistPlot = Query(...),
    y: list[str] = Query(None)
):
    df = load_ocean_data()
    if df is None:
        return {"error": "No data found"}

    # keep only numeric parameters
    core = df[Y_PARAMETERS].apply(pd.to_numeric, errors="coerce").dropna()

    # remove cosmic junk from DIC etc
    core = core[(core > -1e10).all(axis=1)]

    # trim outliers
    core = core[(core >= core.quantile(0.01)) & (core <= core.quantile(0.99))]

    sns.set_style("whitegrid")

    # ==========================================================
    # 1️⃣ VIOLIN & BOX: requires single parameter
    # ==========================================================
    if plot in ["violin", "box"]:
        if not y or len(y) != 1:
            return {"error": "Select exactly 1 parameter for violin/box"}

        param = y[0]
        if param not in Y_PARAMETERS:
            return {"error": f"Invalid param {param}"}

        fig, ax = plt.subplots(figsize=(7, 5), dpi=240)

        if plot == "violin":
            sns.violinplot(y=core[param], inner="quartile", ax=ax, color="#0077B6")
            title = f"Violin Distribution of {param.upper()}"
        else:
            sns.boxplot(y=core[param], ax=ax, color="#6A4C93", fliersize=2)
            title = f"Box Spread of {param.upper()}"

        ax.set_title(title)
        ymin, ymax = RANGE_LIMITS[param]
        ax.set_ylim(ymin, ymax)

    # ==========================================================
    # 2️⃣ CORRELATION HEATMAP (all params)
    # ==========================================================
    elif plot == "corr":
        fig, ax = plt.subplots(figsize=(9, 7), dpi=240)
        corr = core.corr()
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        ax.set_title("Parameter Correlation Matrix Heatmap")

    # ==========================================================
    # 3️⃣ SCATTER MATRIX (pairplot style)
    # ==========================================================
    elif plot == "scatter_matrix":
        g = sns.pairplot(core, diag_kind="hist", plot_kws={"alpha": 0.6, "s": 35})
        buf = io.BytesIO()
        g.fig.savefig(buf, format="png", dpi=230)
        plt.close()
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")

    # ==========================================================
    # 4️⃣ RELATION SCATTERS (multi param relation grid)
    # ==========================================================
    elif plot == "relation":
        if not y or len(y) < 2:
            return {"error": "Select at least 2 parameters for relation grid"}

        sel = core[y]
        sns.set(font_scale=0.8)
        g = sns.pairplot(sel, kind="scatter", diag_kind="kde", plot_kws={"s": 30})
        buf = io.BytesIO()
        g.fig.savefig(buf, format="png", dpi=230)
        plt.close()
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/png")


    # ====================
    # Return Non-pair PNG
    # ====================
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=240)
    plt.close()
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")
