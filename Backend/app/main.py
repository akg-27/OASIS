from fastapi import FastAPI
from app.routers import upload_routes
from app.routers import ocean_routes
from app.routers import taxonomy_routes
from app.routers import otolith_routes
from app.routers import edna_routes

app = FastAPI(title="CMLRE Marine Data Platform")

# Add Routers
app.include_router(upload_routes.router)
app.include_router(ocean_routes.router)
app.include_router(taxonomy_routes.router)
app.include_router(otolith_routes.router)
app.include_router(edna_routes.router)


@app.get("/")
def root():
    return {"msg": "Backend running..."}