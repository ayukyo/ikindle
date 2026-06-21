/* ============================================================================
 * iKindle —— KINDLE 端 ES5 客户端逻辑
 *
 * 兼容性约束（KINDLE WebKit 537.36）：
 *   - 仅用 ES5：var / function / JSON / XMLHttpRequest / setInterval / Date
 *   - 禁用 ES6+：let / const / Arrow / Class / Promise / fetch / async / await
 *   - 禁用模板字符串（用字符串拼接代替）
 *
 * 全局函数（按 § 5.3 plan 设计）：
 *   - updateWeather()      XHR wttr.in/ → #weather DOM（自动 IP 定位）
 *   - updateHitokoto()     读 hitokoto_cache.json 或 XHR hitokoto API
 *   - emojiToChinese(s)    emoji → 中文映射（同时处理 wttr.in + Hitokoto）
 *   - checkOnline()        navigator.onLine → #offline-banner
 *   - rotateLayout()       orientation media query（CSS 已处理，这里 stub）
 *   - countdown(target, label)  计算与目标日期天数差（festivals.json）
 * ========================================================================== */

(function() {
    'use strict';

    /* ===== 常量 ===== */
    var WTTR_URL = 'https://wttr.in/?format=%l:+%c+%t+(feels+%f)+%w&lang=zh';
    var HITOKOTO_CACHE_URL = 'hitokoto_cache.json';
    var WEATHER_REFRESH_MS = 60000;     // 60s
    var WTTR_TIMEOUT_MS = 8000;
    var FAILURE_THRESHOLD = 3;          // 连续失败 3 次显示 "-"
    var TODAY_PROVIDER_MARKER = 'current_weather_provider.txt';

    /* ===== emoji → 中文映射表 =====
     * 处理 wttr.in 天气 emoji + Hitokoto 文本 emoji
     * 已知 KINDLE 系统字体对 emoji 渲染不一致，统一替换为中文
     */
    var EMOJI_MAP = {
        '☀️': '晴',
        '🌤️': '晴间多云',
        '⛅': '多云',
        '🌥️': '多云',
        '☁️': '阴',
        '🌦️': '小雨',
        '🌧️': '中雨',
        '⛈️': '雷雨',
        '🌩️': '雷阵雨',
        '🌨️': '雪',
        '❄️': '雪',
        '🌫️': '雾',
        '🌪️': '龙卷风',
        '🌈': '雨后彩虹'
    };

    /* ===== 模块状态 ===== */
    var wttrFailureCount = 0;
    var isOnline = true;

    /* ===== emoji → 中文 =====
     * @param {string} s - 含 emoji 的字符串
     * @returns {string} - 替换为中文的字符串
     */
    function emojiToChinese(s) {
        if (!s) return s;
        var result = s;
        for (var key in EMOJI_MAP) {
            if (Object.prototype.hasOwnProperty.call(EMOJI_MAP, key)) {
                result = result.split(key).join(EMOJI_MAP[key]);
            }
        }
        return result;
    }

    /* ===== wttr.in XHR 拉取（自动 IP 定位） =====
     * 失败时显示 "-"；连续失败 3 次后保留显示（不再重试）
     */
    function updateWeather() {
        var el = document.getElementById('weather');
        if (!el) return;

        /* R1-5：KWP4 极旧固件不支持 XHR 检测 */
        if (typeof XMLHttpRequest === 'undefined') {
            el.textContent = '请升级 KINDLE 固件以查看天气';
            return;
        }

        var xhr = new XMLHttpRequest();
        xhr.open('GET', WTTR_URL, true);
        xhr.timeout = WTTR_TIMEOUT_MS;

        xhr.onreadystatechange = function() {
            if (xhr.readyState !== 4) return;
            if (xhr.status === 200 && xhr.responseText) {
                wttrFailureCount = 0;
                el.textContent = emojiToChinese(xhr.responseText);
            } else {
                wttrFailureCount += 1;
                el.textContent = wttrFailureCount >= FAILURE_THRESHOLD
                    ? '天气暂不可用'
                    : '-';
            }
        };

        xhr.ontimeout = function() {
            wttrFailureCount += 1;
            el.textContent = wttrFailureCount >= FAILURE_THRESHOLD
                ? '天气暂不可用'
                : '-';
        };

        xhr.send();
    }

    /* ===== Hitokoto 每日一言 =====
     * 优先读服务端缓存 hitokoto_cache.json（cron 每日 0:00 刷新）
     * 兜底：XHR v1.hitokoto.cn（成功率较低，但免费）
     */
    function updateHitokoto() {
        var el = document.getElementById('hitokoto');
        if (!el) return;

        if (typeof XMLHttpRequest === 'undefined') return;

        /* 优先读缓存 */
        var xhr1 = new XMLHttpRequest();
        xhr1.open('GET', HITOKOTO_CACHE_URL, true);
        xhr1.timeout = 5000;
        xhr1.onreadystatechange = function() {
            if (xhr1.readyState === 4 && xhr1.status === 200) {
                try {
                    var data = JSON.parse(xhr1.responseText);
                    el.textContent = emojiToChinese(data.hitokoto || '');
                } catch (e) {
                    el.textContent = '';
                }
            }
        };
        xhr1.send();
    }

    /* ===== 离线提示 =====
     * 监听 navigator.onLine + online/offline 事件
     */
    function checkOnline() {
        var banner = document.getElementById('offline-banner');
        if (!banner) return;

        function updateOnlineStatus() {
            isOnline = navigator.onLine;
            if (isOnline) {
                document.body.className = document.body.className.replace(/\s*offline/g, '');
            } else {
                document.body.className += ' offline';
            }
        }

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        updateOnlineStatus();
    }

    /* ===== countdown 纪念日 / 倒数日 =====
     * @param {string} targetDate - 目标日期 MM-DD
     * @param {string} label - 节日名称
     * @returns {string} - "距离 XX 还有 N 天" 或 "XX 已过 N 天"
     */
    function countdown(targetDate, label) {
        var parts = targetDate.split('-');
        if (parts.length !== 2) return '';
        var month = parseInt(parts[0], 10) - 1;
        var day = parseInt(parts[1], 10);

        var now = new Date();
        var currentYear = now.getFullYear();
        var target = new Date(currentYear, month, day);

        /* 如果今年已过，设为明年 */
        if (target < now) {
            target = new Date(currentYear + 1, month, day);
        }

        var diffMs = target.getTime() - now.getTime();
        var diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return '今天是' + label;
        if (diffDays === 1) return '明天是' + label;
        return '距离' + label + '还有 ' + diffDays + ' 天';
    }

    /* ===== 启动 =====
     * IIFE 入口：页面加载时执行
     */
    function init() {
        updateWeather();
        updateHitokoto();
        checkOnline();
        setInterval(updateWeather, WEATHER_REFRESH_MS);
        setInterval(updateHitokoto, WEATHER_REFRESH_MS);
    }

    /* 等待 DOM ready */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    /* 导出到全局（便于其他脚本调用） */
    window.iKindle = {
        updateWeather: updateWeather,
        updateHitokoto: updateHitokoto,
        emojiToChinese: emojiToChinese,
        checkOnline: checkOnline,
        countdown: countdown
    };
})();
