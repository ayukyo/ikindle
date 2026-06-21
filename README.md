# iKindle —— 6 寸 KINDLE 墨水屏台历仪表盘

把一台 Kindle Paperwhite 4+（2018 及更新机型）改造成**桌面台历 / 信息仪表盘**，利用墨水屏物理特性（不发光、护眼、可长时间显示静态画面、纸质阅读体验）作为床头 / 书桌常驻屏。

**线上地址**：https://kindle.91api.vip/
**当前版本**：v0.1.0（[CHANGELOG](CHANGELOG.md)）

## ✨ 功能

- 🕐 **时间** —— 当前时分 + 日期副标题 + 农历（丙午年五月初六 庚寅日）
- 📅 **日历** —— 当月月历，今日加粗高亮，ISO 周数
- 🌦️ **天气** —— [wttr.in](https://wttr.in/)（默认按服务器 IP 定位，详见已知问题）
- 🎉 **传统节日** —— 春节 / 端午 / 中秋 / 国庆等
- 🌅 **日出日落** —— 实时天文数据（24h 制）
- 💬 **Hitokoto** —— 每日一言（每日 0:00 cron 缓存）
- 📴 **离线提示** —— 网络断开时友好降级
- 🔄 **30 分钟刷新** —— 平衡墨水屏体验和电池寿命

## 📦 技术栈

- **前端**：HTML5 + CSS3 + ES5 JavaScript（KINDLE WebKit 537.36 兼容）
- **构建**：cron + bash + sed + curl + Python `cnlunar`
- **部署**：阿里云 Linux + nginx + Let's Encrypt + certbot
- **数据源**：[wttr.in](https://wttr.in/)（IP 自动定位）+ [v1.hitokoto.cn](https://hitokoto.cn/) + 农历计算库

## 🚀 快速开始

### 本地预览（开发）

```bash
git clone <repository>  # 注：CLAUDE.md 全局规则禁止 git commit/push，但允许 git clone
cd ikindle
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000/dashboard.html
```

### 手动构建

```bash
./build.sh   # 生成 dashboard.html（注入时间戳、农历、日历、节日）
```

### 部署到阿里云 Linux

详见 [deploy/README.md](deploy/README.md)。

## 📁 项目结构

```
ikindle/
├── index.html              # 主页（SEO 强）
├── install.html            # 部署指南（HowTo JSON-LD）
├── about.html              # 关于
├── screenshots.html        # 截图展示（ImageObject JSON-LD）
├── changelog.html          # 更新日志
├── dashboard.html          # 动态仪表盘（构建期生成，gitignore 忽略）
├── style.css               # 墨水屏台历样式
├── app.js                  # ES5 客户端逻辑（KINDLE 兼容）
├── sitemap.xml             # 站点地图
├── robots.txt              # 爬虫指令
├── build.sh                # 主构建脚本（cron 每分钟）
├── refresh_hitokoto.sh     # Hitokoto 缓存刷新（cron 每日 0:00）
├── lunar.py                # 农历计算（依赖 cnlunar）
├── generate_calendar.py    # 月历生成
├── festivals.json          # 节日配置
├── hitokoto_cache.json     # Hitokoto 缓存（cron 生成）
├── templates/
│   └── dashboard.html      # dashboard 模板（含占位符）
├── deploy/
│   ├── nginx.conf          # nginx 配置
│   ├── crontab             # cron 配置
│   ├── ssh_harden.sh       # SSH 加固脚本
│   └── README.md           # 部署文档
├── assets/                 # 截图占位目录
├── .gitignore              # Git 忽略
├── LICENSE                 # MIT License
└── README.md               # 本文件
```

## 🧪 测试

本项目有完整的自动化测试套件（19 项，CI 集成在 GitHub Actions）。

```bash
# 安装依赖（cnlunar）
pip3 install --user -r requirements.txt

# 一键运行所有测试
bash tests/run_all.sh

# 单独运行某个测试
python3 -m unittest tests.test_build -v
```

测试覆盖：
- Bash / Python / JS 语法检查
- JSON 语法
- Python 依赖可导入性
- 单元测试（月历生成 / 节日匹配）
- 集成测试（build.sh / refresh_hitokoto.sh 端到端）
- E-Ink 灰度模拟截图（Chrome headless + CSS filter）

## ⚠️ 已知问题

详见 [docs/visual-audit-v0.1.0.md](docs/visual-audit-v0.1.0.md)。

- **VIS-005（v0.2.0 修复）**：build.sh 中 wttr.in 默认按**服务器 IP 定位**（美东时间），输出对国内用户无意义。v0.2.0 将支持 `CITY` 环境变量。
- **VIS-007（待真机图）**：CSS 使用 vw 单位，KWP4 实机 viewport（600×800 CSS px）下字号可能偏小。
- **VIS-008（等用户）**：所有视觉走查基于 Chrome 灰度模拟，未在 KWP4 真机验证。

## 📅 下一步规划

详见 [docs/next-steps.md](docs/next-steps.md)。

## 🎯 目标设备

| 机型 | 发布年 | 兼容性 |
|------|--------|--------|
| Kindle Paperwhite 4 (10th gen) | 2018 | ✅ 主要目标 |
| Kindle Paperwhite 5 (11th gen) | 2021 | ✅ |
| Kindle Paperwhite Signature (11th gen) | 2021 | ✅ |
| Kindle Basic 11th | 2022 | ✅ |
| Kindle Scribe | 2022 | ✅ |
| Oasis 10 / Basic 10 | 2019 | ✅ 同代 WebKit 537.36 |
| Colorsoft | 2024 | ✅ 浏览器内核一致 |

## 🔧 KINDLE 浏览器兼容性

基于 WebKit 537.36（~Chromium 28-35 时代）：

- ✅ 支持：HTML5 语义标签 / Flexbox / `@keyframes` / SVG `<animate>` / ES5 (`var`/`function`/`JSON`/`XHR`)
- ❌ 禁用：`let`/`const`/Arrow/Class/Promise/fetch / CSS 变量 / CSS Grid / `position: sticky`
- ⚠️ 谨慎：`localStorage` / CSS 3D transform / 复杂 CORS 跨域

## 📜 License

MIT License —— 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [wttr.in](https://github.com/chubin/wttr.in) —— 免费的天气 API + CORS 友好
- [Hitokoto](https://hitokoto.cn/) —— 每日一言的开源 API
- [cnlunar](https://github.com/OPN48/cnlunar) —— Python 农历 / 干支计算
- [Let's Encrypt](https://letsencrypt.org/) —— 免费 HTTPS 证书
- [online-screensaver](https://github.com/ypcrts/online-screensaver) —— KINDLE 屏保替换项目灵感
- [MobileRead Kindle Hacking Wiki](https://wiki.mobileread.com/wiki/Kindle_Touch_Hacking) —— KPW4 浏览器兼容性资料

## 🔗 相关链接

- **线上地址**：https://kindle.91api.vip/
- **部署文档**：[deploy/README.md](deploy/README.md)
- **更新日志**：[changelog.html](changelog.html)（线上）或 [changelog.html](changelog.html)
