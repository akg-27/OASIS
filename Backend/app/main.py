from fastapi import FastAPI
# from app.database import init_db
from app.routers import upload_routes
from app.routers import visualization_routes
from app.routers import taxonomy_routes
from app.routers import otolith_routes
from app.routers import edna_routes


# Force Python to resolve all DNS using IPv4 only
import socket

original_getaddrinfo = socket.getaddrinfo

def force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = force_ipv4_getaddrinfo


app = FastAPI(title="CMLRE Marine Data Platform")

# Initialize DB tables
# init_db()

# Add Routers
app.include_router(upload_routes.router)
app.include_router(visualization_routes.router)
app.include_router(taxonomy_routes.router)
app.include_router(otolith_routes.router)
app.include_router(edna_routes.router)


@app.get("/")
def root():
    return {"msg": "Backend running..."}
