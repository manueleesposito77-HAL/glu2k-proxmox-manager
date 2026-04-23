# Glu2k Proxmox Manager

> **⚠️ DISCLAIMER**
>
> **Il presente software viene fornito "così com'è", senza garanzie di alcun tipo, esplicite o implicite. L'autore non si assume alcuna responsabilità per eventuali danni diretti, indiretti, incidentali o consequenziali derivanti dall'utilizzo, dalla modifica o dalla distribuzione di questo software. L'utilizzo è interamente a rischio e responsabilità dell'utente.**


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
CT_ID=200 CT_HOSTNAME=glu2k MEMORY=4096 DISK_SIZE=16 STORAGE=local-zfs BRIDGE=vmbr0 \
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/proxmox-helper.sh)"
```

| Variabile | Default | Note |
|---|---|---|
| `CT_ID` | next free | ID LXC |
| `CT_HOSTNAME` | `glu2k-proxmox-manager` | |
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
- **Lista VM/CT ospitate** sul nodo con link diretto al detail
- Log firewall nodo con filtri (DROP/ACCEPT/REJECT) + ricerca
- Aggiornamenti APT disponibili + refresh lista
- **Console shell nodo**: bottone blu per aprire la shell Proxmox del nodo in una nuova tab
- Log tasks nodo

### Wizard creazione VM/CT
- Pulsante **"+ Crea VM/CT"** nella vista cluster
- Tab dedicate per **LXC Container** e **VM QEMU**
- Form completo: nodo, VMID (auto-calcolato), hostname/nome, password, cores, RAM, swap, storage, disco, bridge, IP, gateway
- Selezione **template/ISO** da qualunque storage del nodo
- Pulsante **"Scarica nuovo template/ISO"** che apre sotto-modal con:
  - **Catalogo Proxmox + TurnKey Linux** (lista sfogliabile, badge colorati)
  - **Download da URL** (es. Ubuntu/Debian ISO, auto-detect filename)
- Opzione "Avvia dopo la creazione"

### Gestione VM / Container
- Stato running + risorse live (CPU%, RAM, disco, rete I/O)
- Grafici storici della VM (CPU, RAM, rete IN/OUT, disco read/write)
- **Editor configurazione hardware**: cores, sockets, RAM, balloon/swap, boot order, OS type, start at boot, descrizione
- **Firewall VM** con regole drag&drop + toggle enable/disable (applica anche `firewall=1` sulle NIC automaticamente)
- **Log firewall VM** con filtri e auto-refresh
- **Interfacce di rete**: aggiungi/modifica/rimuovi NIC (modello, bridge, VLAN, MAC, firewall, rate limit)
- **Dischi/Volumi**: tabella con storage, volume, size, opzioni — icone per tipo (disco, CD-ROM, rootfs, mount point)
  - **Gestione CD-ROM**: monta/smonta ISO con selettore da tutti gli storage del nodo
  - Ordinamento automatico: dischi prima, CD-ROM dopo
- **Ordine di Boot**: card dedicata con lista ordinata, frecce su/giù per riordinare, aggiungi/rimuovi dispositivi, salvataggio diretto su Proxmox — icone per tipo dispositivo (disco, CD-ROM, rete, EFI)
- **Console noVNC**: bottone blu per aprire la console Proxmox della VM/CT in una nuova tab (disponibile anche a VM spenta)
- **IP nelle interfacce di rete**: visualizzazione IP corrente per VM QEMU (via Guest Agent) e LXC (da config)
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

## Generare un API Token Proxmox (passaggi dettagliati)

Glu2k **non** usa username/password del PAM, ma un **API Token** Proxmox. Questo è più sicuro: il token si può revocare in qualsiasi momento senza cambiare la password dell'utente.

### Metodo 1 — Web UI di Proxmox (consigliato)

1. **Login** alla Web UI di Proxmox (es. `https://192.168.1.10:8006`)
2. Nel menu a sinistra clicca su **Datacenter** (la radice, non un nodo)
3. Vai su **Permissions** → **API Tokens**
4. Clicca il pulsante **Add** in alto
5. Compila la form:
   - **User**: seleziona `root@pam` (o un altro utente con permessi sufficienti)
   - **Token ID**: un nome a tua scelta, es. `glu2k`
   - **Privilege Separation**: ⚠️ **DESELEZIONA** questo checkbox
     > Se lo lasci selezionato, il token viene creato con **zero permessi** e Glu2k non potrà vedere nulla. Dovresti poi assegnare manualmente i permessi al token.
   - **Expire**: lascia vuoto per nessuna scadenza (oppure metti una data)
   - **Comment**: opzionale
