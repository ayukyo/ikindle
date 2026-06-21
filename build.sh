#!/usr/bin/env bash
# ============================================================================
# build.sh —— 构建 iKindle dashboard.html
#
# 工作流程：
#   1. date 生成时间戳 / 日期 / ISO 周数
#   2. python3 lunar.py 生成农历信息
#   3. python3 generate_calendar.py 生成当月月历
#   4. curl wttr.in (j1) 获取日出日落
#   5. 读取 festivals.json / hitokoto_cache.json
#   6. sed 替换占位符 → 输出 build/dashboard.html
#
# 用法：
#   ./build.sh                  # 构建当前时刻
#   LUNAR_DATE=2026-12-31 ./build.sh   # 指定日期构建（用于回填历史）
#
# 失败处理：
#   - set -euo pipefail：任何命令失败立即退出
#   - wttr.in 失败：保留上次成功 build/dashboard.html
#   - 农历 / 日历失败：占位符留空字符串
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
TEMPLATE="$PROJECT_DIR/templates/dashboard.html"
# 注意：dashboard.html 输出到项目根（而非 build/），便于 nginx 直接服务 + sitemap.xml 链接正确
OUTPUT="$PROJECT_DIR/dashboard.html"
FESTIVALS="$PROJECT_DIR/festivals.json"
HITOKOTO_CACHE="$PROJECT_DIR/hitokoto_cache.json"
LOG="$PROJECT_DIR/build.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

mkdir -p "$BUILD_DIR"
# 注意：OUTPUT 是项目根（保持 nginx root 配置兼容），但 BUILD_DIR 仍用于 wttr 健康状态文件

# ---- 1. 时间戳 ----
TIME_NOW=$(date "+%H:%M")
DATE_NOW=$(date "+%Y年%m月%d日")
ISO_WEEK=$(date "+%V")
log "构建: $DATE_NOW $TIME_NOW (ISO $ISO_WEEK)"

# ---- 2. 农历（尊重外部传入的 LUNAR_DATE 环境变量，用于回填历史）----
LUNAR_DATE="${LUNAR_DATE:-$(date '+%Y-%m-%d')}"
LUNAR_INFO=$(LUNAR_DATE="$LUNAR_DATE" python3 "$PROJECT_DIR/lunar.py" 2>/dev/null || echo "")
log "农历: $LUNAR_INFO"

# ---- 3. 月历 ----
CALENDAR_MONTH=$(date "+%Y年%m月")
CALENDAR_HTML=$(python3 "$PROJECT_DIR/generate_calendar.py" 2>/dev/null || echo "")

# ---- 4. 日出日落（VIS-005 城市定位 + VIS-004 24h 制）----
SUNRISE_SUNSET=""
LOCATION=""
CITY_SOURCE=""  # 记录定位来源，用于日志和兜底

# wttr.in URL：支持 /<city> 路径传城市名（也支持 IP 反查）
# 注：CITY 可能未设置（set -u 时会抛 unbound），用 ${CITY:-} 兜底
if [ -n "${CITY:-}" ]; then
    # 用户显式指定城市：URL-encode 空格为 %20 / 中文为 UTF-8
    CITY_ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$CITY")
    WTTR_URL="https://wttr.in/${CITY_ENCODED}?format=j1"
    CITY_SOURCE="env:CITY=$CITY"
else
    # 未指定：默认按服务器 IP 定位（兜底，对国内用户可能不准确）
    WTTR_URL="https://wttr.in/?format=j1"
    CITY_SOURCE="ip-fallback"
fi
log "日出日落查询: $WTTR_URL ($CITY_SOURCE, encoded=${CITY_ENCODED:-none})"

