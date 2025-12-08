# app/routers/biodiversity_routes.py

from fastapi import APIRouter, Query
from fastapi.responses import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import io
from enum import Enum
from app.database import supabase

router = APIRouter(prefix="/biodiversity", tags=["Biodiversity Diversity Metrics"])


# =========================
# Enum for Dropdown
# =========================
class DiversityPlot(str, Enum):
    shannon_index = "shannon_index"
    simpson_dominance = "simpson_dominance"
    evenness_scatter = "evenness_scatter"
    diversity_rank = "diversity_rank"


def load_oto_data():
    res = supabase.table("otolith_data").select("*").execute()
    if not res.data:
        return None
    return pd.DataFrame(res.data)


@router.get("/indices")
def diversity_indices(plot: DiversityPlot):
    df = load_oto_data()
    if df is None:
        return {"error": "No Otolith biodiversity data found"}

    df = df[["scientific_name", "locality"]].dropna()
    if df.empty:
        return {"error": "Dataset missing required fields"}

    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6), dpi=200)

    # =======================
    # SAFE Diversity Calculation
    # =======================
    counts = df.groupby(["locality", "scientific_name"]).size().reset_index(name="n")

    # transform ensures perfect index alignment (fix)
    loc_totals = counts.groupby("locality")["n"].transform("sum")
    counts["p"] = counts["n"] / loc_totals

    # Shannon
    counts["H"] = -(counts["p"] * np.log(counts["p"]))
    shannon = counts.groupby("locality")["H"].sum()

    # Simpson Dominance
    counts["p2"] = counts["p"] ** 2
    simpson = counts.groupby("locality")["p2"].sum()

    # Evenness
    richness = counts.groupby("locality")["scientific_name"].nunique()
    evenness = shannon / np.log(richness)

    # ===========================
    # 1️⃣ Shannon Diversity Index
    # ===========================
    if plot == DiversityPlot.shannon_index:
        shannon.sort_values(ascending=False).plot(kind="bar", color="#0077B6")
        plt.ylabel("H' (Shannon)")
        plt.title("Shannon Diversity Index by Locality")

    # ===========================
    # 2️⃣ Simpson Dominance Curve
    # ===========================
    elif plot == DiversityPlot.simpson_dominance:
        simpson.sort_values(ascending=True).plot(kind="bar", color="#D62828")
        plt.ylabel("Dominance (D)")
        plt.title("Simpson Dominance (Higher = Few Species Dominate)")

    # ===========================
    # 3️⃣ Evenness Scatter
    # ===========================
    elif plot == DiversityPlot.evenness_scatter:
        plt.scatter(richness, shannon, c=evenness, cmap="viridis", s=120, edgecolor="black")

        for loc in richness.index:
            plt.text(richness[loc], shannon[loc], loc, fontsize=8)

        plt.xlabel("Species Richness (S)")
        plt.ylabel("Shannon Index (H')")
        plt.title("Evenness vs Richness (Color = Evenness)")
        cbar = plt.colorbar()
        cbar.set_label("Evenness (J)")

    # ===========================
    # 4️⃣ Diversity Rank Curve
    # ===========================
    elif plot == DiversityPlot.diversity_rank:
        overall = df["scientific_name"].value_counts()
        plt.plot(range(1, len(overall) + 1), overall.values, marker="o", color="#6A4C93")
        plt.yscale("log")
        plt.xlabel("Species Rank")
        plt.ylabel("Abundance (log)")
        plt.title("Global Diversity Rank-Abundance Curve")

    # ===========================
    # Return Plot
    # ===========================
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=220)
    plt.close()
    buf.seek(0)

    return Response(content=buf.getvalue(), media_type="image/png")
