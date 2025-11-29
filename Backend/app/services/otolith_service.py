# app/services/otolith_service.py
import io
import csv
import time
import requests
from PIL import Image
from typing import Dict, Any, List
import pandas as pd

from app.utils.storage_service import upload_bytes_to_otolith_bucket
from app.database import supabase

# Config
DOWNLOAD_TIMEOUT = 15
DOWNLOAD_RETRY = 2
BATCH_INSERT_SIZE = 200

def _download_image(url: str, timeout: int = DOWNLOAD_TIMEOUT, retries: int = DOWNLOAD_RETRY) -> bytes | None:
    """Download image bytes with retry; return bytes or None."""
    if not url:
        return None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        time.sleep(0.5)
    return None

def _extract_image_metadata(image_bytes: bytes) -> Dict[str, Any]:
    """Return width, height, mode and size_bytes for given image bytes."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        mode = img.mode
        img.close()
        return {"width": width, "height": height, "mode": mode, "size_bytes": len(image_bytes)}
    except Exception:
        return {"width": None, "height": None, "mode": None, "size_bytes": len(image_bytes) if image_bytes else None}

def _row_to_otolith_record(row: Dict[str, Any], storage_path: str, public_url: str, image_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize CSV row to DB record dict."""
    return {
        "otolith_id": row.get("otolithID") or row.get("otolith_id") or None,
        "family": row.get("family") or None,
        "scientific_name": row.get("scientific_name") or row.get("scientificName") or None,
        "project_code": row.get("projectCode") or None,
        "station_id": row.get("stationID") or row.get("Station ID") or None,
        "locality": row.get("locality") or row.get("Locality") or None,
        "water_body": row.get("waterBody") or None,
        "original_image_url": row.get("image_url") or row.get("detail_url") or None,
        "storage_path": public_url or storage_path,
        "metadata": image_meta or None,
        "label": None
    }

def _insert_batch(batch: List[Dict[str, Any]]):
    """Insert a batch of records into otolith_data table."""
    if not batch:
        return
    cleaned = []
    for r in batch:
        cleaned_row = {k: (v if v != "" else None) for k, v in r.items()}
        cleaned.append(cleaned_row)
    supabase.table("otolith_data").insert(cleaned).execute()

def ingest_otolith_csv_bytes(csv_bytes: bytes) -> Dict[str, Any]:
    """
    Parse CSV bytes, download/upload images and insert rows to Supabase.
    Returns summary dict.
    """
    # Try pandas parse; fallback to csv parser
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes), dtype=str)
    except Exception:
        sio = io.StringIO(csv_bytes.decode(errors="ignore"))
        reader = csv.DictReader(sio)
        df = pd.DataFrame(list(reader))

    df = df.fillna("")
    total = len(df)
    succeeded = 0
    failed_rows = []
    batch = []

    for idx, row_series in df.iterrows():
        row = row_series.to_dict()
        image_url = row.get("image_url") or row.get("detail_url") or ""
        ext = (image_url.split(".")[-1].split("?")[0]) if "." in image_url else "jpg"
        orig_filename = (row.get("otolithID") or f"otolith_{idx}") + f".{ext}"

        image_bytes = _download_image(image_url) if image_url else None
        if image_bytes is None:
            failed_rows.append({"row_index": idx, "reason": "image_download_failed", "image_url": image_url})
            rec = _row_to_otolith_record(row, None, None, {"download_error": True, "original_url": image_url})
            batch.append(rec)
        else:
            meta = _extract_image_metadata(image_bytes)
            try:
                object_name, public_url = upload_bytes_to_otolith_bucket(orig_filename, image_bytes)
            except Exception as e:
                failed_rows.append({"row_index": idx, "reason": f"upload_failed: {str(e)}"})
                rec = _row_to_otolith_record(row, None, None, {"upload_error": True, "original_url": image_url})
                batch.append(rec)
            else:
                rec = _row_to_otolith_record(row, object_name, public_url, meta)
                succeeded += 1
                batch.append(rec)

        if len(batch) >= BATCH_INSERT_SIZE:
            _insert_batch(batch)
            batch = []

    if batch:
        _insert_batch(batch)

    return {"total": total, "succeeded": succeeded, "failed": len(failed_rows), "failures": failed_rows}