WTTR_JSON=$(curl -s --max-time 8 "$WTTR_URL" 2>/dev/null || echo "")
if [ -n "$WTTR_JSON" ] && command -v python3 >/dev/null 2>&1; then
    WTTR_RESULT=$(echo "$WTTR_JSON" | python3 -c "
import json, sys, re
def to_24h(s):
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', s.strip(), re.IGNORECASE)
    if not m:
        return s
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).upper()
    if ap == 'PM' and h != 12:
        h += 12
    elif ap == 'AM' and h == 12:
        h = 0
    return '%02d:%s' % (h, mi)
try:
    d = json.loads(sys.stdin.read())
    today = d['weather'][0]
    sunrise = to_24h(today['astronomy'][0]['sunrise'])
    sunset = to_24h(today['astronomy'][0]['sunset'])
    area = d.get('nearest_area', [{}])[0]
    city_name = area.get('areaName', [{}])[0].get('value', '')
    country = area.get('country', [{}])[0].get('value', '')
    sun_str = '日出 ' + sunrise + ' / 日落 ' + sunset
    loc_str = ''
    if city_name:
        loc_str = city_name
        if country and country != city_name:
            loc_str += ' / ' + country
    print(sun_str + '^^^' + loc_str)
except Exception:
    pass
" 2>/dev/null || echo "")
    # 用 sed 切：第一个 ^^^ 之前的部分作为 sunrise-sunset，之后作为 location
    SUNRISE_SUNSET=$(echo "$WTTR_RESULT" | sed 's/\^\^\^.*//')
    LOCATION=$(echo "$WTTR_RESULT" | sed 's/.*\^\^\^//')
fi

# 兜底：API 失败或解析失败时显示
if [ -z "$SUNRISE_SUNSET" ]; then
    if [ -n "${CITY:-}" ]; then
        SUNRISE_SUNSET="日出日落暂不可用（城市: $CITY）"
        LOCATION="定位失败"
    else
        SUNRISE_SUNSET="日出日落暂不可用（未配置城市）"
        LOCATION="未配置城市"
    fi
fi

# LOCATION 加来源标识（让用户知道数据是否可信）
if [ -n "${CITY:-}" ] && [ -n "$LOCATION" ] && [ "$LOCATION" != "定位失败" ]; then
    # 用户显式指定 + 解析成功 → 显示 "城市 / 国家"
    LOCATION_DISPLAY="$LOCATION"
elif [ -z "${CITY:-}" ] && [ -n "$LOCATION" ]; then
    # IP 兜底 → 加 "（IP 定位，可能不准确）" 警告
    LOCATION_DISPLAY="$LOCATION （IP 定位）"
else
    LOCATION_DISPLAY="$LOCATION"
fi
LOCATION="$LOCATION_DISPLAY"

log "日出日落: $SUNRISE_SUNSET"
log "城市定位: $LOCATION"

