# app/utils/storage_service.py
from app.database import supabase
from typing import Tuple

OTOLITH_BUCKET = "otolith"

def _object_exists(object_name: str) -> bool:
    """
    Check if a file with this object_name already exists in Supabase Storage.
    """
    try:
        res = supabase.storage.from_(OTOLITH_BUCKET).list(path="otolith")
        if isinstance(res, list):
            return any(obj.get("name") == object_name.split("/")[-1] for obj in res)
        return False
    except Exception:
        return False


def upload_bytes_to_otolith_bucket(object_name: str, content: bytes) -> Tuple[str, str]:
    """
    Upload raw bytes to Supabase storage under 'otolith' bucket.
    Automatically handles duplicate filenames by appending _1, _2, ...
    """
    base_name = object_name
    counter = 1

    # If name exists, append suffix
    while _object_exists(base_name):
        name, ext = object_name.rsplit(".", 1)
        base_name = f"{name}_{counter}.{ext}"
        counter += 1

    # Upload final unique name
    supabase.storage.from_(OTOLITH_BUCKET).upload(base_name, content)

    # Public URL
    public = supabase.storage.from_(OTOLITH_BUCKET).get_public_url(base_name)

    if isinstance(public, dict):
        public_url = public.get("publicURL") or public.get("public_url") or str(public)
    else:
        public_url = str(public)

    return base_name, public_url
