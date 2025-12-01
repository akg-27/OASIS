# app/services/integration_service.py
import math
from typing import Any, Dict, List, Optional

from app.database import supabase
from app.services.edna_service import run_blast_direct

# -------------------------
# Helpers
# -------------------------

def normalize_species_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    n = str(name).strip()
    # remove extra characters commonly found in hit_def
    n = n.replace('"', '').replace("'", "")
    # If species is "Genus sp." or similar, leave it; otherwise try to ensure two tokens
    parts = [p for p in n.split() if p]
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return n


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# -------------------------
# Robust taxonomy lookup
# -------------------------
def robust_taxonomy_lookup(species: str) -> Optional[Dict[str, Any]]:
    """
    Try multiple strategies to find taxonomy for a species in taxonomy_data.
    1) ilike on common JSON keys
    2) fallback: fetch rows and do Python-level case-insensitive match
    """
    if not species:
        return None

    species = species.strip()

    # Try common JSON keys using ilike
    keys_to_try = [
        "data->>Scientific Name",
        "data->>Species",
        "data->>scientific_name",
        "data->>Common Name",
    ]
    for key in keys_to_try:
        try:
            res = supabase.table("taxonomy_data").select("data").ilike(key, f"%{species}%").limit(1).execute()
            if res.data:
                return res.data[0]["data"]
        except Exception:
            # ignore query errors and continue
            pass

    # Fallback: fetch a modest number of taxonomy rows and try Python-side match
    try:
        res_all = supabase.table("taxonomy_data").select("data").execute()
        if not res_all.data:
            return None
        for r in res_all.data:
            d = r.get("data") or {}
            # check several candidate fields
            for fld in ["Scientific Name", "Species", "scientific_name", "Common Name"]:
                val = d.get(fld)
                if val and species.lower() == str(val).strip().lower():
                    return d
            # also try substring match
            for fld in ["Scientific Name", "Species", "scientific_name", "Common Name", "Distribution"]:
                val = d.get(fld)
                if val and species.lower() in str(val).strip().lower():
                    return d
    except Exception:
        return None

    return None


