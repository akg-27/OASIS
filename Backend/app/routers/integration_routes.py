# app/routers/integration_routes.py
from fastapi import APIRouter, Query, requests, Body
from app.services.integration_service import (
    integrate_by_species,
    integrate_by_otolith_id,
    integrate_by_edna,
)

router = APIRouter(prefix="/integrate", tags=["Integration"])


# 1) Integration by scientific name
@router.get("/species")
def integration_by_species(name: str = Query(..., description="Scientific Name")):
    result = integrate_by_species(name)
    return result


# 2) Integration by otolith original ID (slash-safe through query param)
@router.get("/otolith")
def integration_by_otolith(oid: str = Query(..., description="Otolith ID like CMLRE/OTL/00027")):
    result = integrate_by_otolith_id(oid)
    if not result:
        raise requests.get(404, "Otolith ID not found")
    return result


# 3) EDNA integration (direct raw string)
@router.post("/edna")
def integrate_edna_route(sequence: str = Body(..., embed=False)):
    return integrate_by_edna(sequence)
