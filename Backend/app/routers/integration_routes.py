from fastapi import APIRouter, HTTPException, Query, Body
from app.services.integration_service import (
    integrate_species,
    integrate_by_otolith_id,
    integrate_edna_direct,
)

router = APIRouter(prefix="/integrate", tags=["Integration"])


# ---------------------- SPECIES → FULL PROFILE ----------------------
@router.get("/species")
def species_integration(name: str = Query(..., description="Scientific Name")):
    """
    Integrate using a species name.
    """
    result = integrate_species(name)
    if not result:
        raise HTTPException(404, "Species not found")
    return result


# ---------------------- OTOLITH → FULL PROFILE ----------------------
@router.get("/otolith")
def otolith_integration(
    oid: str = Query(..., description="OtolithID like CMLRE/OTL/00001")
):
    """
    Integrate using an otolith ID.
    """
    result = integrate_by_otolith_id(oid)
    if not result:
        raise HTTPException(404, "Otolith ID not found")
    return result


# ---------------------- NEW: DIRECT EDNA INTEGRATION ----------------------
@router.post("/edna")
async def edna_direct(sequence: str = Body(..., embed=False)):
    """
    Direct EDNA → BLAST → Taxonomy → Otolith → Ocean integration.
    No need to store EDNA or use UUID.
    """
    result = integrate_edna_direct(sequence)
    if not result:
        raise HTTPException(404, "No usable EDNA result found")
    return result
