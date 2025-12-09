from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload_routes
from app.routers import ocean_single_routes
from app.routers import taxonomy_routes
from app.routers import otolith_routes
from app.routers import edna_routes
from app.routers import integration_routes
from app.routers import metadata_routes
from app.routers import auth_routes
from app.routers import visualization_routes
from app.routers import data_info_routes
from app.routers import otolith_inference
from app.routers import ocean_heat_routes
from app.routers import ocean_multi_routes
from app.routers import biodiversity_routes
from app.routers import biodiversity_two_routes
from app.routers import ocean_box_routes
import os
import uvicorn


app = FastAPI(title="CMLRE Marine Data Platform")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(upload_routes.router)
app.include_router(ocean_single_routes.router)
app.include_router(taxonomy_routes.router)
app.include_router(otolith_routes.router)
app.include_router(edna_routes.router)
app.include_router(integration_routes.router)
app.include_router(metadata_routes.router)
app.include_router(auth_routes.router)
app.include_router(visualization_routes.router)
app.include_router(data_info_routes.router)
app.include_router(otolith_inference.router)
app.include_router(ocean_heat_routes.router)
app.include_router(ocean_multi_routes.router)
app.include_router(biodiversity_routes.router)
app.include_router(biodiversity_two_routes.router)
app.include_router(ocean_box_routes.router)


@app.get("/")
def root():
    return {"msg": "Backend running successfully"}


# ---------- REQUIRED FOR RENDER ----------
# Bind Uvicorn to 0.0.0.0 and use $PORT env
if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )


    
