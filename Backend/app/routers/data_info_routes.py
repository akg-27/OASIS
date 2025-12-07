from fastapi import APIRouter
from app.database import supabase
from app.schemas.data_info_schema import DataInfoCreate

router = APIRouter(prefix="/data-info", tags=["Data Info"])


@router.post("/add")
def add_data_info(payload: DataInfoCreate):

    row = {
        "dataset_name": payload.dataset_name,
        "dataset_domain": payload.dataset_domain,
        "dataset_link": payload.dataset_link,
        "meta_data": payload.meta_data,
        "curated_data": payload.curated_data,
        "raw_data": payload.raw_data
    }

    res = supabase.table("data_info").insert(row).execute()

    if not res.data:
        return {"status": "error", "detail": "Insert failed"}

    return {
        "status": "ok",
        "inserted_id": res.data[0]["id"],
        "dataset_name": payload.dataset_name
    }
