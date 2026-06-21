#!/usr/bin/env bash
# ============================================================================
# deploy/install.sh —— iKindle 一键部署脚本（阿里云 Ubuntu 22.04）
#
# 部署：
#   sudo bash deploy/install.sh
#
# 操作：
#   1. 检测发行版（Ubuntu/Debian vs CentOS/RHEL）
#   2. 安装依赖（nginx / python3 / certbot / cnlunar）
#   3. 复制项目文件到 /home/ikindle/
#   4. 配置 nginx + certbot
#   5. 配置 cron + systemd timer 替代
#   6. （可选）运行 ssh_harden.sh
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR="/home/ikindle"
SERVICE_USER="ikindle"

echo "============================================"
echo "  iKindle 一键部署脚本"
echo "============================================"

# ---- 1. 检测发行版 ----
echo "[1/8] 检测发行版"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
    echo "  发行版: $PRETTY_NAME"
else
    echo "  ❌ 无法检测发行版（缺少 /etc/os-release）"
    exit 1
fi

case "$DISTRO" in
    ubuntu|debian)
        PKG_INSTALL="apt install -y"
        PKG_UPDATE="apt update"
        SERVICE_MANAGER="systemctl"
        ;;
    centos|rhel|rocky|almalinux|fedora)
        PKG_INSTALL="dnf install -y"
        PKG_UPDATE="dnf check-update || true"
        SERVICE_MANAGER="systemctl"
        ;;
    *)
        echo "  ⚠️  未测试发行版 $DISTRO，尝试 apt（Debian 系）"
        PKG_INSTALL="apt install -y"
        PKG_UPDATE="apt update"
        SERVICE_MANAGER="systemctl"
        ;;
esac

# ---- 2. 创建服务用户 ----
echo "[2/8] 创建服务用户 $SERVICE_USER"
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    sudo useradd -m -s /bin/bash "$SERVICE_USER"
    echo "  ✅ 用户已创建"
else
    echo "  ✅ 用户已存在"
fi

# ---- 3. 安装依赖 ----
echo "[3/8] 安装依赖（nginx / python3 / certbot / cnlunar）"
sudo $PKG_UPDATE
sudo $PKG_INSTALL nginx python3 python3-pip cron curl
if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
    sudo $PKG_INSTALL certbot python3-certbot-nginx
else
    sudo $PKG_INSTALL certbot
fi
sudo pip3 install cnlunar 2>&1 | tail -3
echo "  ✅ 依赖已安装"

# ---- 4. 复制项目文件 ----
echo "[4/8] 复制项目文件到 $INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
sudo chmod +x "$INSTALL_DIR"/*.sh "$INSTALL_DIR"/*.py "$INSTALL_DIR"/deploy/*.sh
echo "  ✅ 文件已复制"

# ---- 5. 配置 nginx ----
echo "[5/8] 配置 nginx"
sudo cp "$INSTALL_DIR/deploy/nginx.conf" /etc/nginx/sites-available/kindle
sudo ln -sf /etc/nginx/sites-available/kindle /etc/nginx/sites-enabled/
sudo nginx -t && echo "  ✅ nginx 配置语法正确"
sudo $SERVICE_MANAGER reload nginx

# ---- 6. 签发 HTTPS 证书 ----
echo "[6/8] 签发 HTTPS 证书（kindle.91api.vip）"
echo "  ⚠️  请确保 DNS A 记录 kindle.91api.vip 已指向本机公网 IP"
read -p "  是否现在签发证书？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo certbot --nginx -d kindle.91api.vip --non-interactive --agree-tos \
        --email admin@91api.vip || echo "  ⚠️  certbot 失败（可能 DNS 未生效），稍后手动跑"
fi

# ---- 7. 配置 cron ----
echo "[7/8] 配置 cron（每分钟构建 + 每日 Hitokoto）"
sudo cp "$INSTALL_DIR/deploy/crontab" /etc/cron.d/ikindle
sudo chmod 644 /etc/cron.d/ikindle
sudo $SERVICE_MANAGER restart cron 2>/dev/null || sudo $SERVICE_MANAGER enable --now crond
echo "  ✅ cron 已配置"

# ---- 8. 首次构建 + 健康检查 ----
echo "[8/8] 首次构建 dashboard.html"
sudo -u "$SERVICE_USER" bash "$INSTALL_DIR/build.sh"
if [ -f "$INSTALL_DIR/dashboard.html" ]; then
    SIZE=$(wc -c < "$INSTALL_DIR/dashboard.html")
    echo "  ✅ dashboard.html 已生成（$SIZE 字节）"
fi

# logrotate 配置
echo ""
echo "[Bonus] 配置 logrotate（防止 build.log 无限增长）"
sudo tee /etc/logrotate.d/ikindle > /dev/null << EOF
$INSTALL_DIR/build.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
}
EOF
echo "  ✅ logrotate 已配置"

echo ""
echo "============================================"
echo "  部署完成！"
echo "============================================"
echo ""
echo "下一步："
echo "  1. 验证 HTTPS: curl -I https://kindle.91api.vip/"
echo "  2. 查看日志:  tail -f $INSTALL_DIR/build.log"
echo "  3. KWP4 实物验证（在 KINDLE 浏览器打开 https://kindle.91api.vip/dashboard.html）"
echo ""
echo "可选 SSH 加固："
echo "  sudo bash $INSTALL_DIR/deploy/ssh_harden.sh"
