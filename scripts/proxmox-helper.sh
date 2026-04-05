#!/usr/bin/env bash
# Glu2k Proxmox Manager - Helper Script per Proxmox VE host
# Crea un container LXC e installa tutto automaticamente.
#
# Uso (SSH sul nodo Proxmox come root):
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/proxmox-helper.sh)"

set -euo pipefail

# ==== Default config ====
CT_ID="${CT_ID:-$(pvesh get /cluster/nextid)}"
CT_HOSTNAME="${CT_HOSTNAME:-}"
CT_HOSTNAME_DEFAULT="glu2k-proxmox-manager"
CORES="${CORES:-2}"
MEMORY="${MEMORY:-2048}"
SWAP="${SWAP:-512}"
DISK_SIZE="${DISK_SIZE:-12}"
STORAGE="${STORAGE:-local-lvm}"
BRIDGE="${BRIDGE:-vmbr0}"
NET_CONFIG="${NET_CONFIG:-dhcp}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
OS_TEMPLATE_NAME="${OS_TEMPLATE_NAME:-debian-12-standard}"
UNPRIVILEGED="${UNPRIVILEGED:-1}"
PASSWORD="${PASSWORD:-}"

banner() {
  cat <<'EOF'
   _____ _      _    _ ___  _  __
  / ____| |    | |  | |__ \| |/ /
 | |  __| |    | |  | |  ) | ' /
 | | |_ | |    | |  | | / /|  <
 | |__| | |____| |__| |/ /_| . \
  \_____|______|\____/|____|_|\_\
    Proxmox Manager Installer
EOF
}

info()  { echo -e "\e[1;34m[INFO]\e[0m $*"; }
ok()    { echo -e "\e[1;32m[OK]\e[0m $*"; }
err()   { echo -e "\e[1;31m[ERR]\e[0m $*" >&2; }
die()   { err "$*"; exit 1; }

banner
echo

# ==== Check: siamo su un nodo Proxmox? ====
command -v pct >/dev/null || die "'pct' non trovato. Questo script va eseguito su un nodo Proxmox VE."
command -v pveam >/dev/null || die "'pveam' non trovato. Questo script va eseguito su un nodo Proxmox VE."

# ==== Scarica il template se manca ====
info "Cerco template $OS_TEMPLATE_NAME..."
TEMPLATE=$(pveam available --section system | grep "$OS_TEMPLATE_NAME" | awk '{print $2}' | sort -V | tail -1 || true)
if [ -z "$TEMPLATE" ]; then die "Template $OS_TEMPLATE_NAME non trovato in pveam available"; fi

if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE"; then
  info "Scarico template $TEMPLATE..."
  pveam update >/dev/null
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi
TEMPLATE_PATH="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}"
ok "Template pronto: $TEMPLATE_PATH"

# ==== Hostname (interattivo se non fornito) ====
if [ -z "$CT_HOSTNAME" ]; then
  echo
  read -r -p "Hostname del container (invio per default '$CT_HOSTNAME_DEFAULT'): " CT_HOSTNAME_INPUT
  CT_HOSTNAME="${CT_HOSTNAME_INPUT:-$CT_HOSTNAME_DEFAULT}"
fi
info "Hostname: $CT_HOSTNAME"

