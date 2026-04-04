# Glu2k Proxmox Manager

Web app completa per la gestione centralizzata di più cluster **Proxmox VE** con autenticazione, ruoli, firewall, networking e monitoring in tempo reale.

![version](https://img.shields.io/badge/version-1.0.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-purple)

---

## 🚀 Installazione come container LXC su Proxmox (un comando)

**SSH sul nodo Proxmox come root** e incolla:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/proxmox-helper.sh)"
```

Lo script:
1. 📦 Scarica il template Debian 12
2. 🐧 Crea un **LXC unprivileged** con `nesting=1` e `keyctl=1` (necessari per Docker dentro LXC)
3. 🔧 Installa Docker, clona il repo, genera chiavi Fernet, avvia lo stack
4. ✅ Stampa IP del container, password root generata e URL della Web UI

Al termine:
- 🌐 **UI**: `http://<IP>:3000`
- 🔐 **Login**: `admin` / `admin` *(cambialo subito!)*

### Personalizzazione (variabili d'ambiente)

```bash
CT_ID=200 HOSTNAME=glu2k MEMORY=4096 DISK_SIZE=16 STORAGE=local-zfs BRIDGE=vmbr0 \
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/proxmox-helper.sh)"
```

| Variabile | Default | Note |
|---|---|---|
| `CT_ID` | next free | ID LXC |
| `HOSTNAME` | `glu2k-manager` | |
| `CORES` | `2` | |
| `MEMORY` | `2048` (MB) | |
| `SWAP` | `512` (MB) | |
| `DISK_SIZE` | `12` (GB) | |
| `STORAGE` | `local-lvm` | Storage del rootfs |
| `BRIDGE` | `vmbr0` | |
| `NET_CONFIG` | `dhcp` | oppure `10.0.0.10/24,gw=10.0.0.1` |
| `PASSWORD` | autogenerata | root pwd container |
| `UNPRIVILEGED` | `1` | `0` per privileged |

---

## Caratteristiche principali

### Autenticazione & RBAC
- Login JWT con scadenza 24h
- **3 ruoli**: `admin` (tutto), `operator` (gestisce VM/CT), `viewer` (solo lettura)
- UI di gestione utenti (solo admin): crea, modifica, elimina, disattiva
- Credenziali API Proxmox cifrate con Fernet (AES-256)
- Admin di default creato al primo avvio (`admin` / `admin`)

### Dashboard multi-cluster
- Card per cluster con stato aggregato (nodi online/offline, VM running/fermi)
- Spia rossa pulsante se nodi offline
- Barre CPU/RAM per ogni nodo, live (refresh 3s)
- Volumi storage per nodo con percentuale utilizzo e alert soglie

### Gestione Cluster (Datacenter)
- Metriche aggregate storiche (CPU medio, RAM totale, rete, load)
- Node cards con CPU/RAM + **tutti i volumi storage** del nodo
- Tabella VM/CT con stato, CPU, RAM, disco, uptime
- Firewall Cluster con regole, opzioni, drag&drop reorder
- Log tasks cluster-wide con espansione log completo

### Gestione Nodo
- Risorse in tempo reale (CPU, RAM, disco root, swap)
- Grafici storici: CPU, RAM, rete, load average (hour/day/week/month/year)
- Tabella storage volumi con uso, tipo, contenuto, stato
- **Networking**: bridge/bond/VLAN create, modifica, elimina + apply/revert pending
- Log firewall nodo con filtri (DROP/ACCEPT/REJECT) + ricerca
- Aggiornamenti APT disponibili + refresh lista
- Log tasks nodo

