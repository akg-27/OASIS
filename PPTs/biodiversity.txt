# app/routers/biodiversity_routes.py

from fastapi import APIRouter, Query
from fastapi.responses import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
from enum import Enum
from app.database import supabase

router = APIRouter(prefix="/biodiversity", tags=["Biodiversity Plots"])


# =========================
# Enum for Swagger Dropdown
# =========================
class PlotType(str, Enum):
    richness_heatmap = "richness_heatmap"
    family_composition = "family_composition"
    rank_abundance = "rank_abundance"
    locality_diversity = "locality_diversity"


def load_oto_data():
    res = supabase.table("otolith_data").select("*").execute()
    if not res.data:
        return None
    return pd.DataFrame(res.data)


@router.get("/plots")
def biodiversity_plots(plot: PlotType):
    df = load_oto_data()
    if df is None:
        return {"error": "No Otolith biodiversity data found"}

    required = ["scientific_name", "family", "locality", "lat", "lon"]
    df = df[required].dropna()

    if df.empty:
        return {"error": "Dataset empty or missing required fields"}

    plt.figure(figsize=(10, 6), dpi=200)
    sns.set_style("whitegrid")

    if plot == PlotType.richness_heatmap:
        pivot = df.pivot_table(
            index="lat",
            columns="lon",
            values="scientific_name",
            aggfunc="nunique"
        )
        sns.heatmap(pivot, cmap="viridis")
        plt.title("Species Richness Heatmap (Lat vs Lon)")

    elif plot == PlotType.family_composition:
        fam_counts = df["family"].value_counts()
        plt.pie(
            fam_counts.values,
            labels=fam_counts.index,
            autopct="%1.1f%%",
            startangle=90
        )
        plt.title("Family Composition (%)")

    elif plot == PlotType.rank_abundance:
        counts = df["scientific_name"].value_counts()
        plt.plot(range(1, len(counts) + 1), counts.values, marker="o")
        plt.yscale("log")
        plt.xlabel("Species Rank")
        plt.ylabel("Abundance (Log Scale)")
        plt.title("Rank-Abundance (Dominance vs Rarity)")

    elif plot == PlotType.locality_diversity:
        richness = df.groupby("locality")["scientific_name"].nunique()
        richness.sort_values(ascending=False).plot(kind="bar", color="#4B8BBE")
        plt.ylabel("Unique Species Count")
        plt.title("Species Richness per Locality")


    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=220)
    plt.close()
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")
