# Changelog

iKindle 所有版本的变更记录。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Planned
- VIS-005 城市定位（v0.2.0）
- v0.2.0 候选功能：暗色主题 / 多语言 / 月相 / 番茄钟

---

## [0.1.0] - 2026-06-21

首个可用版本。基础台历仪表盘 + 完整测试套件 + 视觉走查。

### ✨ Features
- **基础静态页** —— index / install / about / screenshots / changelog
- **动态仪表盘** —— dashboard.html + app.js（ES5 兼容 KINDLE WebKit 537.36）
- **构建脚本** —— build.sh + lunar.py + generate_calendar.py
- **节日配置** —— festivals.json（公历/农历/纪念日，i18n 双语）
- **部署配置** —— nginx + cron + ssh_harden
- **SEO 资源** —— sitemap.xml + robots.txt + JSON-LD

### 🧪 Testing
- 新增 `tests/test_calendar.py` —— generate_calendar.py 单元测试
- 新增 `tests/test_festivals.py` —— festivals.json + 农历匹配测试
- 新增 `tests/test_build.py` —— build.sh 端到端集成测试
- 新增 `tests/test_hitokoto.py` —— refresh_hitokoto.sh 端到端集成测试
- 新增 `tests/eink_screenshot.py` —— E-Ink 灰度模拟截图（portrait + landscape）
- 新增 `tests/run_all.sh` —— 一键运行所有测试
- **结果**：19/19 通过

### 🐛 Bug Fixes
- **FIX-001**：test_build.py 兼容 Python 3.6（subprocess.run 不用 capture_output）
- **FIX-002**：补装 cnlunar 依赖（lunar.py 不再静默降级）
- **FIX-003**：意外 commit state.json → 加 .gitignore 隔离 dev-agent 内部档案

### 🎨 Visual Audit
- 发布 `docs/visual-audit-v0.1.0.md`，识别 9 项视觉问题
- **VIS-001**（P0）：移除装饰性 emoji 🎉（墨水屏 16 级灰阶下糊成灰块）
- **VIS-002**（P0）：节日/倒计时为空时兜底文案
- **VIS-003**（P1）：eink_screenshot 支持横屏验证
- **VIS-004**（P1）：日出日落改 24h 制（去除 AM/PM）
- **VIS-006**（P1）：刷新频率 5min → 30min（省电）
- **VIS-009**（P2）：字体优先 KINDLE 内置 Caecilia / Bookerly
- **VIS-005**（P1）：wttr.in 按服务器 IP 定位 → defer 到 v0.2.0
- **VIS-007**（P2）：vw → px 重构 → defer（需真机图验证）
- **VIS-008**（P2）：缺 KWP4 实机对比图 → 等待用户

### 📦 Dependencies
- 新增 `requirements.txt`：cnlunar>=0.2,<1.0
- 测试增加 Python 依赖导入检查项

### 📚 Documentation
- 新增 `docs/visual-audit-v0.1.0.md` —— 视觉走查报告
- 新增 `docs/next-steps.md` —— 下一步规划
- 新增 `CHANGELOG.md`（本文件）

### ⚠️ Known Issues
- **VIS-005**：日出日落数据按服务器 IP 定位（美东时间），对国内用户无效
- **VIS-007**：CSS 用 vw 单位，实机字号可能偏小
- **VIS-008**：未在 KWP4 真机验证，所有走查基于 Chrome 灰度模拟

---

## 版本历史

- **0.1.0** (2026-06-21) —— 初版