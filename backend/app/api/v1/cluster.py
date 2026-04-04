from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cluster import Cluster
from app.models.user import User
from app.schemas.cluster import ClusterCreate, ClusterResponse, ClusterUpdate
from app.services.proxmox_service import ProxmoxService
from app.core.config import get_settings
from app.core.security import require_any, require_admin, require_operator_or_admin
from cryptography.fernet import Fernet
from typing import List

router = APIRouter(dependencies=[Depends(require_any)])
settings = get_settings()
cipher = Fernet(settings.ENCRYPTION_KEY)

@router.get("/", response_model=List[ClusterResponse])
def list_clusters(db: Session = Depends(get_db)):
    return db.query(Cluster).all()

@router.post("/", response_model=ClusterResponse, dependencies=[Depends(require_admin)])
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

@router.put("/{cluster_id}", response_model=ClusterResponse, dependencies=[Depends(require_admin)])
def update_cluster(cluster_id: int, cluster_in: ClusterUpdate, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    data = cluster_in.model_dump(exclude_unset=True)
    # Se arriva auth_token, cifralo (ignora se vuoto = non toccare)
    if "auth_token" in data:
        if data["auth_token"]:
            data["auth_token"] = cipher.encrypt(data["auth_token"].encode()).decode()
        else:
            del data["auth_token"]
    for k, v in data.items():
        setattr(cluster, k, v)
    db.commit()
    db.refresh(cluster)
    return cluster


@router.delete("/{cluster_id}", dependencies=[Depends(require_admin)])
def delete_cluster(cluster_id: int, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    db.delete(cluster)
    db.commit()
    return {"status": "deleted"}


def _get_cluster_or_404(cluster_id: int, db: Session) -> Cluster:
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.get("/{cluster_id}/vms")
def list_cluster_vms(cluster_id: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.get_all_vms()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes")
def list_cluster_nodes(cluster_id: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/status")
def node_status(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).status.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/storage")
def node_storage(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).storage.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/disks")
def node_disks(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).disks.list.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/updates")
def node_updates(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).apt.update.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/nodes/{node}/updates/refresh", dependencies=[Depends(require_admin)])
def node_updates_refresh(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        task = svc.proxmox.nodes(node).apt.update.post()
        return {"status": "ok", "task_id": task}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/services")
def node_services(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).services.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/storage")
def cluster_storage(cluster_id: int, db: Session = Depends(get_db)):
    """Storage del cluster (risorse aggregate tra nodi)."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.cluster.resources.get(type="storage")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/tasks")
def cluster_tasks(cluster_id: int, limit: int = 50, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        tasks = svc.proxmox.cluster.tasks.get()
        return tasks[:limit] if isinstance(tasks, list) else tasks
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/tasks")
def node_tasks(cluster_id: int, node: str, limit: int = 50, vmid: int = None, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        params = {"limit": limit}
        if vmid is not None:
            params["vmid"] = vmid
        return svc.proxmox.nodes(node).tasks.get(**params)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/tasks/{upid}/log")
def task_log(cluster_id: int, node: str, upid: str, start: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).tasks(upid).log.get(start=start, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/tasks/{upid}/status")
def task_status(cluster_id: int, node: str, upid: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).tasks(upid).status.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/firewall/log")
def node_firewall_log(cluster_id: int, node: str, limit: int = 100, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).firewall.log.get(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/syslog")
def node_syslog(cluster_id: int, node: str, limit: int = 100, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).syslog.get(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/rrddata")
def node_rrddata(cluster_id: int, node: str, timeframe: str = "hour", db: Session = Depends(get_db)):
    """Dati storici del nodo (cpu, memoria, rete, disco). timeframe: hour/day/week/month/year"""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).rrddata.get(timeframe=timeframe, cf="AVERAGE")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/network/{iface}")
def node_network_get(cluster_id: int, node: str, iface: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).network(iface).get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/nodes/{node}/network")
def node_network(cluster_id: int, node: str, db: Session = Depends(get_db)):
    """Lista interfacce di rete del nodo (bridges, bonds, physical)."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.nodes(node).network.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/nodes/{node}/network", dependencies=[Depends(require_admin)])
def node_network_create(cluster_id: int, node: str, payload: dict, db: Session = Depends(get_db)):
    """Crea una nuova interfaccia (es. bridge). Applica modifiche."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        svc.proxmox.nodes(node).network.post(**payload)
        # Apply pending changes
        try:
            svc.proxmox.nodes(node).network.put()
        except Exception:
            pass
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/nodes/{node}/network/{iface}", dependencies=[Depends(require_admin)])
def node_network_update(cluster_id: int, node: str, iface: str, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        svc.proxmox.nodes(node).network(iface).put(**payload)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{cluster_id}/nodes/{node}/network/{iface}", dependencies=[Depends(require_admin)])
def node_network_delete(cluster_id: int, node: str, iface: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        svc.proxmox.nodes(node).network(iface).delete()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/nodes/{node}/network/apply", dependencies=[Depends(require_admin)])
def node_network_apply(cluster_id: int, node: str, db: Session = Depends(get_db)):
    """Applica le modifiche di rete pending (reload ifupdown2)."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        task = svc.proxmox.nodes(node).network.put()
        return {"status": "ok", "task_id": task}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/nodes/{node}/network/revert", dependencies=[Depends(require_admin)])
def node_network_revert(cluster_id: int, node: str, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        svc.proxmox.nodes(node).network.delete()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---- Firewall (cluster-level) ----
@router.get("/{cluster_id}/firewall/rules")
def fw_cluster_rules(cluster_id: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.cluster.firewall.rules.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/firewall/rules", dependencies=[Depends(require_admin)])
def fw_cluster_add_rule(cluster_id: int, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        svc.proxmox.cluster.firewall.rules.post(**clean)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/firewall/rules/{pos}", dependencies=[Depends(require_admin)])
def fw_cluster_move_rule(cluster_id: int, pos: int, payload: dict, db: Session = Depends(get_db)):
    """Sposta/modifica una regola. payload={moveto: N} per riordinare."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        # Campi vuoti → lista per parametro 'delete' di Proxmox
        to_delete = [k for k, v in payload.items() if (v is None or v == "") and k not in ("moveto", "delete")]
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        if to_delete:
            clean["delete"] = ",".join(to_delete)
        svc.proxmox.cluster.firewall.rules(pos).put(**clean)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{cluster_id}/firewall/rules/{pos}", dependencies=[Depends(require_admin)])
def fw_cluster_del_rule(cluster_id: int, pos: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        svc.proxmox.cluster.firewall.rules(pos).delete()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/firewall/options")
def fw_cluster_options(cluster_id: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        return svc.proxmox.cluster.firewall.options.get()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/firewall/options", dependencies=[Depends(require_admin)])
def fw_cluster_set_options(cluster_id: int, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        svc.proxmox.cluster.firewall.options.put(**clean)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


def _vm_handle(svc, node: str, vmid: int):
    """Ritorna (handle, type) gestendo sia QEMU che LXC."""
    vms = svc.get_all_vms()
    vm = next((v for v in vms if v.get("vmid") == vmid and v.get("node") == node), None)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    vtype = vm.get("type")
    if vtype == "lxc":
        return svc.proxmox.nodes(node).lxc(vmid), "lxc"
    return svc.proxmox.nodes(node).qemu(vmid), "qemu"


@router.get("/{cluster_id}/vms/{node}/{vmid}/config")
def vm_get_config(cluster_id: int, node: str, vmid: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, vtype = _vm_handle(svc, node, vmid)
        cfg = handle.config.get()
        return {"type": vtype, "config": cfg}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/vms/{node}/{vmid}/rrddata")
def vm_rrddata(cluster_id: int, node: str, vmid: int, timeframe: str = "hour", db: Session = Depends(get_db)):
    """Dati storici VM (cpu, mem, net, disk)."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        return handle.rrddata.get(timeframe=timeframe, cf="AVERAGE")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/vms/{node}/{vmid}/status")
def vm_get_status(cluster_id: int, node: str, vmid: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        return handle.status.current.get()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/vms/{node}/{vmid}/config", dependencies=[Depends(require_operator_or_admin)])
def vm_update_config(cluster_id: int, node: str, vmid: int, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        # Rimuovi chiavi vuote
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        if not clean:
            raise HTTPException(status_code=400, detail="No fields to update")
        handle.config.put(**clean)
        return {"status": "ok", "updated": list(clean.keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---- Firewall VM-level ----
@router.get("/{cluster_id}/vms/{node}/{vmid}/firewall/rules")
def fw_vm_rules(cluster_id: int, node: str, vmid: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        return handle.firewall.rules.get()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/vms/{node}/{vmid}/firewall/rules", dependencies=[Depends(require_operator_or_admin)])
def fw_vm_add_rule(cluster_id: int, node: str, vmid: int, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        handle.firewall.rules.post(**clean)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/vms/{node}/{vmid}/firewall/rules/{pos}", dependencies=[Depends(require_operator_or_admin)])
def fw_vm_move_rule(cluster_id: int, node: str, vmid: int, pos: int, payload: dict, db: Session = Depends(get_db)):
    """Sposta/modifica regola VM. payload={moveto: N} per riordinare."""
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        to_delete = [k for k, v in payload.items() if (v is None or v == "") and k not in ("moveto", "delete")]
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        if to_delete:
            clean["delete"] = ",".join(to_delete)
        handle.firewall.rules(pos).put(**clean)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/{cluster_id}/vms/{node}/{vmid}/firewall/rules/{pos}", dependencies=[Depends(require_operator_or_admin)])
def fw_vm_del_rule(cluster_id: int, node: str, vmid: int, pos: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        handle.firewall.rules(pos).delete()
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/vms/{node}/{vmid}/firewall/options")
def fw_vm_options(cluster_id: int, node: str, vmid: int, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        return handle.firewall.options.get()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{cluster_id}/vms/{node}/{vmid}/firewall/log")
def fw_vm_log(cluster_id: int, node: str, vmid: int, limit: int = 100, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        return handle.firewall.log.get(limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{cluster_id}/vms/{node}/{vmid}/firewall/options", dependencies=[Depends(require_operator_or_admin)])
def fw_vm_set_options(cluster_id: int, node: str, vmid: int, payload: dict, db: Session = Depends(get_db)):
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        handle, _ = _vm_handle(svc, node, vmid)
        clean = {k: v for k, v in payload.items() if v is not None and v != ""}
        handle.firewall.options.put(**clean)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{cluster_id}/vms/{node}/{vmid}/action", dependencies=[Depends(require_operator_or_admin)])
def vm_action(cluster_id: int, node: str, vmid: int, action: str, db: Session = Depends(get_db)):
    if action not in ("start", "stop", "shutdown", "reset", "reboot"):
        raise HTTPException(status_code=400, detail="Invalid action")
    cluster = _get_cluster_or_404(cluster_id, db)
    try:
        svc = ProxmoxService(cluster)
        # LXC usa un endpoint diverso rispetto a QEMU
        vms = svc.get_all_vms()
        vm = next((v for v in vms if v.get("vmid") == vmid and v.get("node") == node), None)
        if not vm:
            raise HTTPException(status_code=404, detail="VM not found")
        vtype = vm.get("type")  # "qemu" or "lxc"
        if vtype == "lxc":
            task_id = svc.proxmox.nodes(node).lxc(vmid).status(action).post()
        else:
            task_id = svc.proxmox.nodes(node).qemu(vmid).status(action).post()
        return {"status": "ok", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
