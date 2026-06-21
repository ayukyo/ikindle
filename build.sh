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
#   LANG=en ./build.sh                  # 英文版（i18n）
#   CITY=Beijing LANG=en ./build.sh     # 组合：英文 + 北京
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

# 日志函数（必须在 i18n 加载之前定义，因为 i18n 加载也用 log）
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

# ---- 0. 加载 i18n 字符串（按 LANG env var 选择 zh / en）----
# 注意：系统的 LANG 可能是 'en_US.UTF-8' / 'zh_CN.UTF-8'，只取前 2 位
# 同时用一个单独的 I18N_LANG env var 让用户可以强制指定（避免被系统 LANG 干扰）
RAW_LANG="${I18N_LANG:-${LANG:-zh}}"
LANG_CODE=$(echo "$RAW_LANG" | cut -d'_' -f1 | cut -d'.' -f1 | tr 'A-Z' 'a-z')
I18N_STRINGS=$(LANG="$LANG_CODE" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from i18n import get_strings
import json
s = get_strings('$LANG_CODE')
print(json.dumps(s, ensure_ascii=False))
")
# 提取常用字符串到 bash 变量
HTML_LANG=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['html_lang'])")
TITLE_STR=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['title'])")
META_DESC=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['meta_description'])")
META_KW=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['meta_keywords'])")
OG_TITLE=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['og_title'])")
OG_DESC=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['og_description'])")
OFFLINE_BANNER=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['offline_banner'])")
LOADING=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['loading'])")
WEEKDAY_TEMPLATE=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print('|'.join(json.loads(sys.stdin.read())['weekdays']))")
WEEK_NUMBER_TEMPLATE=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['week_number'])")
TODAY_NO_FESTIVAL=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['today_no_festival'])")
NO_COUNTDOWN=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['no_countdown'])")
COUNTDOWN_TPL=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['countdown_to'])")
SUNRISE_SUNSET_TPL=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['sunrise_sunset'])")
SUNRISE_SUNSET_UNAVAILABLE=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['sunrise_sunset_unavailable'])")
LOCATION_UNCONFIGURED=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['location_unconfigured'])")
LOCATION_FAILED=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['location_failed'])")
IP_FALLBACK_MARKER=$(echo "$I18N_STRINGS" | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['ip_fallback_marker'])")
log "i18n: lang=$LANG_CODE title=$TITLE_STR"

mkdir -p "$BUILD_DIR"
# 注意：OUTPUT 是项目根（保持 nginx root 配置兼容），但 BUILD_DIR 仍用于 wttr 健康状态文件

