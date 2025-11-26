from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io

from app.services.ingestion_service import detect_dataset_type
from app.services.metadata_service import extract_metadata, save_metadata
from app.utils.file_storage import save_uploaded_file   # <-- VERY IMPORTANT

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/{dtype}")
async def upload_file(dtype: str, file: UploadFile = File(...)):
    allowed = ["ocean", "taxonomy", "otolith", "edna"]
    if dtype not in allowed:
        raise HTTPException(status_code=400, detail="Invalid dataset type")

    # CSV / EXCEL
    if dtype in ["ocean", "taxonomy"]:
        if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
            raise HTTPException(400, "Expected CSV or Excel file")

        # 📌 Read file ONCE
        file_bytes = await file.read()

        # 📌 Load into pandas using Bytes
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        # 📌 Detect type
        detected_type = detect_dataset_type(df)

        # 📌 Save file physically
        saved_path = save_uploaded_file(file, file_bytes)

        # 📌 Build metadata
        metadata = extract_metadata(df, detected_type)
        metadata["file_path"] = saved_path

        save_metadata(metadata)  # Only prints for now

        return {
            "msg": "File uploaded successfully",
            "type": detected_type,
            "metadata": metadata
        }

    # IMAGE (Otolith)
    if dtype == "otolith":
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(400, "Expected image file")

        file_bytes = await file.read()
        saved_path = save_uploaded_file(file, file_bytes)

        metadata = extract_metadata(None, dtype)
        metadata["file_path"] = saved_path
        save_metadata(metadata)

        return {"msg": "Otolith image received", "metadata": metadata}

    # DNA Sequence (eDNA)
    if dtype == "edna":
        if file.content_type not in ["text/plain"]:
            raise HTTPException(400, "Expected text file")

        file_bytes = await file.read()
        text_data = file_bytes.decode()
        saved_path = save_uploaded_file(file, file_bytes)

        metadata = extract_metadata(text_data, dtype)
        metadata["file_path"] = saved_path
        save_metadata(metadata)

        return {"msg": "eDNA text received", "metadata": metadata}
