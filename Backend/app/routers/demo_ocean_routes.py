from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase
from datetime import datetime

router = APIRouter(prefix="/ocean-entry", tags=["Ocean Data Entry"])


class OceanEntry(BaseModel):
    datetime: datetime
    lon: float
    lat: float
    dic: float | None = None
    mld: float | None = None
    pco2_original: float | None = None
    chl: float | None = None
    no3: float | None = None
    sss: float | None = None
    sst: float | None = None
    deviant_uncertainty: float | None = None
    station_id: str | None = None
    locality: str | None = None
    water_body: str | None = None


@router.post("/add")
def insert_ocean_data(entry: OceanEntry):
    payload = entry.dict()

    # 🔥 Fix datetime conversion
    if isinstance(payload["datetime"], datetime):
        payload["datetime"] = payload["datetime"].isoformat()

    try:
        res = supabase.table("oceandemo_data").insert(payload).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "inserted": res.data}
