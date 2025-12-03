from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload_routes
from app.routers import ocean_routes
from app.routers import taxonomy_routes
from app.routers import otolith_routes
from app.routers import edna_routes
from app.routers import integration_routes
from app.routers import metadata_routes


app = FastAPI(title="CMLRE Marine Data Platform")

# Allow all origins (for development)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # React access allowed
    allow_credentials=True,
    allow_methods=["*"],              # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],              # All headers allowed
)


# Add Routers
app.include_router(upload_routes.router)
app.include_router(ocean_routes.router)
app.include_router(taxonomy_routes.router)
app.include_router(otolith_routes.router)
app.include_router(edna_routes.router)
app.include_router(integration_routes.router)
app.include_router(metadata_routes.router)


@app.get("/")
def root():
    return {"msg": "Backend running..."}