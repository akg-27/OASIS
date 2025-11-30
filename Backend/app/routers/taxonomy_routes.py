# THIS FILE HAS TAXONOMY ENDPOINTS WHICH IS IMPORTED IN MAIN.PY

from fastapi import APIRouter
import pandas as pd
from app.services.db_reader_service import load_taxonomy_from_db
router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])


# ----------------------------
# HELPER: GET DATA FROM DB
# ----------------------------

def load_taxonomy():
    df = load_taxonomy_from_db()
    return df


# ---------------------------------------------------------
# 1) SHOW THE OVERALL LIST OF TAXONOMY DATABASE
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 2) FULL DETAILS OF SPECIES BY GIVING SCIENTIFIC NAME
# ---------------------------------------------------------

@router.get("/species/{name}")
def species_info(name: str):
    df = load_taxonomy()
    if df is None:
        return {"error": "No taxonomy data uploaded"}

    df["Scientific Name"] = df["Scientific Name"].astype(str)
    match = df[df["Scientific Name"].str.lower() == name.lower()]
    if match.empty:
        return {"error": "Species not found"}

    return match.to_dict(orient="records")[0]


# ---------------------------------------------------------
# 3) FILTER BY FAMILY, GENUS & ORDER
# ---------------------------------------------------------

@router.get("/filter")
def filter_taxonomy(
    family: str | None = None,
    genus: str | None = None,
    order: str | None = None
):
    df = load_taxonomy()
    if df is None:
        return {"error": "No taxonomy data uploaded"}

    for col in ["Family", "Genus", "Order"]:
        df[col] = df[col].astype(str).fillna("").str.lower()

    if family:
        df = df[df["Family"] == family.lower()]
    if genus:
        df = df[df["Genus"] == genus.lower()]
    if order:
        df = df[df["Order"] == order.lower()]

    clean_df = df.where(pd.notnull(df), None)
    return clean_df.to_dict(orient="records")
