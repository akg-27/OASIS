# UPLOAD ROUTE FOR OCEAN , TAXONOMY & OTOLITH
from fastapi import APIRouter, UploadFile, File,Query
from app.services.metadata_service import extract_metadata, save_metadata
from app.utils.column_standardizer import standardize_df
from app.utils.taxonomy_cleaner import clean_taxonomy_df
from app.database import supabase
import pandas as pd
import io
import os
import requests
from datetime import datetime


router = APIRouter(prefix="/upload", tags=["Dataset Upload"])

# helper: chunk insert
def chunked_insert(table_name, rows, chunk_size=2000):
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i+chunk_size]
        supabase.table(table_name).insert(chunk).execute()

# helper: upload file bytes to Supabase storage (otolith images)
def upload_image_to_supabase(bucket_name, path, content_bytes):
    # supabase-python storage upload API differs by versions. Common usage:
    # supabase.storage.from_(bucket_name).upload(path, content_bytes)
    # Use the client you have in app.database — adapt if method differs.
    try:
        res = supabase.storage.from_(bucket_name).upload(path, content_bytes)
        return res
    except Exception as e:
        # fallback: some clients expect file-like
        try:
            res = supabase.storage.from_(bucket_name).upload(path, io.BytesIO(content_bytes))
            return res
        except Exception as e2:
            raise