# ==== Storage per il rootfs (interattivo se non fornito) ====
if [ -z "${STORAGE_OVERRIDE:-}" ] && [ "$STORAGE" = "local-lvm" ]; then
  echo
  echo "Storage disponibili per il rootfs del container:"
  # Lista storage che supportano rootdir/images
  mapfile -t AVAIL_STORAGES < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 && $3=="active" {print $1"|"$2"|"$5"|"$7}')
  if [ ${#AVAIL_STORAGES[@]} -eq 0 ]; then
    info "Nessuno storage con rootdir attivo trovato, uso default: $STORAGE"
  else
    i=1
    declare -A STORAGE_MAP
    for s in "${AVAIL_STORAGES[@]}"; do
      IFS='|' read -r name type total avail <<< "$s"
      # convert to GB
      avail_gb=$(( avail / 1024 / 1024 ))
      total_gb=$(( total / 1024 / 1024 ))
      # Indica se dinamico
      case "$type" in
        zfspool|btrfs|cephfs|rbd|nfs) dyn="dinamico" ;;
        lvmthin) dyn="dinamico (thin)" ;;
        lvm) dyn="statico" ;;
        dir) dyn="dinamico (sparse)" ;;
        *) dyn="$type" ;;
      esac
      printf "  %d) %-20s [%s] %d GB liberi / %d GB totali — %s\n" "$i" "$name" "$type" "$avail_gb" "$total_gb" "$dyn"
      STORAGE_MAP[$i]="$name"
      i=$((i+1))
    done
    echo
    read -r -p "Scegli storage (numero, invio per default 'local-lvm'): " STORAGE_CHOICE
    if [ -n "$STORAGE_CHOICE" ] && [ -n "${STORAGE_MAP[$STORAGE_CHOICE]:-}" ]; then
      STORAGE="${STORAGE_MAP[$STORAGE_CHOICE]}"
    fi
  fi
fi
info "Storage rootfs: $STORAGE"

# ==== Dimensione disco (interattivo) ====
if [ "$DISK_SIZE" = "12" ]; then
  echo
  read -r -p "Dimensione disco in GB (invio per default '$DISK_SIZE'): " DISK_INPUT
  if [ -n "$DISK_INPUT" ] && [[ "$DISK_INPUT" =~ ^[0-9]+$ ]]; then
    DISK_SIZE="$DISK_INPUT"
  fi
fi
info "Dimensione disco: ${DISK_SIZE} GB"

# ==== Password ====
if [ -z "$PASSWORD" ]; then
  echo
  echo "Imposta la password root del container LXC (invio = genera automaticamente)"
  read -r -s -p "Password root: " PASSWORD
  echo
  if [ -n "$PASSWORD" ]; then
    read -r -s -p "Conferma password: " PASSWORD_CONFIRM
    echo
    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
      die "Le password non corrispondono"
    fi
    if [ ${#PASSWORD} -lt 5 ]; then
      die "La password deve avere almeno 5 caratteri"
    fi
  else
    PASSWORD=$(openssl rand -base64 12)
    info "Password root generata: $PASSWORD"
  fi
fi

# ==== Crea container ====
info "Creo LXC $CT_ID ($CT_HOSTNAME)..."
pct create "$CT_ID" "$TEMPLATE_PATH" \
  --hostname "$CT_HOSTNAME" \
  --cores "$CORES" \
  --memory "$MEMORY" \
  --swap "$SWAP" \
  --rootfs "${STORAGE}:${DISK_SIZE}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=${NET_CONFIG}" \
  --unprivileged "$UNPRIVILEGED" \
  --features "nesting=1,keyctl=1" \
  --password "$PASSWORD" \
  --onboot 1 \
  --start 0
ok "Container $CT_ID creato"

# ==== Start + wait ====
info "Avvio container..."
pct start "$CT_ID"
sleep 5

# Attendo rete
for i in {1..30}; do
  if pct exec "$CT_ID" -- sh -c "ip -4 addr show eth0 | grep -q 'inet '" 2>/dev/null; then break; fi
  sleep 1
done
sleep 3

# ==== Installa dentro il container ====
info "Installo Glu2k dentro il container..."
pct exec "$CT_ID" -- bash -c "
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq curl ca-certificates
"

pct exec "$CT_ID" -- bash -c "curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/glu2k-proxmox-manager/main/scripts/install.sh | bash"

# ==== Info finale ====
IP=$(pct exec "$CT_ID" -- hostname -I 2>/dev/null | awk '{print $1}')
echo
ok "INSTALLAZIONE COMPLETATA"
echo "============================================"
echo " Container ID:  $CT_ID ($CT_HOSTNAME)"
echo " IP:            $IP"
echo " Root pwd:      $PASSWORD"
echo
echo " Glu2k Web UI:  http://${IP}:3000"
echo " API docs:      http://${IP}:8000/docs"
echo " Login:         admin / admin"
echo "============================================"
echo
echo "IMPORTANTE: cambia la password admin al primo login!"
