# iKindle 下一步规划

**生成日期**：2026-06-21
**当前版本**：v0.1.0（测试验证阶段完成）
**状态**：19/19 测试通过，综合视觉评级 8/10

---

## 📋 总览

| 来源 | 项 | 优先级 | 性质 |
|---|---|---|---|
| 视觉走查遗留 | VIS-005 城市定位 | P1 | v0.2.0 必做 |
| 视觉走查遗留 | VIS-007 vw → px 重构 | P2 | 单独立项 |
| 视觉走查遗留 | VIS-008 真机对比 | P2 | 用户依赖 |
| 下一阶段选项 | v0.2.0 城市定位 | — | 功能规划 |
| 下一阶段选项 | v0.2.0 暗色主题 | — | 功能规划 |
| 下一阶段选项 | v0.2.0 月相 | — | 功能规划 |
| 下一阶段选项 | v0.2.0 多语言（英文版） | — | 功能规划 |
| 流程性 | 进入部署发布阶段 | — | 阶段推进 |

---

## 🔴 VIS-005 城市定位（必做，影响数据可信度）

### 问题
当前 build.sh 默认调用 `wttr.in` 按**服务器 IP 所在地**（美东 Lake Ridge）定位，输出的日出日落时间对国内用户毫无意义。截图里 "日出 05:45 / 日落 20:37" 对北京时间的用户来说是误导。

### 现状
- `build.sh` 调用：`curl -s 'https://wttr.in/?format=j1'`
- wttr.in 默认按调用方 IP 反查位置
- 已在 build.sh 注释中标记 defer

### 方案对比

#### 方案 A：环境变量传入城市（简单）
- **做法**：build.sh 读 `CITY` 环境变量，传入 wttr.in
  ```bash
  CITY="${CITY:-Beijing}"
  WTTR_JSON=$(curl -s "https://wttr.in/${CITY}?format=j1")
  ```
- **优点**：零额外代码，CI 友好
- **缺点**：每次构建只支持一个城市；用户切换需改 cron 配置
- **工作量**：30min

#### 方案 B：前端 JS 自动 IP 定位 + URL 参数
- **做法**：`app.js` 启动时调用 `https://ipapi.co/json/` 获取城市，访问 `/dashboard.html?city=Beijing`
- **优点**：用户零配置
- **缺点**：KINDLE 浏览器对跨域 fetch 支持差，可能回退
- **工作量**：2h

#### 方案 C：服务端 ip 反查 + build.sh 拼 URL
- **做法**：build.sh 调 `https://ipapi.co/json/` 取自己 IP 的城市，传给 wttr.in
- **优点**：和现状最接近
- **缺点**：服务器和用户地理位置往往不同（特别是部署到云上）
- **工作量**：1h

### 推荐
**先做方案 A**（v0.2.0 第一个 commit），保证数据准确；后续视用户反馈决定是否升级到 B/C。

### 验收标准
- `CITY=Beijing bash build.sh` 输出北京时间相符的日出日落
- 默认无 CITY 时输出兜底文案（如 "定位未配置"）
- 测试新增 `test_build.sh CITY env var`

---

## 🟡 VIS-007 vw → px 重构（单独立项，影响面大）

### 问题
`style.css` 全用 `vw` 单位（`font-size: 12vw` 等），但 KWP4 实机 viewport 是 **600×800 CSS 像素**，而 Chrome 模拟用 1072×1448。同一段代码在两个环境下渲染字号不一致：
- 实机：12vw = 72px
- Chrome 模拟：12vw = 128px（76% 偏大）

导致 Chrome 走查结论不能直接外推到实机。

### 风险
- 全量改动 237 行 CSS
- 需要回归所有字号/间距
- 在 KWP4 真机不可得的情况下，重构后无法充分验证

### 推荐路径
**不在 v0.2.0 做，等 VIS-008（真机图）回来之后再做**。否则改了不知道对不对。

### 预备动作（v0.2.0 顺便做）
- 在 `style.css` 顶部加注释，明确标注 viewport 假设（"基于 1072×1448 模拟，vw 在 KWP4 实机 600×800 viewport 下字号偏小约 44%"）
- 在 `visual-audit-v0.1.0.md` 顶部加显眼警告

### 重构方案（VIS-008 之后）
1. 改用 `px` 配合 `@media (max-width: 600px)` 媒体查询
2. 或 `rem` + 在 `<html>` 上根据 viewport 动态设 font-size
3. 完整测试套件（19/19）+ 实机图对比验证

