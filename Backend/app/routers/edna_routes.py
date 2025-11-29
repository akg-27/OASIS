# app/routers/edna_routes.py
from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from fastapi.responses import JSONResponse
from typing import Dict
import io

from app.services.edna_service import analyze_sequence_and_store, clean_sequence
from app.database import supabase

router = APIRouter(prefix="/edna", tags=["eDNA"])


@router.post("/analyze")
async def analyze_raw_sequence(payload: Dict):
    """
    POST JSON: { "sequence": "ATGCGT..." }
    Returns BLAST/taxonomy result and stores into Supabase.
    """
    if "sequence" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'sequence' in payload")
    seq = payload["sequence"]
    seq_clean = clean_sequence(seq)
    result = analyze_sequence_and_store(seq_clean)
    return JSONResponse(result)


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


@router.get("/{id}")
def get_result(id: str):
    res = supabase.table("edna_data").select("*").eq("id", id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Record not found")
    return res.data


@router.get("/history")
def history(limit: int = Query(50, gt=0, le=1000), offset: int = 0):
    res = supabase.table("edna_data").select("*").range(offset, offset + limit - 1).execute()
    return {"count": len(res.data or []), "data": res.data}