# -------------------------
# Get lat/lon from an otolith row (many possible keys)
# -------------------------
def get_latlon_from_otolith(row: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Try multiple possible field names to extract latitude and longitude.
    """
    lat_keys = ["decimalLatitude", "decimal_latitude", "latitude", "lat", "LAT", "Latitude"]
    lon_keys = ["decimalLongitude", "decimal_longitude", "longitude", "lon", "LON", "Longitude"]

    lat = None
    lon = None
    for k in lat_keys:
        if k in row and row[k] not in (None, ""):
            lat = safe_float(row[k])
            if lat is not None:
                break

    for k in lon_keys:
        if k in row and row[k] not in (None, ""):
            lon = safe_float(row[k])
            if lon is not None:
                break

    if lat is not None and lon is not None:
        return {"lat": lat, "lon": lon}
    return None


# -------------------------
# Find ocean rows by station/locality fallback
# -------------------------
def find_ocean_by_station_or_locality(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    If no lat/lon, try matching using station id or locality names.
    """
    results = []
    # candidate keys
    station_keys = ["station_id", "Station ID", "stationID", "stationid", "station"]
    locality_keys = ["locality", "Locality", "water_body", "waterBody", "water_body"]

    # Try station id
    for sk in station_keys:
        sid = row.get(sk)
        if sid:
            try:
                r = supabase.table("ocean_data").select("data").ilike("data->>Station ID", f"%{sid}%").limit(10).execute()
                if r.data:
                    results.extend([x["data"] for x in r.data])
                    return results
            except Exception:
                pass

    # Try locality/water body text match
    for lk in locality_keys:
        local = row.get(lk)
        if local:
            try:
                r = supabase.table("ocean_data").select("data").ilike("data->>Locality", f"%{local}%").limit(20).execute()
                if r.data:
                    results.extend([x["data"] for x in r.data])
                    return results
            except Exception:
                pass

    return results


# -------------------------
# Find nearest ocean rows by coordinates (Haversine)
# -------------------------
def find_nearest_ocean_by_coords(lat: float, lon: float, max_km: float = 100) -> List[Dict[str, Any]]:
    """
    Read all ocean rows (data JSON) and return rows within max_km sorted by distance.
    This is OK for moderate dataset sizes. Optimize later if needed.
    """
    try:
        res = supabase.table("ocean_data").select("data").execute()
    except Exception:
        return []

    if not res.data:
        return []

    ocean_rows = [r["data"] for r in res.data]
    nearby = []
    for r in ocean_rows:
        rlat = safe_float(r.get("LAT") or r.get("lat") or r.get("Latitude"))
        rlon = safe_float(r.get("LON") or r.get("lon") or r.get("Longitude"))
        if rlat is None or rlon is None:
            continue
        dist = haversine_km(lat, lon, rlat, rlon)
        if dist <= max_km:
            nearby.append((dist, r))

    nearby_sorted = [r for d, r in sorted(nearby, key=lambda x: x[0])]
    return nearby_sorted


# -------------------------
# Public integration methods
# -------------------------
def integrate_species(species: str) -> Dict[str, Any]:
    species_norm = normalize_species_name(species)

    taxonomy = robust_taxonomy_lookup(species_norm)

    # Otoliths: stored as flat rows in otolith_data
    try:
        o_res = supabase.table("otolith_data").select("*").ilike("scientific_name", f"%{species_norm}%").execute()
        otoliths = o_res.data or []
    except Exception:
        otoliths = []

    # Ocean environment: attempt to find using otolith coordinates, station or locality
    ocean_env = []
    for r in otoliths:
        coords = get_latlon_from_otolith(r)
        if coords:
            found = find_nearest_ocean_by_coords(coords["lat"], coords["lon"])
            if found:
                # append top few
                ocean_env.extend(found[:5])
                continue

        # fallback station/locality
        found2 = find_ocean_by_station_or_locality(r)
        if found2:
            ocean_env.extend(found2)

    # Normalize ocean_env elements (if tuples returned, they might be raw rows)
    # ensure we always return list of dicts
    ocean_env_clean = []
    for item in ocean_env:
        if isinstance(item, tuple):
            ocean_env_clean.append(item[1] if len(item) > 1 else item[0])
        else:
            ocean_env_clean.append(item)

    return {
        "species": species,
        "taxonomy": taxonomy,
        "otolith_records": otoliths,
        "ocean_environment": ocean_env_clean,
    }


def integrate_by_otolith_id(otolith_id: str) -> Optional[Dict[str, Any]]:
    try:
        res = supabase.table("otolith_data").select("*").eq("otolith_id", otolith_id).execute()
    except Exception:
        return None

    if not res.data:
        return None

    record = res.data[0]
    species = record.get("scientific_name") or record.get("Scientific Name") or None
    if not species:
        # attempt to find species by label or family fallback
        species = record.get("label")

    base = integrate_species(species) if species else {"species": None, "taxonomy": None, "otolith_records": [record], "ocean_environment": []}
    base["otolith_record"] = record
    return base


def integrate_edna_direct(sequence: str) -> Optional[Dict[str, Any]]:
    # run blast (no DB storage)
    blast_out = run_blast_direct(sequence)
    species = None
    if blast_out:
        # blast_out may include 'species' at top-level or in 'blast_match'
        if isinstance(blast_out, dict) and blast_out.get("species"):
            species = normalize_species_name(blast_out.get("species"))
        elif isinstance(blast_out, dict) and blast_out.get("blast_match", {}).get("species"):
            species = normalize_species_name(blast_out["blast_match"]["species"])

    if not species:
        return None

    # Now reuse species integration
    base = integrate_species(species)
    # Attach raw blast output for debugging
    base["raw_sequence"] = sequence
    base["blast_match"] = blast_out
    return base