# ---- 1. 时间戳 ----
TIME_NOW=$(date "+%H:%M")
YEAR_NOW=$(date "+%Y")
MONTH_NOW=$(date "+%-m")   # 不补零的月份（英文月份用全称）
DAY_NOW=$(date "+%-d")
ISO_WEEK=$(date "+%V")
# DATE_NOW 用 i18n.format_date()
DATE_NOW=$(LANG="$LANG_CODE" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from i18n import format_date
print(format_date($YEAR_NOW, $MONTH_NOW, $DAY_NOW, '$LANG_CODE'))
")
log "构建: $DATE_NOW $TIME_NOW (ISO $ISO_WEEK, lang=$LANG_CODE)"

# ---- 2. 农历（尊重外部传入的 LUNAR_DATE 环境变量，用于回填历史）----
LUNAR_DATE="${LUNAR_DATE:-$(date '+%Y-%m-%d')}"
LUNAR_INFO_RAW=$(LUNAR_DATE="$LUNAR_DATE" python3 "$PROJECT_DIR/lunar.py" 2>/dev/null || echo "")
# 英文模式用 i18n.translate_lunar() 翻译
if [ "$LANG_CODE" = "en" ]; then
    LUNAR_INFO=$(LANG="$LANG_CODE" LUNAR_RAW="$LUNAR_INFO_RAW" python3 -c "
import sys, os
sys.path.insert(0, '$PROJECT_DIR')
from i18n import translate_lunar
print(translate_lunar(os.environ['LUNAR_RAW'], 'en'))
")
else
    LUNAR_INFO="$LUNAR_INFO_RAW"
fi
log "农历: $LUNAR_INFO"

# ---- 3. 月历 ----
CALENDAR_MONTH=$(LANG="$LANG_CODE" python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from i18n import format_calendar_month
print(format_calendar_month($YEAR_NOW, $MONTH_NOW, '$LANG_CODE'))
")
CALENDAR_HTML=$(LANG="$LANG_CODE" python3 "$PROJECT_DIR/generate_calendar.py" 2>/dev/null || echo "")

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
    WTTR_RESULT=$(echo "$WTTR_JSON" | python3 "$PROJECT_DIR/wttr_parse.py" "$SUNRISE_SUNSET_TPL" 2>/dev/null || echo "")
    # 用 sed 切：第一个 ^^^ 之前的部分作为 sunrise-sunset，之后作为 location
    SUNRISE_SUNSET=$(echo "$WTTR_RESULT" | sed 's/\^\^\^.*//')
    LOCATION=$(echo "$WTTR_RESULT" | sed 's/.*\^\^\^//')
fi

# 兜底：API 失败或解析失败时显示
if [ -z "$SUNRISE_SUNSET" ]; then
    if [ -n "${CITY:-}" ]; then
        SUNRISE_SUNSET="${SUNRISE_SUNSET_UNAVAILABLE}（${CITY}）"
        LOCATION="$LOCATION_FAILED"
    else
        SUNRISE_SUNSET="$SUNRISE_SUNSET_UNAVAILABLE"
        LOCATION="$LOCATION_UNCONFIGURED"
    fi
fi

# LOCATION 加来源标识（让用户知道数据是否可信）
if [ -n "${CITY:-}" ] && [ -n "$LOCATION" ] && [ "$LOCATION" != "$LOCATION_FAILED" ]; then
    # 用户显式指定 + 解析成功 → 显示 "城市 / 国家"
    LOCATION_DISPLAY="$LOCATION"
elif [ -z "${CITY:-}" ] && [ -n "$LOCATION" ]; then
    # IP 兜底 → 加 IP 定位警告
    LOCATION_DISPLAY="$LOCATION $IP_FALLBACK_MARKER"
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
    # 拆 COUNTDOWN_TPL 为两个变量（中文和英文模板）
    COUNTDOWN_TPL_EN='{n} days until {festival}'
    COUNTDOWN_TPL_ZH="$COUNTDOWN_TPL"
    FEST_INFO=$(TODAY_MM_DD="$TODAY_MM_DD" \
        I18N_JSON="$I18N_STRINGS" \
        COUNTDOWN_TPL_EN="$COUNTDOWN_TPL_EN" \
        COUNTDOWN_TPL_ZH="$COUNTDOWN_TPL_ZH" \
        python3 "$PROJECT_DIR/festivals_parse.py" "$FESTIVALS" 2>/dev/null || echo "")
    FEST_TODAY=$(echo "$FEST_INFO" | cut -d'|' -f1)
    COUNTDOWN=$(echo "$FEST_INFO" | cut -d'|' -f3)
    if [ -n "$FEST_TODAY" ]; then
        # 注：原版此处用 🎉 emoji 装饰，但 KINDLE 墨水屏 16 级灰阶下
        # emoji 渲染为灰块，反而干扰可读性。改为纯文字。
        FESTIVALS_TODAY="$FEST_TODAY"
    else
        # VIS-002：节日为空时给兜底文案，避免 dashboard.html 显示空白区域
        FESTIVALS_TODAY="$TODAY_NO_FESTIVAL"
    fi
    if [ -z "$COUNTDOWN" ]; then
        # 倒计时为空时兜底，避免空白
        COUNTDOWN="$NO_COUNTDOWN"
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

# 周几（按 LANG 切换）
weekdays = """$WEEKDAY_TEMPLATE""".split('|')
week_number_str = """$WEEK_NUMBER_TEMPLATE""".format(n='$ISO_WEEK')

replacements = {
    # i18n 占位符（head 部分）
    'HTML_LANG': """$HTML_LANG""",
    'TITLE': """$TITLE_STR""",
    'META_DESC': """$META_DESC""",
    'META_KW': """$META_KW""",
    'OG_TITLE': """$OG_TITLE""",
    'OG_DESC': """$OG_DESC""",
    'OFFLINE_BANNER': """$OFFLINE_BANNER""",
    'LOADING': """$LOADING""",
    # 月历
    'WEEK_NUMBER': week_number_str,
    'WEEKDAY_0': weekdays[0],
    'WEEKDAY_1': weekdays[1],
    'WEEKDAY_2': weekdays[2],
    'WEEKDAY_3': weekdays[3],
    'WEEKDAY_4': weekdays[4],
    'WEEKDAY_5': weekdays[5],
    'WEEKDAY_6': weekdays[6],
    # 动态数据
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
