from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import pandas as pd
import plotly.express as px
import os

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])

# ========= LOAD UPLOADED TAXONOMY CSV ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def load_taxonomy():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".csv")]
    if not files:
        return None
    # Latest uploaded
    latest = sorted(files)[-1]
    df = pd.read_csv(os.path.join(UPLOAD_DIR, latest))
    return df

# ============ 1) SPECIES LIST ===============
@router.get("/list")
def list_species():
    df = load_taxonomy()
    if df is None:
        return {"error": "No taxonomy data uploaded"}

    return {
        "species_count": df.shape[0],
        "species": df["Scientific Name"].dropna().unique().tolist(),
        "common_names": df["Common Name"].dropna().unique().tolist()
    }

# ============ 2) FULL DETAILS OF SPECIES ============
@router.get("/species/{name}")
def species_info(name: str):
    df = load_taxonomy()
    if df is None:
        return {"error": "No taxonomy data uploaded"}

    # Case-insensitive search
    df["Scientific Name"] = df["Scientific Name"].astype(str)
    match = df[df["Scientific Name"].str.lower() == name.lower()]
    if match.empty:
        return {"error": "Species not found"}

    return match.to_dict(orient="records")[0]

# ============ 3) FILTER BY FAMILY, GENUS, ORDER ============
@router.get("/filter")
def filter_taxonomy(
    family: str | None = None,
    genus: str | None = None,
    order: str | None = None
):
    df = load_taxonomy()
    if df is None:
        return {"error": "No taxonomy data uploaded"}

    # 🔽 Keep this EXACT block
    for col in ["Family", "Genus", "Order"]:
        df[col] = df[col].astype(str).fillna("").str.lower()

    # Filters become safe & case-insensitive
    if family:
        df = df[df["Family"] == family.lower()]
    if genus:
        df = df[df["Genus"] == genus.lower()]
    if order:
        df = df[df["Order"] == order.lower()]

    # Convert NaN to None to make JSON safe
    clean_df = df.where(pd.notnull(df), None)
    return clean_df.to_dict(orient="records")


# ============ 4) IUCN STATUS BAR CHART ============
@router.get("/iucn/stats", response_class=HTMLResponse)
def iucn_stats():
    df = load_taxonomy()
    if df is None:
        return "<h3>No taxonomy data uploaded</h3>"

    count = df["IUCN Status"].value_counts().reset_index()
    count.columns = ["IUCN Status", "Count"]

    fig = px.bar(count, x="IUCN Status", y="Count",
                 title="Conservation Status of Species",
                 color="IUCN Status",
                 template="plotly_dark")
    return HTMLResponse(fig.to_html(full_html=True))

# ============ 5) HABITAT PIE CHART ============
@router.get("/habitat/stats", response_class=HTMLResponse)
def habitat_stats():
    df = load_taxonomy()
    if df is None:
        return "<h3>No taxonomy data uploaded</h3>"

    count = df["Habitat Type"].value_counts().reset_index()
    count.columns = ["Habitat Type", "Count"]

    fig = px.pie(count, names="Habitat Type", values="Count",
                 title="Habitat Distribution",
                 template="plotly_dark")
    return HTMLResponse(fig.to_html(full_html=True))
