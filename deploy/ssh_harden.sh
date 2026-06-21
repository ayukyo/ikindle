#!/usr/bin/env bash
# ============================================================================
# deploy/ssh_harden.sh —— SSH 安全加固脚本
#
# 部署：
#   sudo bash deploy/ssh_harden.sh
#
# 操作：
#   1. 禁用 SSH 密码登录（仅密钥登录）
#   2. 修改 SSH 端口（默认 22 → 2222，建议根据 ECS 安全组同步修改）
#   3. 限制登录尝试（MaxAuthTries）
#   4. 安装 fail2ban 防爆破
#
# ⚠️ 警告：执行前请确保：
#   - 已经配置 SSH 密钥登录并能正常用密钥登录
#   - 阿里云 ECS 安全组已放行新 SSH 端口（2222）
#   - 保留当前 SSH 会话直到新连接测试成功
# ============================================================================
set -euo pipefail

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="/etc/ssh/sshd_config.bak.$(date +%Y%m%d_%H%M%S)"

echo "============================================"
echo "  iKindle SSH 加固脚本"
echo "============================================"
echo ""

# 备份原配置
echo "[1/5] 备份 sshd_config → $BACKUP"
sudo cp "$SSHD_CONFIG" "$BACKUP"

# 禁用密码登录
echo "[2/5] 禁用 SSH 密码登录"
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD_CONFIG"

# 修改 SSH 端口（22 → 2222）
echo "[3/5] 修改 SSH 端口（22 → 2222）"
sudo sed -i 's/^#\?Port 22/Port 2222/' "$SSHD_CONFIG"

# 限制登录尝试
echo "[4/5] 限制 MaxAuthTries = 3"
sudo sed -i 's/^#\?MaxAuthTries.*/MaxAuthTries 3/' "$SSHD_CONFIG"

# 禁用 root 登录（如需 root 用 sudo）
# sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' "$SSHD_CONFIG"

# 重启 sshd
echo "[5/5] 重启 sshd 服务"
sudo systemctl restart sshd

# 安装 fail2ban
echo ""
echo "============================================"
echo "  安装 fail2ban（防 SSH 爆破）"
echo "============================================"
sudo apt install -y fail2ban

# 配置 fail2ban（SSH 默认已启用）
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

echo ""
echo "============================================"
echo "  完成！请执行以下检查："
echo "============================================"
echo "1. 新开 SSH 会话测试新端口 2222 + 密钥登录"
echo "2. 阿里云 ECS 安全组放行 2222 端口"
echo "3. 关闭原 22 端口会话"
echo ""
echo "验证 fail2ban 状态："
echo "  sudo fail2ban-client status sshd"