6. Clicca **Add**
7. **Appare una finestra modale con due campi**:
   - **Token ID**: `root@pam!glu2k` (questo è il "full token id")
   - **Secret**: un UUID del tipo `12345678-1234-1234-1234-123456789abc`
8. ⚠️ **COPIA SUBITO IL SECRET IN UN POSTO SICURO**: dopo aver chiuso questa finestra **non potrai più vederlo**. Se lo perdi devi rigenerare il token.

### Metodo 2 — CLI (SSH sul nodo Proxmox)

```bash
ssh root@192.168.1.10
pveum user token add root@pam glu2k --privsep 0
```

Output:
```
┌──────────────┬──────────────────────────────────────┐
│ key          │ value                                │
├──────────────┼──────────────────────────────────────┤
│ full-tokenid │ root@pam!glu2k                       │
│ value        │ 12345678-1234-1234-1234-123456789abc │
└──────────────┴──────────────────────────────────────┘
```

- `full-tokenid` = il campo "Auth User" in Glu2k
- `value` = il campo "Auth Token (Secret)" in Glu2k

### Come usarlo in Glu2k

Nella form "Aggiungi Cluster / Registra Server" di Glu2k compila:

| Campo | Valore |
|---|---|
| Nome Cluster | nome libero, es. `Produzione` |
| IP / Hostname | IP del nodo Proxmox, es. `192.168.1.10` (no `https://`, no `:8006`) |
| Porta | `8006` (default) |
| **Auth User** | `root@pam!glu2k` |
| Auth Type | `API Token` |
| **Auth Token** | `12345678-1234-1234-1234-123456789abc` |
| Verify SSL | OFF *(certificati Proxmox sono self-signed di default)* |

### Limitare i permessi del token (opzionale, più sicuro)

Se vuoi dare permessi limitati (read-only, nessuna modifica), usa un token con privsep e assegna ruolo specifico:

```bash
# Crea utente dedicato e token con solo PVEAuditor (sola lettura)
pveum user add glu2k@pve --password $(openssl rand -base64 16)
pveum user token add glu2k@pve viewer --privsep 0
pveum aclmod / --user glu2k@pve --role PVEAuditor
```

Ruoli Proxmox utili:
- `PVEAuditor`: solo lettura
- `PVEVMAdmin`: gestione VM completa (serve per il ruolo `operator` di Glu2k)
- `Administrator`: accesso totale (serve per il ruolo `admin` di Glu2k)

### Troubleshooting token

| Errore | Causa | Soluzione |
|---|---|---|
| `401 invalid PVE ticket` | token scaduto o secret errato | rigenera token |
| `403 permission denied` | privilege separation attivo o ruolo insufficiente | crea nuovo token con `--privsep 0` oppure assegna `Administrator` all'ACL |
| `SSL: certificate verify failed` | Verify SSL attivo con cert self-signed | disattiva "Verify SSL" |
| `connection refused` | porta sbagliata o firewall | usa porta `8006`, controlla firewall del nodo |

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
| Monta/smonta ISO CD-ROM | ✅ | ✅ | ❌ |
| Modifica ordine di boot | ✅ | ✅ | ❌ |
| Aprire console VM/nodo | ✅ | ✅ | ✅ |

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

### Login admin/admin non funziona

Se al primo accesso `admin`/`admin` restituisce "Credenziali non valide", il bootstrap dell'admin potrebbe non essere avvenuto (il backend è partito prima del DB). Soluzioni:

**1. Controlla i log:**
```bash
docker logs glu2k-api | grep bootstrap
# Dovresti vedere: "[bootstrap] Creato admin default: admin/admin"
```

**2. Riavvia il backend forzatamente:**
```bash
docker restart glu2k-api
docker logs glu2k-api | tail -20
```

**3. Reset admin di emergenza** (usa la SECRET_KEY dal `backend/.env`):
```bash
# leggi la SECRET_KEY
grep SECRET_KEY backend/.env

# chiama l'endpoint di reset
curl -X POST "http://localhost:8000/api/v1/reset-admin?secret=$(grep SECRET_KEY backend/.env | cut -d= -f2)"
```

Dopo questo: login con `admin`/`admin` funzionerà.

**4. Verifica DB connesso:**
```bash
docker exec glu2k-db psql -U nexus -d nexus_db -c "SELECT username,role,is_active FROM users;"
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
- [x] Log firewall aggregato cluster
- [ ] Backup/snapshot management
- [ ] Notifiche (Telegram/Email)
- [ ] Metriche esportabili (Prometheus)
- [ ] Multi-factor authentication
- [ ] Template LXC pronto all'uso

## Licenza

MIT
