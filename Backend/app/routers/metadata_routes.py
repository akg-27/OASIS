from fastapi import APIRouter, requests
from app.database import supabase

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.get("/latest/{dtype}")
def get_latest_by_type(dtype: str):
    """Return the latest metadata for ocean | taxonomy | otolith"""
    res = (
        supabase.table("dataset_metadata")
        .select("*")
        .eq("dataset_type", dtype)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise requests.get(404, f"No metadata found for type '{dtype}'")

    return res.data[0]


@router.get("/types")
def list_dataset_types():
    """List all dataset types present in metadata table."""
    res = supabase.table("dataset_metadata").select("dataset_type").execute()
    types = sorted({r["dataset_type"] for r in res.data})
    return {"dataset_types": types}
