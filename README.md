# Nexus Proxmox Manager

Web app completa per la gestione centralizzata di più cluster **Proxmox VE** con autenticazione, ruoli, firewall, networking e monitoring in tempo reale.

![version](https://img.shields.io/badge/version-1.0.0-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React-purple)

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
git clone https://github.com/manueleesposito77-HAL/proxmox-manager.git
cd proxmox-manager

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
docker logs -f nexus-api
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

Nexus usa token API Proxmox (non password) per massima sicurezza.

### Via Web UI Proxmox
1. Datacenter → Permissions → **API Tokens** → Add
2. User: `root@pam` (o altro)
3. Token ID: es. `nexus`
4. ⚠️ **Deseleziona** "Privilege Separation" (altrimenti il token ha 0 permessi)
5. Copia subito il **Secret** UUID (non è più visibile dopo)

### Via CLI (sul nodo Proxmox)
```bash
pveum user token add root@pam nexus --privsep 0
```

### Nel form Nexus
- **Auth User**: `root@pam!nexus` (full token id)
- **Auth Token**: il secret UUID

## Installazione in container LXC su Proxmox

```bash
# Sul nodo Proxmox host
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname nexus-manager \
  --cores 2 --memory 2048 --swap 512 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --rootfs local-lvm:8 \
  --features nesting=1,keyctl=1 \
  --unprivileged 1

pct start 200
pct enter 200

# Dentro il container
apt update && apt install -y docker.io docker-compose git python3-cryptography openssl
git clone https://github.com/manueleesposito77-HAL/proxmox-manager.git
cd proxmox-manager
# ... segui lo script setup come sopra
docker-compose up --build -d
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
docker logs -f nexus-api

# Logs frontend
docker logs -f nexus-ui

# DB non raggiungibile
docker restart nexus-api nexus-db

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
