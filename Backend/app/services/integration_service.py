# app/services/integration_service.py
from typing import Dict, Any, List, Optional
from app.database import supabase

# ============================
# TAXONOMY LOOKUP
# ============================

def get_taxonomy(scientific_name: str) -> Optional[Dict[str, Any]]:
    if not scientific_name:
        return None

    res = (
        supabase.table("taxonomy_data")
        .select("*")
        .eq("scientific_name", scientific_name)
        .execute()
    )

    if not res.data:
        return None

    return res.data[0]


# ============================
# OCEAN LOOKUP (NEAREST ENV)
# ============================

def get_ocean_environment(lat: float, lon: float, limit: int = 1) -> List[Dict[str, Any]]:
    """
    Use simple numeric bounding-box approximation to fetch few nearest rows.
    FRONTEND will do final nearest distance logic if needed.
    """
    if lat is None or lon is None:
        return []

    # fetch small area around given lat/lon
    res = (
        supabase.table("ocean_data")
        .select("*")
        .gte("lat", lat - 0.5)
        .lte("lat", lat + 0.5)
        .gte("lon", lon - 0.5)
        .lte("lon", lon + 0.5)
        .limit(limit)
        .execute()
    )

    return res.data or []


# ============================
# OTOLITH LOOKUP
# ============================

def get_otolith_by_original_id(otolith_id: str) -> List[Dict[str, Any]]:
    res = (
        supabase.table("otolith_data")
        .select("*")
        .eq("otolith_id", otolith_id)
        .execute()
    )
    return res.data or []


def get_otolith_by_species(scientific_name: str) -> List[Dict[str, Any]]:
    res = (
        supabase.table("otolith_data")
        .select("*")
        .eq("scientific_name", scientific_name)
        .execute()
    )
    return res.data or []


# ============================
# E-DNA BLAST DIRECT ANALYSIS
# ============================
from app.services.edna_service import run_blast_direct

def run_edna_analysis(sequence: str) -> Dict[str, Any]:
    """Run BLAST → return dict with species, taxonomy, etc."""
    return run_blast_direct(sequence)


# ============================
# CORE INTEGRATION LOGIC
# ============================

def integrate_by_species(scientific_name: str):
    sci = scientific_name.strip()
    taxonomy = get_taxonomy(sci)
    otoliths = get_otolith_by_species(sci)

    # ocean environment: take one otolith location → fetch ocean data
    ocean_env = []
    if otoliths:
        lat = otoliths[0].get("lat")
        lon = otoliths[0].get("lon")
        ocean_env = get_ocean_environment(lat, lon)

    return {
        "species": sci,
        "taxonomy": taxonomy,
        "otolith_records": otoliths,
        "ocean_environment": ocean_env,
    }


def integrate_by_otolith_id(oid: str):
    otos = get_otolith_by_original_id(oid)
    if not otos:
        return None

    rec = otos[0]
    sci = rec.get("scientific_name")
    taxonomy = get_taxonomy(sci)

    lat = rec.get("lat")
    lon = rec.get("lon")
    ocean_env = get_ocean_environment(lat, lon)

    return {
        "species": sci,
        "taxonomy": taxonomy,
        "otolith_record": rec,
        "ocean_environment": ocean_env,
    }


def integrate_by_edna(sequence: str):
    blast = run_edna_analysis(sequence)
    sci = blast.get("species")

    taxonomy = get_taxonomy(sci)
    otoliths = get_otolith_by_species(sci)

    # ocean environment by using any otolith record
    ocean_env = []
    if otoliths:
        lat = otoliths[0].get("lat")
        lon = otoliths[0].get("lon")
        ocean_env = get_ocean_environment(lat, lon)

    return {
        "raw_sequence": sequence,
        "blast_match": blast,
        "species": sci,
        "taxonomy": taxonomy,
        "otolith_records": otoliths,
        "ocean_environment": ocean_env,
    }
