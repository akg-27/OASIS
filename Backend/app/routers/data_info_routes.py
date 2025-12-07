from fastapi import APIRouter
from app.database import supabase

router = APIRouter(prefix="/data-info", tags=["Data Info"])


@router.post("/add")
def add_data_info(payload: dict):
    """
    Insert dataset metadata record into data_info table.
    """

    required = ["dataset_name", "dataset_domain"]
    for field in required:
        if field not in payload or not payload[field]:
            return {"status": "error", "detail": f"{field} is required"}

    row = {
        "dataset_name": payload.get("dataset_name"),
        "dataset_domain": payload.get("dataset_domain"),
        "dataset_link": payload.get("dataset_link"),
        "meta_data": payload.get("meta_data"),
        "curated_data": payload.get("curated_data"),
        "raw_data": payload.get("raw_data")
    }

    res = supabase.table("data_info").insert(row).execute()

    if not res.data:
        return {"status": "error", "detail": "Insert failed"}

    inserted_id = res.data[0]["id"]

    return {
        "status": "ok",
        "inserted_id": inserted_id,
        "dataset_name": payload.get("dataset_name")
    }
