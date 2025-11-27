from fastapi import FastAPI
# from app.database import init_db
from app.routers import upload_routes
from app.routers import visualization_routes
from app.routers import taxonomy_routes


app = FastAPI(title="CMLRE Marine Data Platform")

# Initialize DB tables
# init_db()

# Add Routers
app.include_router(upload_routes.router)
app.include_router(visualization_routes.router)
app.include_router(taxonomy_routes.router)


@app.get("/")
def root():
    return {"msg": "Backend running..."}
