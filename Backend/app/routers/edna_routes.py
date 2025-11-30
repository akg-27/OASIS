# THIS FILE HAS E-DNA ENDPOINTS WHICH IS IMPORTED IN MAIN.PY

from fastapi.responses import JSONResponse
from app.database import supabase
from fastapi import APIRouter, HTTPException, Body, File, UploadFile
from fastapi.responses import JSONResponse
from app.services.edna_service import (
    analyze_sequence_and_store,
    clean_sequence,
)

router = APIRouter(prefix="/edna", tags=["eDNA"])


# ---------------------------------------------------------
# 1) ANALYZE RAW DNA SEQUENCE (RAW TEXT)
# ---------------------------------------------------------

@router.post("/analyze")
async def analyze_raw_edna(
    raw_sequence: str = Body(..., media_type="text/plain", description="Raw DNA sequence (no JSON)")
):
    seq_text = raw_sequence.strip()

    if not seq_text:
        raise HTTPException(status_code=400, detail="Empty sequence")

    # Handle FASTA if present
    if seq_text.startswith(">"):
        lines = seq_text.splitlines()
        seq_text = "".join(lines[1:]).strip()

    result = analyze_sequence_and_store(seq_text)
    return JSONResponse(result)


# ---------------------------------------------------------
# 2) UPLOAD .FASTA FILE
# ---------------------------------------------------------

@router.post("/upload-fasta")
async def upload_fasta(file: UploadFile = File(...)):
    """
    Upload a FASTA file (single sequence expected). Returns analysis for the sequence(s).
    """
    contents = await file.read()
    text = contents.decode(errors="ignore")
    # crude parsing: remove headers and linebreaks
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith(">")]
    sequence = "".join(lines)
    seq_clean = clean_sequence(sequence)
    result = analyze_sequence_and_store(seq_clean)
    return JSONResponse(result)


# ---------------------------------------------------------
# 3) GET HISTORY STORED IN SUPABASE (latest to oldest)
# ---------------------------------------------------------

@router.get("/history")
def edna_history(limit: int = 20, offset: int = 0):
    """List past EDNA runs with pagination."""
    res = (
        supabase.table("edna_data")
        .select("*")
        .order("id", desc=True)  # latest first
        .limit(limit)
        .offset(offset)
        .execute()
    )

    if not res.data:
        return {"count": 0, "results": []}

    return {
        "count": len(res.data),
        "results": res.data
    }
