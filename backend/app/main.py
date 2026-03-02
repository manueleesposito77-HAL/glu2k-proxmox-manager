from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1.cluster import router as cluster_router
from app.database import engine, Base

settings = get_settings()

# Create Tables (Automatic for Dev, use Alembic for Prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(cluster_router, prefix=f"{settings.API_V1_STR}/clusters", tags=["clusters"])

@app.get("/")
def root():
    return {"message": "Welcome to Nexus Proxmox Manager API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
