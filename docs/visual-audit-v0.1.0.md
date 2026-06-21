# iKindle v0.1.0 视觉走查报告

**走查日期**：2026-06-21
**走查方式**：Chrome headless + CSS `filter: grayscale(1)` 模拟 16 级灰阶墨水屏（KWP4 viewport 1072×1448）
**走查工具**：`tests/eink_screenshot.py`
**截图归档**：`/tmp/ikindle_grayscale/kpw4_eink_<timestamp>.png`

---

## 综合评级

| 维度 | 评分 | 备注 |
|---|---|---|
| 布局完整性 | 8/10 | 单列堆叠正常，所有元素均在 viewport 内 |
| 字号梯度 | 8/10 | 时间(12vw) > 日期(3.5vw) > 农历(2.8vw) > 天气(2.5vw) > 日历(2.4vw) > Hitokoto(2.2vw)，层次合理 |
| 灰阶可读性 | 6/10 | 主要文字清晰，但 emoji 和浅灰细节会糊 |
| emoji 适配 | 3/10 | 🔅(today标记)、🌅(日出日落符号) 在 16 级灰阶下变成灰块 |
| 字体选择 | 7/10 | 回退链合理，但实际渲染依赖系统字体，非 KINDLE 内置字体 |
| 横屏适配 | 7/10 | media query 实现左右两栏，但未实测横屏效果 |
| **综合** | **7/10** | 主功能可用，但 emoji 和装饰元素需要优化 |

---

## 发现的问题清单

### 🔴 P0（影响核心可读性，建议 v0.1.0 修复）

#### VIS-001：emoji 在 16 级灰阶下变成灰块
- **位置**：`dashboard.html` 全局
- **现象**：🔅 (today 边框装饰)、🌅 / 🌇 (日出日落 emoji) 在墨水屏上是大灰色块
- **影响**：today 标记的视觉提示失效；日出日落信息可能被误读为文字
- **现状**：CSS `.calendar-day.today` 用 `border: 0.4vw solid #000000` 已经有边框，emoji 实际是冗余的——但 build.sh 里没看到 emoji 来源，需要 grep
- **修复方向**：移除装饰性 emoji，或换成纯文字 + border 样式
- **工作量**：30min（grep + 删 + 测试）

#### VIS-002：`festival-today` / `countdown` 内容为空
- **位置**：`dashboard.html` `<section class="festivals">`
- **现象**：节日 / 倒计时 div 渲染为空（HTML 里有元素但没内容）
- **原因猜测**：build.sh 里 FESTIVALS_TODAY 走 python 解析但可能匹配失败；或者解析成功但当日确实无节日（2026-06-21 不在 festivals.json 列表中）
- **影响**：v0.1.0 承诺"传统节日"功能，体验不完整
- **修复方向**：先用 `jq` / `python` 验证 build.sh 解析逻辑；考虑兜底文案"今日无节日"
- **工作量**：1h

### 🟡 P1（视觉优化，建议 v0.2.0 处理）

#### VIS-003：横屏布局未实测
- **位置**：`style.css` `@media (orientation: landscape)`
- **现象**：代码定义了横屏两栏布局，但 eink_screenshot.py 只截了竖屏
- **影响**：用户横屏使用（罕见但 KINDLE 可以）可能布局错乱
- **修复方向**：eink_screenshot.py 增加 `--window-size=1448,1072` 横屏截图选项
- **工作量**：20min

#### VIS-004：天气信息英文/中文混排
- **位置**：`build.sh` 中 wttr.in 处理
- **现象**：日出日落显示 "日出 05:45 AM / 日落 08:37 PM"——AM/PM 在中文语境下不规范
- **影响**：细节体验，不影响功能
- **修复方向**：build.sh 解析时去掉 AM/PM 后缀，统一用 24 小时制 "日出 05:45 / 日落 20:37"
- **工作量**：15min

