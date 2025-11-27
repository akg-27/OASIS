import uuid
from app.database import supabase

def save_uploaded_file(file, content: bytes) -> str:
    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"

    supabase.storage.from_("datasets").upload(unique_name, content)

    print("File uploaded to Supabase Storage:", unique_name)
    return unique_name
