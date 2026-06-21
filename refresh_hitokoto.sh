#!/usr/bin/env bash
# ============================================================================
# refresh_hitokoto.sh —— 每日 0:00 刷新 Hitokoto 缓存
#
# 输出：hitokoto_cache.json
# 内容：{"hitokoto": "...", "from": "...", "creator": "...", "created_at": "..."}
#
# Cron 配置：
#   0 0 * * * /home/ikindle/refresh_hitokoto.sh >> /home/ikindle/build.log 2>&1
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="$PROJECT_DIR/hitokoto_cache.json"
LOG="$PROJECT_DIR/build.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] refresh_hitokoto: $*" | tee -a "$LOG"
}

# 拉取 Hitokoto（优先官方 API，失败兜底默认一言）
RESP=$(curl -s --max-time 8 "https://v1.hitokoto.cn/?encode=text" 2>/dev/null || echo "")

if [ -z "$RESP" ]; then
    # 兜底默认一言
    RESP="生活不止眼前的苟且，还有诗和远方。"
    log "Hitokoto API 失败，使用兜底默认"
fi

# 构造 JSON（用 Python 安全转义）
python3 -c "
import json, sys
text = sys.argv[1]
data = {
    'hitokoto': text,
    'from': 'unknown',
    'creator': 'refresh_hitokoto.sh',
    'created_at': '$(date '+%Y-%m-%d %H:%M:%S')'
}
with open('$OUTPUT', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
" "$RESP"

log "Hitokoto 已缓存: $RESP"
