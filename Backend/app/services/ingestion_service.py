def detect_dataset_type(df):
    cols = list(df.columns)

    ocean_keywords = ["DATETIME", "LON", "LAT", "DIC", "MLD", "PCO2_ORIGINAL", "CHL", "NO3", "SSS", "SST", "DEVIANT_UNCERTAINTY"]
    

    # Oceanographic signatures
    if any(k in cols for k in ocean_keywords):
        return "ocean"

    taxonomy_keywords = ["Kingdom", "Phylum", "Class,Order", "Family", "Genus", "Species", "Scientific Name", "Common Name", "Authority (Year)", "Distribution", "Habitat Type", "Trophic Level,Max Length (cm)","IUCN Status", "Fisheries Importance", "Data Types Available,Notes for Research"]
    
    if any(k in cols for k in taxonomy_keywords):
        return "taxonomy"
    
    return "unknown"
