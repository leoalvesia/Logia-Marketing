#!/bin/bash
# setup-server.sh — Configura VPS Ubuntu 22.04 para hospedar a Logia Platform
#
# Uso (como root no servidor):
#   curl -fsSL https://raw.githubusercontent.com/SEU_ORG/logia-marketing/main/scripts/setup-server.sh | bash
#   -- ou --
#   bash setup-server.sh
#
# O que faz:
#   1. Atualiza o sistema
#   2. Instala Docker + Docker Compose Plugin
#   3. Instala Caddy (proxy reverso com SSL automatico)
#   4. Configura firewall UFW (22, 80, 443)
#   5. Configura Fail2ban (protecao SSH)
#   6. Cria usuario "deploy" sem root
#   7. Cria 2 GB de swap
#   8. Ajusta limites de sistema para containers
#   9. Cria estrutura de diretorios /opt/logia/

set -euo pipefail

DEPLOY_USER="deploy"
APP_DIR="/opt/logia"
SWAP_SIZE="2G"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "ERRO: $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Execute como root: sudo bash setup-server.sh"

log "Atualizando sistema..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq curl wget gnupg ca-certificates lsb-release git ufw fail2ban htop ncdu unzip jq

log "Instalando Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker && systemctl start docker

log "Instalando Caddy..."
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -qq && apt-get install -y -qq caddy
systemctl enable caddy

log "Configurando UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment "SSH"
ufw allow 80/tcp   comment "HTTP"
ufw allow 443/tcp  comment "HTTPS"
ufw --force enable

log "Configurando Fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 1h
findtime = 10m
maxretry = 5
[sshd]
enabled = true
EOF
systemctl enable fail2ban && systemctl restart fail2ban

log "Criando usuario ${DEPLOY_USER}..."
id "${DEPLOY_USER}" &>/dev/null || useradd -m -s /bin/bash "${DEPLOY_USER}"
usermod -aG docker "${DEPLOY_USER}"
mkdir -p "/home/${DEPLOY_USER}/.ssh"
chmod 700 "/home/${DEPLOY_USER}/.ssh"
touch "/home/${DEPLOY_USER}/.ssh/authorized_keys"
chmod 600 "/home/${DEPLOY_USER}/.ssh/authorized_keys"
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "/home/${DEPLOY_USER}/.ssh"

if ! swapon --show | grep -q /swapfile; then
    log "Criando swap ${SWAP_SIZE}..."
    fallocate -l "${SWAP_SIZE}" /swapfile
    chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "vm.swappiness=10" >> /etc/sysctl.conf && sysctl -p -q
fi

log "Ajustando limites..."
cat >> /etc/sysctl.conf << 'EOF'
vm.max_map_count=262144
net.core.somaxconn=65535
net.ipv4.tcp_tw_reuse=1
EOF
sysctl -p -q

log "Criando estrutura ${APP_DIR}..."
mkdir -p "${APP_DIR}"/{app,logs,backups,credentials}
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${APP_DIR}"
mkdir -p /var/log/caddy && chown caddy:caddy /var/log/caddy

echo ""
echo "================================================================"
echo " Setup concluido! Proximos passos:"
echo "  1. echo 'CHAVE_PUBLICA' >> /home/${DEPLOY_USER}/.ssh/authorized_keys"
echo "  2. scp .env.production deploy@IP:${APP_DIR}/.env"
echo "  3. su - ${DEPLOY_USER} && git clone REPO ${APP_DIR}/app"
echo "  4. cp ${APP_DIR}/app/config/Caddyfile /etc/caddy/Caddyfile && systemctl reload caddy"
echo "  5. cd ${APP_DIR}/app && docker compose -f docker-compose.prod.yml up -d"
echo "  6. docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"
echo "================================================================"
