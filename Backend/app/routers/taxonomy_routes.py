# app/routers/taxonomy_routes.py
from fastapi import APIRouter, Query, requests
from app.database import supabase
import plotly.express as px
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])


# ---------------------------------------------------------
# 1) LIST TAXONOMY (uses Supabase directly)
# ---------------------------------------------------------

@router.get("/list")
def list_species(limit: int = Query(1000, gt=1, le=10000), offset: int = 0):
    res = (
        supabase.table("taxonomy_data")
        .select("*")
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "count": len(res.data or []),
        "data": res.data or []
    }


# ---------------------------------------------------------
# 2) GET SPECIES DETAILS (case-insensitive)
# ---------------------------------------------------------
@router.get("/species/{name}")
def species_info(name: str):

    # Query in lowercase for case-insensitive matching
    res = (
        supabase.table("taxonomy_data")
        .select("*")
        .execute()
    )

    if not res.data:
        raise requests.get(status_code=404, detail="No taxonomy data uploaded")

    # Manual filtering (Supabase does not support ILIKE on JSON columns)
    name_lower = name.lower()

    for row in res.data:
        sci = row.get("scientific_name")
        if sci and sci.lower() == name_lower:
            return row

    raise requests.get(status_code=404, detail="Species not found")


# ---------------------------------------------------------
# 3) FILTER TAXONOMY BY FAMILY, GENUS, ORDER
# ---------------------------------------------------------
@router.get("/filter")
def filter_taxonomy(
    family: str | None = None,
    genus: str | None = None,
    order: str | None = None
):
    # Load all rows (efficient for filtering)
    res = supabase.table("taxonomy_data").select("*").execute()
    if not res.data:
        return []

    rows = res.data
    filtered = []

    # Normalize request filters
    fam = family.lower() if family else None
    gen = genus.lower() if genus else None
    ord_ = order.lower() if order else None

    for row in rows:
        rfam = (row.get("family") or "").lower()
        rgen = (row.get("genus") or "").lower()
        rord = (row.get("order") or "").lower()

        if fam and rfam != fam:
            continue
        if gen and rgen != gen:
            continue
        if ord_ and rord != ord_:
            continue

        filtered.append(row)

    return filtered


@router.get("/map", response_class=HTMLResponse)
def taxonomy_species_map(family: str = Query(..., description="Exact family name")):
    
    # ------------------------------------
    # 1. Fetch points by FAMILY
    # ------------------------------------
    res = (
        supabase.table("taxonomy_data")
        .select(
            "lat, lon, family, genus, kingdom, phylum, scientific_name, species", "locality"
        )
        .eq("family", family)
        .execute()
    )

    if not res.data:
        return HTMLResponse(f"<h3>No records found for family: {family}</h3>", status_code=404)

    # ------------------------------------
    # 2. Filter valid lat/lon entries
    # ------------------------------------
    data = [row for row in res.data if row.get("lat") and row.get("lon")]

    if not data:
        return HTMLResponse(f"<h3>No valid lat/lon entries for family: {family}</h3>", status_code=404)

    # ------------------------------------
    # 3. Bubble Map
    # ------------------------------------
    import pandas as pd
    df = pd.DataFrame(data)

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        hover_data=[
            "lat", "lon",
            "family", "genus", "kingdom", "phylum",
            "scientific_name", "species", "locality"
        ],
        color="scientific_name",
        size_max=10,
        title=f"Distribution Map (Family): {family}"
    )

    # ------------------------------------
    # 4. Indian Region Focus
    # ------------------------------------
    fig.update_geos(
        showcountries=True,
        showcoastlines=True,
        landcolor="lightgray",
        oceancolor="lightblue",
        projection=dict(type="natural earth"),
        lataxis_range=[5, 35],
        lonaxis_range=[60, 100],
    )

    fig.update_layout(
        height=650,
        template="plotly_dark",
        margin={"r":10, "t":40, "l":10, "b":10}
    )

    return HTMLResponse(fig.to_html(full_html=True))