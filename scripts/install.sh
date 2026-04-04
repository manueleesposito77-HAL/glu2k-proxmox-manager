#!/usr/bin/env bash
# Glu2k Proxmox Manager - installer dentro un container Debian/Ubuntu
# Da eseguire DENTRO il container LXC

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/glu2k-proxmox-manager}"
REPO="https://github.com/manueleesposito77-HAL/glu2k-proxmox-manager.git"

echo "=== Glu2k Proxmox Manager installer ==="
echo

# Update
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  git curl ca-certificates python3 python3-cryptography openssl

# Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "Installo Docker..."
  apt-get install -y -qq docker.io docker-compose
  systemctl enable --now docker
fi

# Clone repo
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Clono il repository..."
  git clone "$REPO" "$INSTALL_DIR"
else
  echo "Repository già presente, aggiorno..."
  cd "$INSTALL_DIR" && git pull
fi

cd "$INSTALL_DIR"

# .env
if [ ! -f backend/.env ]; then
  echo "Genero backend/.env..."
  cat > backend/.env <<EOF
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://nexus:securepass@db:5432/nexus_db
REDIS_URL=redis://redis:6379/0
EOF
fi

# Build & start
echo "Costruisco e avvio i container..."
docker-compose up --build -d

# Wait for backend
echo -n "Attendo backend..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health >/dev/null; then echo " OK"; break; fi
  echo -n "."; sleep 2
done

IP=$(hostname -I | awk '{print $1}')

echo
echo "============================================"
echo " Glu2k Proxmox Manager installato!"
echo " URL:     http://${IP}:3000"
echo " API:     http://${IP}:8000/docs"
echo " Login:   admin / admin (cambiala subito!)"
echo "============================================"
