# iKindle 部署指南

本目录包含阿里云 Linux 部署所需的所有配置文件。

## 文件清单

| 文件 | 用途 | 部署命令 |
|------|------|---------|
| `nginx.conf` | nginx 站点配置（kindle.91api.vip） | `sudo cp nginx.conf /etc/nginx/sites-available/kindle && sudo ln -s /etc/nginx/sites-available/kindle /etc/nginx/sites-enabled/` |
| `crontab` | cron 任务配置（构建 + Hitokoto 刷新） | `sudo cp crontab /etc/cron.d/ikindle && sudo chmod 644 /etc/cron.d/ikindle && sudo systemctl restart cron` |
| `ssh_harden.sh` | SSH 安全加固脚本 | `sudo bash ssh_harden.sh` |

## 部署顺序

### 1. 前置条件

- 阿里云 ECS Ubuntu 22.04（公网 IP）
- 域名 `91api.vip` 添加 A 记录 `kindle` → ECS 公网 IP
- 阿里云 ECS 安全组放行 80 / 443 端口

### 2. 安装基础依赖

```bash
sudo apt update
sudo apt install -y nginx python3 python3-pip certbot python3-certbot-nginx
pip3 install cnlunar
```

### 3. 复制项目文件

```bash
# 在 ECS 上创建目录
sudo mkdir -p /home/ikindle/{templates,deploy,assets,build}
sudo chown -R $USER:$USER /home/ikindle

# 从本地复制（rsync / scp）
rsync -avz --exclude='.git' --exclude='build/' \
    ./ ikindle@<ECS_IP>:/home/ikindle/
```

### 4. 配置 nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/kindle
sudo ln -s /etc/nginx/sites-available/kindle /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. 签发 HTTPS 证书

```bash
sudo certbot --nginx -d kindle.91api.vip
```

certbot 会自动修改 nginx 配置并 reload。证书 90 天有效，certbot 自带 systemd timer 自动续期。

### 6. 配置 cron

```bash
sudo cp deploy/crontab /etc/cron.d/ikindle
sudo chmod 644 /etc/cron.d/ikindle
sudo systemctl restart cron
```

### 7. SSH 加固（可选但推荐）

```bash
sudo bash deploy/ssh_harden.sh
```

⚠️ **警告**：执行前确保：
- 已配置 SSH 密钥登录
- 阿里云 ECS 安全组已放行 2222 端口
- 保留当前 SSH 会话直到新连接测试成功

### 8. 验证部署

```bash
# 测试 HTTPS
curl -I https://kindle.91api.vip/

# 测试 dashboard.html
curl -I https://kindle.91api.vip/dashboard.html

# 测试 cron 构建
ls -la /home/ikindle/dashboard.html
cat /home/ikindle/build.log | tail -20
```

### 9. KWP4 实物验证

1. 在 KWP4 浏览器打开 `https://kindle.91api.vip/dashboard.html`
2. 截图确认布局（白底 / 纯黑加粗衬线 / 6 寸适配）
3. 测试 `meta refresh 300s`（等待 5 分钟）
4. 测试 XHR wttr.in（确认天气显示城市正确）
5. 测试离线提示（关闭 WiFi 确认离线条显示）

## 故障排查

### nginx 配置错误

```bash
sudo nginx -t           # 检查配置语法
sudo tail -f /var/log/nginx/ikindle_error.log
```

### cron 不执行

```bash
sudo systemctl status cron
grep CRON /var/log/syslog | tail -20
```

### HTTPS 证书过期

```bash
sudo certbot renew --dry-run   # 测试续期
sudo certbot renew             # 手动续期
sudo systemctl list-timers | grep certbot  # 检查自动续期 timer
```

### KINDLE 浏览器加载样式失败

```bash
# 检查 nginx MIME types
curl -I https://kindle.91api.vip/style.css
# 应该返回 Content-Type: text/css
```

### dashboard.html 不更新

```bash
# 检查 cron 是否执行
cat /home/ikindle/build.log | tail -20

# 手动跑一次构建
cd /home/ikindle && ./build.sh

# 检查缓存
curl -I https://kindle.91api.vip/dashboard.html
# 应该返回 Cache-Control: no-cache
```
