# THIS FILE HAS OTOLITH ENDPOINTS WHICH IS IMPORTED IN MAIN.PY

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from app.services.otolith_service import ingest_otolith_csv_bytes
from app.database import supabase

router = APIRouter(prefix="/otolith", tags=["Otolith"])


# ---------------------------------------------------------
# 1) FOR OTOLITH CSV FILE UPLOAD
# ---------------------------------------------------------

@router.post("/upload-csv")
async def upload_otolith_csv(file: UploadFile = File(...)):
    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    content = await file.read()
    result = ingest_otolith_csv_bytes(content)
    return JSONResponse({"status": "ok", "summary": result})


# ---------------------------------------------------------
# 2) SHOW THE OVERALL LIST OF OTOLITH DATABASE
# ---------------------------------------------------------

@router.get("/list")
def list_otoliths(limit: int = Query(1000, gt=0, le=10000), offset: int = 0):
    res = supabase.table("otolith_data").select("*").range(offset, offset + limit - 1).execute()
    return {"count": len(res.data or []), "data": res.data}


# ---------------------------------------------------------
# 3) GIVE UNLABELED DATA FROM ML (Required for ML)
# ---------------------------------------------------------

@router.get("/unlabeled")
def unlabeled(limit: int = Query(1000, gt=0, le=10000)):
    res = supabase.table("otolith_data").select("*").is_("label", None).limit(limit).execute()
    return {"count": len(res.data or []), "data": res.data}


# ---------------------------------------------------------
# 4) MANUALLY LABEL DATAFOR ML
# ---------------------------------------------------------

@router.post("/label")
def add_label(id: str = Query(...), label: str = Query(...)):
    check = supabase.table("otolith_data").select("id").eq("id", id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Otolith record not found")
    supabase.table("otolith_data").update({"label": label}).eq("id", id).execute()
    return {"status": "ok", "id": id, "label": label}


# ---------------------------------------------------------
# 5) SEARCH BY OTOLITH_ID
# ---------------------------------------------------------

@router.get("/by-otolithid")
def get_by_otolith_id(oid: str = Query(..., description="Original otolithID like CMLRE/OTL/00001")):
    """
    Fetch otolith record using the original dataset otolithID.
    Example:
    /otolith/by-otolithid?oid=CMLRE/OTL/00001
    """
    res = (
        supabase.table("otolith_data")
        .select("*")
        .eq("otolith_id", oid)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Otolith ID not found")

    return res.data[0]
