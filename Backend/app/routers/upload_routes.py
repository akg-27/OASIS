from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd, io

from app.utils.file_storage import save_uploaded_file
from app.services.ingestion_service import detect_dataset_type
from app.services.metadata_service import extract_metadata, save_metadata
from app.services.taxonomy_service import save_taxonomy_dataset
from app.services.ocean_service import save_ocean_dataset

router = APIRouter(prefix="/upload", tags=["Dataset Upload"])

@router.post("/{dtype}")
async def upload_file(dtype: str, file: UploadFile = File(...)):
    allowed = ["ocean", "taxonomy"]
    if dtype not in allowed:
        raise HTTPException(400, "Only ocean & taxonomy allowed for now")

    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(400, "Upload CSV or Excel only")

    file_bytes = await file.read()
    df = pd.read_csv(io.BytesIO(file_bytes)) if file.filename.endswith(".csv") else pd.read_excel(io.BytesIO(file_bytes))

    detected_type = detect_dataset_type(df)
    saved_path = save_uploaded_file(file, file_bytes)

    metadata = extract_metadata(df, detected_type)
    metadata["file_path"] = saved_path
    save_metadata(metadata)

    if detected_type == "taxonomy":
        save_taxonomy_dataset(df)
    if detected_type == "ocean":
        save_ocean_dataset(df)

    return {"msg": "Uploaded", "type": detected_type, "file_path": saved_path, "metadata": metadata}
