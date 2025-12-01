# app/routers/taxonomy_routes.py

from fastapi import APIRouter, Query, requests
from app.database import supabase

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
