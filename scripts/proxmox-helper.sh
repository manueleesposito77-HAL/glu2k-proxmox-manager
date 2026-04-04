#!/usr/bin/env bash
# Nexus Proxmox Manager - Helper Script per Proxmox VE host
# Crea un container LXC e installa tutto automaticamente.
#
# Uso (SSH sul nodo Proxmox come root):
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/proxmox-manager/main/scripts/proxmox-helper.sh)"

set -euo pipefail

# ==== Default config ====
CT_ID="${CT_ID:-$(pvesh get /cluster/nextid)}"
HOSTNAME="${HOSTNAME:-nexus-manager}"
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
  _   _
 | \ | |
 |  \| | _____  ___   _ ___
 | . ` |/ _ \ \/ / | | / __|
 | |\  |  __/>  <| |_| \__ \
 |_| \_|\___/_/\_\\__,_|___/
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

# ==== Password ====
if [ -z "$PASSWORD" ]; then
  PASSWORD=$(openssl rand -base64 12)
  info "Password root generata: $PASSWORD"
fi

# ==== Crea container ====
info "Creo LXC $CT_ID ($HOSTNAME)..."
pct create "$CT_ID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME" \
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
info "Installo Nexus dentro il container..."
pct exec "$CT_ID" -- bash -c "
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq curl ca-certificates
"

pct exec "$CT_ID" -- bash -c "curl -fsSL https://raw.githubusercontent.com/manueleesposito77-HAL/proxmox-manager/main/scripts/install.sh | bash"

# ==== Info finale ====
IP=$(pct exec "$CT_ID" -- hostname -I 2>/dev/null | awk '{print $1}')
echo
ok "INSTALLAZIONE COMPLETATA"
echo "============================================"
echo " Container ID:  $CT_ID ($HOSTNAME)"
echo " IP:            $IP"
echo " Root pwd:      $PASSWORD"
echo
echo " Nexus Web UI:  http://${IP}:3000"
echo " API docs:      http://${IP}:8000/docs"
echo " Login:         admin / admin"
echo "============================================"
echo
echo "IMPORTANTE: cambia la password admin al primo login!"
