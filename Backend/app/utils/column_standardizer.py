# COLUMN STANDARDIZER WHICH GIVES SAME COLUMN NAMES FOR ALL OCEAN AND TAXONOMY DATASETS 

import pandas as pd


# =========================================
# 1) OCEAN DATA STANDARDIZATION DICTIONARY
# =========================================

STANDARD_OCEAN_MAP = {
    "DATETIME":   ["DATETIME", "Date", "date_time", "Timestamp", "Time"],
    "LAT":        ["LAT", "Latitude", "latitude", "Lat", "lat_deg", "lat"],
    "LON":        ["LON", "Longitude", "longitude", "Lon", "lon_deg", "lon"],
    "DIC":        ["DIC", "DIC(mmol/m3)", "dic"],
    "MLD":        ["MLD", "MixedLayerDepth", "mld"],
    "PCO2_ORIGINAL": ["PCO2_ORIGINAL", "pCO2", "PCO2", "pco2"],
    "CHL":        ["CHL", "Chlorophyll", "Chl_a", "chl"],
    "NO3":        ["NO3", "Nitrate", "N03", "nitrate"],
    "SSS":        ["SSS", "Salinity", "salt", "sal"],
    "SST":        ["SST", "Temperature", "Temp", "SeaTemp", "temp"],
    "DEVIANT_UNCERTAINTY": ["DEVIANT_UNCERTAINTY", "uncertainty", "error"],
}


# =========================================
# 2) TAXONOMY STANDARDIZATION DICTIONARY
# =========================================

STANDARD_TAXONOMY_MAP = {
    "Kingdom":              ["Kingdom"],
    "Phylum":               ["Phylum"],
    "Class":                ["Class", "class"],
    "Order":                ["Order", "order"],
    "Family":               ["Family", "family"],
    "Genus":                ["Genus", "genus"],
    "Species":              ["Species", "species"],
    "Scientific Name":      ["Scientific Name", "scientific_name", "SciName"],
    "Common Name":          ["Common Name", "common_name", "Common"],
    "Authority (Year)":     ["Authority (Year)", "Authority"],
    "Distribution":         ["Distribution", "Region", "Area"],
    "Habitat Type":         ["Habitat Type", "Habitat"],
    "Trophic Level":        ["Trophic Level", "Trophic", "trophic"],
    "Max Length (cm)":      ["Max Length (cm)", "MaxLength", "Length"],
    "IUCN Status":          ["IUCN Status", "IUCN"],
    "Fisheries Importance": ["Fisheries Importance", "Fisheries"],
    "Data Types Available": ["Data Types Available", "DataType"],
    "Notes for Research":   ["Notes for Research", "Notes"],
}


# =========================================
# 3) GENERIC COLUMN NORMALIZER
# =========================================

def normalize_columns(df: pd.DataFrame, mapping: dict):
    new_cols = {}
    existing = list(df.columns)

    for standard_col, variants in mapping.items():
        for col in existing:
            if col.strip() in variants:
                new_cols[col] = standard_col

    return df.rename(columns=new_cols)


# =========================================
# 4) WRAPPERS FOR EACH DOMAIN
# =========================================

def normalize_ocean_columns(df: pd.DataFrame):
    return normalize_columns(df, STANDARD_OCEAN_MAP)


def normalize_taxonomy_columns(df: pd.DataFrame):
    return normalize_columns(df, STANDARD_TAXONOMY_MAP)
