# app/utils/taxonomy_cleaner.py
import pandas as pd

# Canonical columns we will keep (final DB column names)
CANONICAL_COLS = [
    "lat", "lon",
    "family", "genus", "kingdom", "phylum",
    "scientific_name", "species",
    "subclass", "subfamily", "suborder", "subphylum",
    "superclass", "superfamily", "superorder", "locality"
]

# Map common raw names to canonical names
TAXONOMY_MAP = {
    "decimalLatitude": "lat",
    "decimal_latitude": "lat",
    "latitude": "lat",

    "decimalLongitude": "lon",
    "decimal_longitude": "lon",
    "longitude": "lon",

    "family": "family",
    "genus": "genus",
    "kingdom": "kingdom",
    "phylum": "phylum",

    # scientific name variations
    "scientificName": "scientific_name",
    "Scientific Name": "scientific_name",
    "scientific_name": "scientific_name",

    "species": "species",

    # sub / super / suborder etc variations (case/space tolerant)
    "subclass": "subclass",
    "subfamily": "subfamily",
    "suborder": "suborder",
    "subphylum": "subphylum",
    "superclass": "superclass",
    "superfamily": "superfamily",
    "superorder": "superorder",

    #Location
    "locality" : "locality",
}

# Utility: normalize one dataframe
def clean_taxonomy_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes column names, keeps only CANONICAL_COLS, and
    ensures empty strings/NaN are turned into None.
    """
    # Create copy to avoid side effects
    df = df.copy()

    # Build rename dict by checking existing columns against TAXONOMY_MAP keys (case-sensitive and case-insensitive)
    rename_map = {}
    for col in df.columns:
        if col in TAXONOMY_MAP:
            rename_map[col] = TAXONOMY_MAP[col]
        else:
            # try case-insensitive match
            low = col.strip().lower()
            for k in TAXONOMY_MAP:
                if k.strip().lower() == low:
                    rename_map[col] = TAXONOMY_MAP[k]
                    break

    if rename_map:
        df = df.rename(columns=rename_map)

    # After renaming, keep only canonical columns
    keep = [c for c in CANONICAL_COLS if c in df.columns]
    # If some canonical columns are missing, create them with None values
    for c in CANONICAL_COLS:
        if c not in df.columns:
            df[c] = None

    df = df[CANONICAL_COLS]  # preserve canonical order

    # Clean values: strip strings and convert empty -> None
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().replace({"nan": None, "": None})
        else:
            # try convert numeric lat/lon to floats but keep None if conversion fails
            if col in ("lat", "lon"):
                def to_float_safe(x):
                    try:
                        if x is None or (isinstance(x, float) and pd.isna(x)):
                            return None
                        return float(x)
                    except Exception:
                        return None
                df[col] = df[col].apply(to_float_safe)
            else:
                # for other non-object columns, replace pandas NA with None
                df[col] = df[col].where(pd.notnull(df[col]), None)

    # Final normalization of empty strings -> None
    df = df.where(pd.notnull(df), None)

    return df
