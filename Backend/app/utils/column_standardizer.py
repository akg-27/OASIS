# app/utils/column_standardizer.py
OCEAN_MAP = {
    "DATETIME": "datetime",         
    "DATE": "datetime",             
    "LON": "lon",
    "LONGITUDE": "lon",
    "LONG": "lon",
    "LAT": "lat",
    "LATITUDE": "lat",
    "DIC": "dic",
    "MLD": "mld",
    "PCO2_ORIGINAL": "pco2_original",
    "PCO2": "pco2_original",
    "CHL": "chl",
    "CHL_A": "chl",
    "NO3": "no3",
    "SSS": "sss",
    "SST": "sst",
    "DEVIANT_UNCERTAINTY": "deviant_uncertainty",
    "STATIONID": "station_id",
    "STATION_ID": "station_id",
    "LOCALITY": "locality",
    "WATERBODY": "water_body",
}


TAXONOMY_MAP = {
    "Kingdom": "kingdom",
    "Phylum": "phylum",
    "Class": "class",
    "Order": "order",
    "Family": "family",
    "Genus": "genus",
    "Species": "species",
    "Scientific Name": "scientific_name",
    "Common Name": "common_name",
    "Authority (Year)": "authority_year",
    "Distribution": "distribution",
    "Habitat Type": "habitat_type",
    "Trophic Level": "trophic_level",
    "Max Length (cm)": "max_length_cm",
    "IUCN Status": "iucn_status",
    "Fisheries Importance": "fisheries_importance",
    "Data Types Available": "data_types_available",
    "Notes for Research": "notes_for_research",
}

OTOLITH_MAP = {
    # Core ID fields
    "otolithID": "otolith_id",
    "otolithId": "otolith_id",
    "otolith_id": "otolith_id",

    # Taxonomy
    "family": "family",
    "scientific_name": "scientific_name",
    "scientificName": "scientific_name",

    # Project / Station
    "projectCode": "project_code",
    "project_code": "project_code",
    "stationID": "station_id",
    "Station ID": "station_id",
    "station_id": "station_id",

    # Location fields
    "locality": "locality",
    "Locality": "locality",
    "waterBody": "water_body",
    "water_body": "water_body",

    # Image
    "image_url": "original_image_url",
    "imageUrl": "original_image_url",
    "Image_url": "original_image_url",

    # Coordinates
    "decimalLatitude": "lat",
    "decimal_latitude": "lat",
    "decimalLongitude": "lon",
    "decimal_longitude": "lon",

    # Depth
    "Collection Depth (in mts)": "collection_depth_m",
    "collection_depth_m": "collection_depth_m",
    "Station Depth (in mts)": "station_depth_m",
    "station_depth_m": "station_depth_m",

    # Metadata
    "submittedBy": "submitted_by",
    "submitted_by": "submitted_by",

    # Extra fields present in your CSV
    "Detail_url": "detail_url",
    "detail_url": "detail_url",
    "Sex": "sex",
    "Life stage": "life_stage",
    "Habitat": "habitat",
    "Platform": "platform",
    "Collection Method": "collection_method",
}



def standardize_df(df, dtype: str):
    df = df.rename(columns=lambda x: str(x).strip())
    mapping = {}
    if dtype == "ocean":
        mapping = {k: v for k, v in OCEAN_MAP.items()}
    elif dtype == "taxonomy":
        mapping = {k: v for k, v in TAXONOMY_MAP.items()}
    elif dtype == "otolith":
        mapping = {k: v for k, v in OTOLITH_MAP.items()}

    # build rename map by matching case-insensitively and ignoring spaces and punctuation
    rename_map = {}
    lower_map = {k.lower().replace(" ", "").replace("_", ""): v for k, v in mapping.items()}
    for col in df.columns:
        key = col.lower().replace(" ", "").replace("_", "")
        if key in lower_map:
            rename_map[col] = lower_map[key]
        else:
            # try exact match
            if col in mapping:
                rename_map[col] = mapping[col]

    df = df.rename(columns=rename_map)
    return df
