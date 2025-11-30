# THIS IS UPLOAD ENDPOINT FOR OCEAN/TAXONOMY DATASETS

from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd, io
from app.services.ocean_service import save_ocean_dataset
from app.services.taxonomy_service import save_taxonomy_dataset
from app.utils.column_standardizer import normalize_ocean_columns, normalize_taxonomy_columns

router = APIRouter(prefix="/upload", tags=["Dataset Upload"])


@router.post("/{dtype}")
async def upload_file(dtype: str, file: UploadFile = File(...)):
    if dtype not in ["ocean", "taxonomy"]:
        raise HTTPException(400, "Allowed types: ocean, taxonomy")

    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        raise HTTPException(400, "Upload CSV or Excel only.")

    file_bytes = await file.read()

    df = (
        pd.read_csv(io.BytesIO(file_bytes))
        if file.filename.endswith(".csv")
        else pd.read_excel(io.BytesIO(file_bytes))
    )

    # STEP 1 – clean column whitespaces
    df = df.rename(columns=lambda x: str(x).strip())

    # STEP 2 – normalize column names
    if dtype == "ocean":
        df = normalize_ocean_columns(df)
        count = save_ocean_dataset(df)

    elif dtype == "taxonomy":
        df = normalize_taxonomy_columns(df)
        count = save_taxonomy_dataset(df)

    return {
        "status": "success",
        "dataset_type": dtype,
        "rows_saved": count,
        "standardized_columns": list(df.columns)
    }