### Gestione VM / Container
- Stato running + risorse live (CPU%, RAM, disco, rete I/O)
- Grafici storici della VM (CPU, RAM, rete IN/OUT, disco read/write)
- **Editor configurazione hardware**: cores, sockets, RAM, balloon/swap, boot order, OS type, start at boot, descrizione
- **Firewall VM** con regole drag&drop + toggle enable/disable (applica anche `firewall=1` sulle NIC automaticamente)
- **Log firewall VM** con filtri e auto-refresh
- **Interfacce di rete**: aggiungi/modifica/rimuovi NIC (modello, bridge, VLAN, MAC, firewall, rate limit)
- **Dischi/Volumi**: tabella con storage, volume, size, opzioni
- Azioni: Start, Shutdown (graceful), Stop (forzato), Reboot
- Log tasks della VM + config raw JSON

### Firewall management
- Gestione completa **cluster e VM** con stessa UI
- Regole con **drag&drop** per riordinare (priorità)
- **Switch verde/rosso** per attivare/disattivare singole regole
- Editing inline con pulsante Modifica
- **Opzioni** con policy IN/OUT, log level, MAC/IP filter, NDP, DHCP, RAdv (con tooltip esplicativi)
- **Log firewall viewer** con tabella parsed: timestamp, action, direzione, proto, source/dest, SPT→DPT
- Filtri log: DROP/ACCEPT/REJECT, ricerca testuale, auto-refresh 5s

### Threshold & Alert visivi
- Percentuali CPU/RAM/Disco cambiano colore:
  - **< 75%** grigio/bianco normale
  - **≥ 75%** arancione (warning)
  - **≥ 90%** rosso (critico)
- Badge WARN / CRITICO nelle stat cards VM
- Applicato ovunque: dashboard, cluster, nodi, VM

### UX & Personalizzazione
- **3 temi**: Dark / Gray (middle) / Light (persistenti in localStorage)
- **Personalizza vista**: mostra/nascondi sezioni + **drag&drop reorder** (per Cluster, Node, VM)
- Auto-refresh 3 secondi ovunque (aggiornamento in-place, senza reset dei form)
- Ordine alfabetico stabile per nodi e volumi
- Click sulle StatCard → scroll alla sezione corrispondente

## Stack tecnologico

| Layer | Tecnologia |
|---|---|
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy + proxmoxer |
| **Auth** | JWT (python-jose) + bcrypt |
| **Frontend** | React 18 + Vite + Tailwind CSS + lucide-react + axios |
| **Database** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Container** | Docker + Docker Compose |
| **Crypto** | Fernet (cryptography) per token Proxmox |

## Installazione rapida (Docker)

### Prerequisiti
- Docker & Docker Compose
- Git
- Python 3 (per generare la chiave di cifratura)

### Setup

```bash
# 1. Clone
git clone https://github.com/manueleesposito77-HAL/glu2k-proxmox-manager.git
cd glu2k-proxmox-manager

# 2. Crea il file .env con le chiavi
cat > backend/.env <<EOF
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://nexus:securepass@db:5432/nexus_db
REDIS_URL=redis://redis:6379/0
EOF

# 3. Avvia lo stack
docker-compose up --build -d

# 4. Attendi che il backend sia pronto
docker logs -f glu2k-api
```

Apri http://localhost:3000 → login con **admin / admin** → cambia la password subito.

### Porte esposte

| Servizio | Porta |
|---|---|
| Frontend (React) | 3000 |
| Backend (FastAPI) | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

Swagger UI: http://localhost:8000/docs

## Generare un API Token Proxmox

Glu2k usa token API Proxmox (non password) per massima sicurezza.

### Via Web UI Proxmox
1. Datacenter → Permissions → **API Tokens** → Add
2. User: `root@pam` (o altro)
3. Token ID: es. `glu2k`
4. ⚠️ **Deseleziona** "Privilege Separation" (altrimenti il token ha 0 permessi)
5. Copia subito il **Secret** UUID (non è più visibile dopo)

### Via CLI (sul nodo Proxmox)
```bash
pveum user token add root@pam glu2k --privsep 0
```