#### VIS-005：日落时间解析不正确
- **位置**：`build.sh` 第 60-67 行
- **现象**：截图显示 "日出 05:45 AM / 日落 08:37 PM"，但截图生成时间为 21:16（晚上 9 点），墨水屏实际应该显示接近 19:30 左右（夏季北京日落时间），8:37 PM 偏晚
- **影响**：数据可信度问题
- **原因猜测**：wttr.in 定位不准（默认位置可能不是用户城市）；或 j1 字段时间格式解析错误
- **修复方向**：先用 `curl 'https://wttr.in/?format=j1' | jq` 验证返回数据；考虑用 `?format=%S` 简版
- **工作量**：1h（含 wttr.in 行为调研）

#### VIS-006：刷新频率过高（5 分钟）
- **位置**：`dashboard.html` `<meta http-equiv="refresh" content="300">`
- **现象**：墨水屏每 5 分钟全帧刷新，会显著缩短 KINDLE 电池寿命
- **影响**：长期使用不便
- **修复方向**：改为 30 分钟（1800s）或 60 分钟；或者只在整点刷新
- **工作量**：5min（改 HTML 中数字）

### 🟢 P2（Nice-to-have，可选）

#### VIS-007：CSS 用 vw 单位但 KINDLE viewport 计算可能不一致
- **位置**：`style.css` 全部
- **现象**：设计稿 1072×1448 viewport 适配良好，但 KINDLE Paperwhite 4 实际 viewport 是 600×800（CSS 像素），vw 单位在实机可能算出来字号偏小
- **影响**：实机字号偏小
- **修复方向**：用 px + media query 替代 vw；或提供 rem 兜底
- **工作量**：2h（含全量重测）

#### VIS-008：缺少 KWP4 实机对比图
- **位置**：本文档本身
- **现象**：所有判断基于 Chrome 灰度模拟，未在真机验证
- **影响**：走查结论可信度受限
- **修复方向**：用户拍 KWP4 实机截图后更新本报告，校正偏差项
- **工作量**：取决于用户

#### VIS-009：Hitokoto 字体可能与 KINDLE 不兼容
- **位置**：`style.css` font-family
- **现象**：font-family 优先 Georgia / Source Han Serif，但 KINDLE 实机只有 Caecilia + 内置中文字体
- **影响**：Hitokoto 中文部分可能回退到默认字体
- **修复方向**：调查 KINDLE Paperwhite 4 内置字体清单，针对性调整 font-family
- **工作量**：1h 调研

---

## 截图归档

每次跑 `tests/eink_screenshot.py` 会生成：
```
/tmp/ikindle_grayscale/kpw4_eink_<YYYYMMDD_HHMMSS>.png
```

可在 CI 中归档对比。

---

## 走查方法说明

### 为什么用 Chrome + CSS filter 而不是真机？

1. **可重入性**：CI 友好，每次跑都一致
2. **速度快**：< 2s 出图
3. **不依赖硬件**：开发者无需 KINDLE

### 它和真机的差距

| 维度 | Chrome 灰度模拟 | 真机 KWP4 |
|---|---|---|
| 颜色空间 | RGB → CSS filter | 16 级灰阶 |
| 字体 | Linux 字体 | KINDLE 内置字体 |
| 抗锯齿 | 可关闭 | 默认无 |
| 渲染速度 | 即时 | 慢（每屏 1s） |
| JavaScript | 现代 ES2020+ | 老 WebKit |
| emoji | 彩色 → 灰阶 | 灰阶但样式不同 |

### 走查结论可信度

- **布局**：可信（CSS 布局在两边都一致）
- **字号**：可信（vw 计算逻辑一致）
- **颜色对比**：可信（16 灰阶接近模拟）
- **emoji 行为**：部分可信（emoji 字体不同）
- **字体渲染**：不可信（字体完全不同）
- **JS 行为**：不可信（需真机跑 app.js）

---

## 后续建议

1. **立即做**：VIS-001（emoji）、VIS-002（节日空）、VIS-006（刷新频率）
2. **下版本做**：VIS-004、VIS-005（日出日落规范化）
3. **真机拿到后**：校正 VIS-008，更新本报告
4. **长期重构**：VIS-007（vw → px 重构）、VIS-009（字体适配）