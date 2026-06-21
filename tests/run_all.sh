#!/usr/bin/env bash
# ============================================================================
# tests/run_all.sh —— 运行所有单元测试 + 集成测试
#
# 用法：bash tests/run_all.sh
# ============================================================================
set -uo pipefail

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$TESTS_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "═══════════════════════════════════════════════════════════"
echo "  iKindle 测试套件"
echo "═══════════════════════════════════════════════════════════"
echo ""

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local cmd="$2"
    echo "[TEST] $name"
    echo "       $cmd"
    if eval "$cmd" > /tmp/test_output.log 2>&1; then
        echo "       ✅ PASS"
        PASS=$((PASS+1))
    else
        echo "       ❌ FAIL"
        tail -20 /tmp/test_output.log | sed 's/^/         /'
        FAIL=$((FAIL+1))
    fi
    echo ""
}

# ---- 1. 语法测试 ----
run_test "Bash 语法 (build.sh)" "bash -n build.sh"
run_test "Bash 语法 (refresh_hitokoto.sh)" "bash -n refresh_hitokoto.sh"
run_test "Bash 语法 (deploy/ssh_harden.sh)" "bash -n deploy/ssh_harden.sh"
run_test "Bash 语法 (deploy/install.sh)" "bash -n deploy/install.sh"
run_test "Python 语法 (lunar.py)" "python3 -m py_compile lunar.py"
run_test "Python 语法 (generate_calendar.py)" "python3 -m py_compile generate_calendar.py"
run_test "JS 语法 (app.js)" "node --check app.js"

# ---- 2. JSON 语法 ----
run_test "JSON 语法 (festivals.json)" "python3 -c \"import json; json.load(open('festivals.json'))\""
run_test "JSON 语法 (hitokoto_cache.json)" "python3 -c \"import json; json.load(open('hitokoto_cache.json'))\""

# ---- 2.5 Python 依赖检查（避免 lunar.py 静默降级）----
run_test "Python 依赖 (cnlunar)" "python3 -c 'import cnlunar'"

# ---- 3. 单元测试 ----
run_test "单元测试 (test_calendar.py)" "python3 -m unittest tests.test_calendar -v"
run_test "单元测试 (test_festivals.py)" "python3 -m unittest tests.test_festivals -v"
run_test "集成测试 (test_build.py)" "python3 -m unittest tests.test_build -v"
run_test "集成测试 (test_hitokoto.py)" "python3 -m unittest tests.test_hitokoto -v"

# ---- 4. 端到端 ----
run_test "端到端构建 (build.sh)" "bash build.sh"
run_test "dashboard.html 完整性" "test -f dashboard.html && grep -q '加载中' dashboard.html && ! grep -q '{{' dashboard.html"

# ---- 5. KWP4 模拟（用 Chrome headless）----
if command -v google-chrome >/dev/null 2>&1; then
    echo "[TEST] KWP4 viewport 截图 (Chrome headless)"
    mkdir -p /tmp/ikindle_screenshots
    # 启动本地 server
    python3 -m http.server 8766 > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 2

    google-chrome --headless --disable-gpu --no-sandbox \
        --window-size=1072,1448 --hide-scrollbars \
        --screenshot=/tmp/ikindle_screenshots/kpw4_test.png \
        http://localhost:8766/dashboard.html 2>&1 | grep -i error | head -3 || true

    kill $SERVER_PID 2>/dev/null

    if [ -f /tmp/ikindle_screenshots/kpw4_test.png ]; then
        SIZE=$(wc -c < /tmp/ikindle_screenshots/kpw4_test.png)
        if [ $SIZE -gt 5000 ]; then
            echo "       ✅ PASS (${SIZE} bytes)"
            PASS=$((PASS+1))
        else
            echo "       ❌ FAIL (截图太小: $SIZE bytes)"
            FAIL=$((FAIL+1))
        fi
    else
        echo "       ❌ FAIL (截图未生成)"
        FAIL=$((FAIL+1))
    fi
    echo ""
fi

echo "═══════════════════════════════════════════════════════════"
echo "  测试结果: $PASS 通过 / $FAIL 失败"
echo "═══════════════════════════════════════════════════════════"

[ $FAIL -eq 0 ] && exit 0 || exit 1
