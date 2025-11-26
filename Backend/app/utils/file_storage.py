import os
import uuid
from fastapi import UploadFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(file: UploadFile, content: bytes) -> str:
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, unique_name)

    with open(path, "wb") as f:
        f.write(content)

    print("\n=========== SAVED FILE ===========")
    print("FILE SAVED AT:", path)
    print("==================================\n")

    return path