# ---- 5. 节日 / Hitokoto ----
FESTIVALS_TODAY=""
COUNTDOWN=""
TODAY_MM_DD=$(date "+%m-%d")
if [ -f "$FESTIVALS" ] && command -v python3 >/dev/null 2>&1; then
    FEST_INFO=$(TODAY_MM_DD="$TODAY_MM_DD" python3 -c "
import json, os
try:
    with open('$FESTIVALS', 'r', encoding='utf-8') as f:
        data = json.load(f)
    today = os.environ.get('TODAY_MM_DD', '')
    labels = []
    countdown = ''
    for item in data:
        if item.get('date') == today:
            # i18n：第一版默认中文（label_zh），未来可根据浏览器 locale 切换
            labels.append(item.get('label_zh', item.get('label_en', '')))
        elif item.get('countdown') and item.get('date') and not item['date'].startswith('L') and not item['date'].startswith('MEM'):
            # 计算距今天数（仅对公历日期）
            try:
                from datetime import datetime
                now = datetime.now()
                # 修复：使用动态年份而非硬编码 '2026-'
                target = datetime.strptime(str(now.year) + '-' + item['date'], '%Y-%m-%d')
                if target < now:
                    target = target.replace(year=now.year + 1)
                diff = (target - now).days
                if 0 < diff <= 30:
                    countdown = '距离' + item.get('label_zh', item.get('label_en', '')) + '还有 ' + str(diff) + ' 天'
                    break
            except Exception:
                pass
    print('|'.join(labels) + '||' + countdown)
except Exception as e:
    pass
" 2>/dev/null || echo "")
    FEST_TODAY=$(echo "$FEST_INFO" | cut -d'|' -f1)
    COUNTDOWN=$(echo "$FEST_INFO" | cut -d'|' -f3)
    if [ -n "$FEST_TODAY" ]; then
        # 注：原版此处用 🎉 emoji 装饰，但 KINDLE 墨水屏 16 级灰阶下
        # emoji 渲染为灰块，反而干扰可读性。改为纯文字。
        FESTIVALS_TODAY="$FEST_TODAY"
    else
        # VIS-002：节日为空时给兜底文案，避免 dashboard.html 显示空白区域
        FESTIVALS_TODAY="今日无节日"
    fi
    if [ -z "$COUNTDOWN" ]; then
        # 倒计时为空时兜底，避免空白
        COUNTDOWN="近期无倒计时"
    fi
fi

HITOKOTO=""
if [ -f "$HITOKOTO_CACHE" ]; then
    HITOKOTO=$(python3 -c "
import json
try:
    with open('$HITOKOTO_CACHE', 'r', encoding='utf-8') as f:
        d = json.load(f)
    print(d.get('hitokoto', ''))
except Exception:
    pass
" 2>/dev/null || echo "")
fi

# ---- 6. 占位符替换（用 Python 处理多行变量，避免 sed 多行 bug）----
# 把所有占位符值写入临时 JSON 文件（安全转义多行 / emoji / 特殊字符）
python3 << PYEOF
import json
replacements = {
    'TIME': """$TIME_NOW""",
    'DATE': """$DATE_NOW""",
    'LUNAR': """$LUNAR_INFO""",
    'ISO_WEEK': """$ISO_WEEK""",
    'CALENDAR_MONTH': """$CALENDAR_MONTH""",
    'CALENDAR': """$CALENDAR_HTML""",
    'SUNRISE_SUNSET': """$SUNRISE_SUNSET""",
    'LOCATION': """$LOCATION""",
    'FESTIVALS_TODAY': """$FESTIVALS_TODAY""",
    'COUNTDOWN': """$COUNTDOWN""",
    'HITOKOTO': """$HITOKOTO"""
}
with open('$TEMPLATE', 'r', encoding='utf-8') as f:
    template = f.read()
for key, value in replacements.items():
    template = template.replace('{{' + key + '}}', value)
with open('$OUTPUT', 'w', encoding='utf-8') as f:
    f.write(template)
PYEOF

log "输出: $OUTPUT"

# ---- 7. 健康检测（切换 wttr.in → Open-Meteo）----
WTTR_HEALTH_FILE="$BUILD_DIR/.wttr_health"
WTTR_FAILURE_COUNT=$(cat "$WTTR_HEALTH_FILE" 2>/dev/null || echo 0)
if [ -z "$WTTR_JSON" ]; then
    WTTR_FAILURE_COUNT=$((WTTR_FAILURE_COUNT + 1))
    echo "$WTTR_FAILURE_COUNT" > "$WTTR_HEALTH_FILE"
    log "wttr.in 失败（连续 $WTTR_FAILURE_COUNT 次）"
    if [ "$WTTR_FAILURE_COUNT" -ge 3 ]; then
        echo "open-meteo" > "$BUILD_DIR/current_weather_provider.txt"
        log "切换到 Open-Meteo 备用 API"
    fi
else
    echo 0 > "$WTTR_HEALTH_FILE"
    echo "wttr.in" > "$BUILD_DIR/current_weather_provider.txt"
fi

log "构建完成"