---

## 🔒 VIS-008 真机对比（用户依赖）

### 缺失内容
- KWP4 Paperwhite 4 上 dashboard.html 的实机截图
- 用于校正 Chrome 灰度模拟的偏差

### 需要用户提供
1. 在 KWP4 上访问 `https://kindle.91api.vip/dashboard.html`
2. 截屏（菜单 → 截屏 → 保存到电脑）
3. 通过以下任一方式提供：
   - 文件上传到 `/home/admin/.openclaw/workspace/projects/ikindle/tests/kwp4_real_*.png`
   - 拖到 webchat（如果支持图片）
   - 直接贴到对话里

### 用法
- 更新 `docs/visual-audit-v0.1.0.md`，加入"实机对比"段落
- 标注哪些 Chrome 模拟结论被实机证伪
- 决定是否需要 v0.1.0 patch release

---

## 🚀 v0.2.0 功能规划（候选，需用户决策）

### 候选 A：暗色主题（黑底白字）
- **场景**：夜间 KINDLE 阅读体验
- **实现**：CSS 变量（KINDLE 不支持的话用 class 切换）+ localStorage
- **工作量**：3h
- **优先级**：⭐⭐⭐（夜间使用场景多）

### 候选 B：月相显示
- **场景**：月历区域扩展
- **实现**：新增 `phase` 占位符，build.sh 用算法算月相（参考 astronomical 算法）
- **工作量**：4h
- **优先级**：⭐⭐（视觉装饰价值）

### 候选 C：多语言（英文版）
- **场景**：海外华人 / 英文用户
- **实现**：`label_en` 已有，扩展 build.sh 支持 `LANG=en` 环境变量切换
- **工作量**：2h
- **优先级**：⭐⭐⭐（打开海外市场）

### 候选 D：番茄钟 / 计时器
- **场景**：KINDLE 当桌面计时器
- **实现**：app.js 加 setInterval，新页面 `/timer.html`
- **工作量**：6h
- **优先级**：⭐（与台历定位偏离）

### 推荐
**v0.2.0 优先三件套**：
1. VIS-005 城市定位（必做）
2. 候选 A 暗色主题
3. 候选 C 多语言

月相 B 和计时器 D 看用户兴趣。

---

## 📦 进入部署阶段（v0.1.0 收尾）

### 当前部署状态
- 仓库：`git@github.com:ayukyo/ikindle.git`（已推送 master）
- 域名：`https://kindle.91api.vip/`（已有 nginx 配置，参考 deploy/ 目录）
- CI：未配置（建议 GitHub Actions 跑 tests/run_all.sh）

### 收尾动作
1. **打 v0.1.0 tag**：`git tag -a v0.1.0 -m "iKindle v0.1.0: KINDLE 墨水屏台历首版"` + `git push --tags`
2. **写 CHANGELOG.md**：列出本次所有改动
3. **更新 README.md**：增加部署说明、已知问题（VIS-005/007/008）
4. **配置 GitHub Actions**：每次 push 自动跑 `tests/run_all.sh`

### 工作量
- tag + CHANGELOG：30min
- README 更新：1h
- GitHub Actions：1h

---

## 📅 建议时间线

```
本周（v0.1.0 收尾）
├── [30min] 打 v0.1.0 tag + CHANGELOG
├── [1h]    更新 README（部署说明 + 已知问题）
└── [1h]    配置 GitHub Actions

下周（v0.2.0 启动）
├── [30min] VIS-005 城市定位（方案 A）
├── [3h]    候选 A 暗色主题
├── [2h]    候选 C 多语言
└── [2h]    v0.2.0 测试 + 走查 + 文档

待定（依赖 VIS-008）
└── [3h+]   VIS-007 vw → px 重构（拿到真机图后启动）
```

---

## ❓ 需要用户决策的问题

1. **v0.2.0 优先做哪些功能**？（A 暗色主题 / B 月相 / C 多语言 / D 计时器）
2. **VIS-005 城市定位**选哪个方案？（A 环境变量 / B 前端 JS / C 服务端 IP）
3. **是否在 v0.1.0 收尾阶段就发布 GitHub Release**？
4. **能否在方便时提供 KWP4 真机截图**？

---

**维护说明**：本文档随项目进度更新。每次 dev-agent 完成一轮工作后，对应的"已完成"项会移入 `docs/CHANGELOG.md`。