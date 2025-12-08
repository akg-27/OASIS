from fastapi import APIRouter, File, UploadFile, requests
from app.models.inference_retrieval import inference_retrieval
import shutil, uuid, os

router = APIRouter()
BASE_DIR = os.path.dirname(__file__)  # directory where inference file lives
UPLOAD_DIR = os.path.join(BASE_DIR, "temp_otolith_inputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/otolith/predict")
async def predict_otolith(file: UploadFile = File(...)):

    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise requests(status_code=400, detail="File must be an image")

    saved_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.jpg")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = inference_retrieval(saved_path)
    except Exception as e:
        raise requests(status_code=500, detail=str(e))

    os.remove(saved_path)

    return {"prediction": result}
