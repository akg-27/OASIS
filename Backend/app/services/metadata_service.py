from datetime import datetime

# ==============================
#   METADATA EXTRACTOR
# ==============================

def extract_metadata(data, dtype):
    if dtype in ["ocean", "taxonomy"]:
        return {
            "type": dtype,
            "columns": list(data.columns),
            "records": len(data),
            "created_at": datetime.now()
        }

    if dtype == "otolith":
        return {
            "type": dtype,
            "info": "image file",
            "created_at": datetime.now()
        }

    if dtype == "edna":
        return {
            "type": dtype,
            "info": "dna sequence text",
            "created_at": datetime.now()
        }


# ==============================
#   TEMP SAVE (NO DATABASE MODE)
# ==============================

def save_metadata(meta):
    print("\n=== METADATA STORED (NO DB MODE) ===")
    for key, value in meta.items():
        print(f"{key}: {value}")
    print("=====================================\n")


# ==============================
#   ORIGINAL DB CODE (COMMENTED)
#   DO NOT DELETE (USE LATER)
# ==============================

# from app.database import SessionLocal
# from app.models.metadata_model import Metadata

# def save_metadata(meta):
#     db = SessionLocal()
#     record = Metadata(
#         dtype=meta["type"],
#         info=str(meta),
#         created_at=meta["created_at"]
#     )
#     db.add(record)
#     db.commit()
#     db.refresh(record)
#     db.close()
