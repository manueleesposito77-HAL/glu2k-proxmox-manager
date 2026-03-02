from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cluster import Cluster
from app.schemas.cluster import ClusterCreate, ClusterResponse
from app.services.proxmox_service import ProxmoxService
from app.core.config import get_settings
from cryptography.fernet import Fernet
from typing import List

router = APIRouter()
settings = get_settings()
cipher = Fernet(settings.ENCRYPTION_KEY)

@router.get("/", response_model=List[ClusterResponse])
def list_clusters(db: Session = Depends(get_db)):
    return db.query(Cluster).all()

@router.post("/", response_model=ClusterResponse)
def add_cluster(cluster_in: ClusterCreate, db: Session = Depends(get_db)):
    # Cifratura del token
    encrypted_token = cipher.encrypt(cluster_in.auth_token.encode()).decode()
    
    db_cluster = Cluster(
        name=cluster_in.name,
        host=cluster_in.host,
        port=cluster_in.port,
        auth_user=cluster_in.auth_user,
        auth_token=encrypted_token,
        auth_type=cluster_in.auth_type,
        verify_ssl=cluster_in.verify_ssl
    )
    
    db.add(db_cluster)
    db.commit()
    db.refresh(db_cluster)
    return db_cluster

@router.delete("/{cluster_id}")
def delete_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    db.delete(cluster)
    db.commit()
    return {"status": "deleted"}