### Nel form Glu2k
- **Auth User**: `root@pam!glu2k` (full token id)
- **Auth Token**: il secret UUID

## Installazione manuale in container LXC su Proxmox

Se preferisci creare il container a mano invece di usare l'[helper script](#-installazione-come-container-lxc-su-proxmox-un-comando):

```bash
# Sul nodo Proxmox host (serve nesting+keyctl per Docker dentro LXC)
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname glu2k-manager \
  --cores 2 --memory 2048 --swap 512 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --rootfs local-lvm:12 \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --password "$(openssl rand -base64 12)"

pct start 200
pct exec 200 -- bash -c "curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/install.sh | bash"
```

## Export template LXC (per distribuzione)

Se vuoi creare un `.tar.zst` riutilizzabile dopo aver installato in un container:

```bash
# Sul nodo Proxmox, dopo aver configurato il container ID 200
pct stop 200
vzdump 200 --mode stop --compress zstd --dumpdir /var/lib/vz/template/cache/
# Rinomina il file in glu2k-manager-v1.0.0.tar.zst
pct start 200
```

Il file può poi essere importato su altri Proxmox:
```bash
pct restore 300 /var/lib/vz/template/cache/glu2k-manager-v1.0.0.tar.zst \
  --storage local-lvm --rootfs local-lvm:12
```

## Ruoli e permessi

| Operazione | admin | operator | viewer |
|---|:-:|:-:|:-:|
| Login | ✅ | ✅ | ✅ |
| Visualizzare tutto | ✅ | ✅ | ✅ |
| Gestire utenti | ✅ | ❌ | ❌ |
| Aggiungere/rimuovere cluster | ✅ | ❌ | ❌ |
| Modificare firewall cluster | ✅ | ❌ | ❌ |
| Modificare networking nodo | ✅ | ❌ | ❌ |
| Aggiornare pacchetti nodo | ✅ | ❌ | ❌ |
| Start/Stop/Reboot VM | ✅ | ✅ | ❌ |
| Modificare config VM | ✅ | ✅ | ❌ |
| Gestire firewall VM | ✅ | ✅ | ❌ |

## Risorse e note operative

- **Refresh automatico**: 3 secondi per tutte le viste (disattivabile chiudendo la tab)
- **Auto-reload pve-firewall**: dopo aver creato/modificato una regola Proxmox impiega ~10s per ricompilarla
- **Flag `firewall=1` su NIC**: necessario su container LXC affinché le regole VM vengano applicate — il pulsante "Attiva FW" lo fa automaticamente
- **Log vuoti?**: abilita `log_level_in: info` nelle Opzioni Firewall oppure imposta `log=info` sulle singole regole

## Troubleshooting

```bash
# Logs backend
docker logs -f glu2k-api

# Logs frontend
docker logs -f glu2k-ui

# DB non raggiungibile
docker restart glu2k-api glu2k-db

# Reset completo (attenzione: cancella volumi)
docker-compose down -v
docker-compose up --build -d
```

## Sviluppo

- **Hot reload**: backend con `uvicorn --reload`, frontend con Vite HMR (polling abilitato per Windows/Docker)
- **Swagger**: http://localhost:8000/docs per testare gli endpoint
- **Migrazioni DB**: schemi generati automaticamente all'avvio (Base.metadata.create_all). Per produzione usa Alembic.

## Roadmap

- [x] Autenticazione JWT + RBAC
- [x] Monitoring multi-cluster
- [x] Firewall management completo
- [x] Networking management
- [x] Editor config VM
- [x] Grafici storici
- [x] Temi personalizzabili
- [x] Layout personalizzabile
- [ ] Template LXC pronto all'uso
- [ ] Log firewall aggregato cluster
- [ ] Backup/snapshot management
- [ ] Notifiche (Telegram/Email)
- [ ] Metriche esportabili (Prometheus)
- [ ] Multi-factor authentication

## Licenza

MIT