@router.post("/")
async def upload_file(dtype: str = Query(..., description="ocean | taxonomy | otolith"), file: UploadFile = File(...)):
    if dtype not in ["ocean", "taxonomy", "otolith"]:
        raise requests.get(status_code=400, detail="dtype must be ocean, taxonomy, or otolith")

    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx")):
        return{"status":"Upload CSV or Excel file only"}

    file_bytes = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(file_bytes)) if file.filename.endswith(".csv") else pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        return {"status": "error", "detail": f"Could not parse file: {e}"}


    # standardize columns
    df = standardize_df(df, dtype)

    # fill NaN -> None
    df = df.where(pd.notnull(df), None)

    df = df.where(pd.notnull(df), None)

    # ---- SAVE METADATA ----
    meta = extract_metadata(df, dtype)
    save_metadata(meta)
    # ------------------------


    # ============================================================
    # OCEAN DATA UPLOAD (FINAL — CLEAN & WORKING)
    # ============================================================

    from datetime import datetime

    def smart_parse_date(x):
        """Handles Excel float dates, dd-mm-yyyy, dd-Mon-yy."""
        if x is None or pd.isna(x):
            return None

        # A) Excel numeric serial date (float/int)
        if isinstance(x, (int, float)):
            try:
                return pd.Timestamp("1899-12-30") + pd.to_timedelta(int(x), "D")
            except:
                pass

        # B) dd-mm-yyyy
        try:
            return datetime.strptime(str(x), "%d-%m-%Y")
        except:
            pass

        # C) dd-Mon-yy (29-Jan-19)
        try:
            return datetime.strptime(str(x), "%d-%b-%y")
        except:
            pass

        # D) Pandas autodetect
        try:
            return pd.to_datetime(str(x), errors="coerce")
        except:
            return None


    if dtype == "ocean":

        allowed = [
            "datetime", "lon", "lat", "dic", "mld",
            "pco2_original", "chl", "no3", "sss", "sst",
            "deviant_uncertainty", "station_id", "locality", "water_body"
        ]

        # ------------ PARSE DATETIME -----------------
        if "datetime" in df.columns:
            df["datetime"] = df["datetime"].apply(smart_parse_date)
        else:
            df["datetime"] = None

        # ------------ BUILD ROWS -----------------
        rows = []
        for _, r in df.iterrows():
            row = {k: r.get(k) for k in allowed}

            # datetime → ISO format
            dt = row.get("datetime")
            if isinstance(dt, (pd.Timestamp, datetime)):
                row["datetime"] = dt.strftime("%Y-%m-%d")
            else:
                row["datetime"] = None

            # numeric fixes
            numeric_cols = [
                "lon", "lat", "dic", "mld", "pco2_original",
                "chl", "no3", "sss", "sst", "deviant_uncertainty"
            ]
            for col in numeric_cols:
                if row.get(col) is not None:
                    try:
                        row[col] = float(row[col])
                    except:
                        row[col] = None

            rows.append(row)

        # ------------ INSERT INTO SUPABASE -----------------
        if rows:
            chunked_insert("ocean_data", rows)

        return {"status": "ok", "saved_rows": len(rows)}




        # === TAXONOMY INSERT BLOCK (replace current taxonomy branch) ===
    elif dtype == "taxonomy":
        # light-weight parser: ensure we read strings, then clean
        try:
            cleaned_df = clean_taxonomy_df(df)
        except Exception as e:
            raise requests.get(status_code=500, detail=f"Taxonomy cleaning failed: {e}")

        
        rows = cleaned_df.where(pd.notnull(cleaned_df), None).to_dict(orient="records")

        if rows:
            chunked_insert("taxonomy_data", rows)

        return {"status": "ok", "saved_rows": len(rows)}


    else :  
        bucket = os.getenv("SUPABASE_BUCKET_OTOLITH", "Otolith")
        rows = []

        for _, r in df.iterrows():

            # -------------------------
            # SAFE VALUE EXTRACTOR
            # -------------------------
            def val(col):
                if col not in r:
                    return None

                v = r[col]

                # Fix: if duplicate column names → Pandas Series
                if isinstance(v, pd.Series):
                    v = v.iloc[0]

                if pd.isna(v):
                    return None
                return v

            # -------------------------
            # BUILD CLEAN ROW
            # -------------------------
            row = {
                "otolith_id": val("otolith_id") or val("otolithID") or val("otolithId"),
                "family": val("family"),
                "scientific_name": val("scientific_name") or val("scientificName"),
                "project_code": val("project_code") or val("projectCode"),
                "station_id": val("station_id") or val("stationID"),
                "locality": val("locality"),
                "water_body": val("water_body") or val("waterBody"),
                "original_image_url": val("original_image_url") or val("image_url") or val("imageUrl"),
                "storage_path": None,
                "sex": val("Sex"),
                "life_stage": val("Life stage"),
                "habitat": val("Habitat"),
                "platform": val("Platform"),
                "collection_method": val("Collection Method"),
                "submitted_by": val("submittedBy") or val("submitted_by"),
                "lat": None,
                "lon": None,
                "collection_depth_m": None,
                "station_depth_m": None
            }

            # -------------------------
            # SAFE LAT / LON
            # -------------------------
            lt = val("lat") or val("decimalLatitude") or val("decimal_latitude")
            ln = val("lon") or val("decimalLongitude") or val("decimal_longitude")

            try:
                row["lat"] = float(lt) if lt is not None else None
            except:
                row["lat"] = None

            try:
                row["lon"] = float(ln) if ln is not None else None
            except:
                row["lon"] = None

            # -------------------------
            # DEPTH PARSE
            # -------------------------
            cd_m = val("collection_depth_m") or val("Collection Depth (in mts)")
            try:
                row["collection_depth_m"] = float(cd_m) if cd_m is not None else None
            except:
                row["collection_depth_m"] = None

            sd_m = val("station_depth_m") or val("Station Depth (in mts)")
            try:
                row["station_depth_m"] = float(sd_m) if sd_m is not None else None
            except:
                row["station_depth_m"] = None

            # -------------------------
            # IMAGE DOWNLOAD + SUPABASE UPLOAD
            # -------------------------
            img_url = row["original_image_url"]

            if img_url:
                try:
                    resp = requests.get(img_url, timeout=12)
                    if resp.status_code == 200:

                        # extension
                        ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"

                        # safe filename (replace slashes)
                        safe_oid = (
                            row["otolith_id"].replace("/", "_")
                            if row["otolith_id"]
                            else os.urandom(8).hex()
                        )

                        storage_key = f"{safe_oid}{ext}"

                        # Upload
                        supabase.storage.from_(bucket).upload(
                            storage_key,
                            resp.content,
                        )

                        # public path
                        row["storage_path"] = (
                            f"{os.getenv('SUPABASE_URL').rstrip('/')}"
                            f"/storage/v1/object/public/{bucket}/{storage_key}"
                        )

                except Exception:
                    row["storage_path"] = None

            rows.append(row)

        # -------------------------
        # BULK INSERT INTO SUPABASE
        # -------------------------
        if rows:
            chunked_insert("otolith_data", rows)

        return {"status": "ok", "saved_rows": len(rows)}

