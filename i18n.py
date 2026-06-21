#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n.py —— iKindle 国际化字符串字典

用法：
    from i18n import get_strings
    s = get_strings('en')
    print(s['title'])

支持语言：
    - zh（默认）：简体中文
    - en：英文

新加语言：
    在 STRINGS 字典加 'xx': {...} 键
"""
import os


# 月份英文缩写 / 全称（用于英文版日期和月历标题）
EN_MONTHS_FULL = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
EN_MONTHS_SHORT = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

# 干支英文（10 天干 + 12 地支）
HEAVENLY_STEMS_EN = {
    '甲': 'Jia', '乙': 'Yi', '丙': 'Bing', '丁': 'Ding', '戊': 'Wu',
    '己': 'Ji', '庚': 'Geng', '辛': 'Xin', '壬': 'Ren', '癸': 'Gui'
}
EARTHLY_BRANCHES_EN = {
    '子': 'Zi', '丑': 'Chou', '寅': 'Yin', '卯': 'Mao', '辰': 'Chen',
    '巳': 'Si', '午': 'Wu', '未': 'Wei', '申': 'Shen', '酉': 'You',
    '戌': 'Xu', '亥': 'Hai'
}

# 生肖英文
ZODIAC_EN = {
    '鼠': 'Rat', '牛': 'Ox', '虎': 'Tiger', '兔': 'Rabbit',
    '龙': 'Dragon', '蛇': 'Snake', '马': 'Horse', '羊': 'Goat',
    '猴': 'Monkey', '鸡': 'Rooster', '狗': 'Dog', '猪': 'Pig'
}

# 节气中英文映射（cnlunar 输出中文）
SOLAR_TERMS_EN = {
    '立春': 'Beginning of Spring', '雨水': 'Rain Water', '惊蛰': 'Awakening of Insects',
    '春分': 'Spring Equinox', '清明': 'Pure Brightness', '谷雨': 'Grain Rain',
    '立夏': 'Beginning of Summer', '小满': 'Lesser Fullness of Grain',
    '芒种': 'Grain in Ear', '夏至': 'Summer Solstice', '小暑': 'Lesser Heat',
    '大暑': 'Greater Heat', '立秋': 'Beginning of Autumn', '处暑': 'End of Heat',
    '白露': 'White Dew', '秋分': 'Autumn Equinox', '寒露': 'Cold Dew',
    '霜降': "Frost's Descent", '立冬': 'Beginning of Winter',
    '小雪': 'Lesser Snow', '大雪': 'Greater Snow', '冬至': 'Winter Solstice',
    '小寒': 'Lesser Cold', '大寒': 'Greater Cold'
}


STRINGS = {
    'zh': {
        'html_lang': 'zh-CN',
        'title': 'iKindle 台历',
        'meta_description': 'iKindle —— 6 寸 KINDLE 墨水屏台历仪表盘。自动定位城市、显示农历、传统节日、Hitokoto。',
        'meta_keywords': 'kindle, dashboard, paperwhite, e-ink, 台历, 墨水屏, 桌面, 时钟, 日历, 天气',
        'og_title': 'iKindle 台历',
        'og_description': '6 寸 KINDLE 墨水屏台历仪表盘',
        'weekdays': ['日', '一', '二', '三', '四', '五', '六'],
        'week_number': '第 {n} 周',
        'offline_banner': '网络已断开，部分功能不可用',
        'loading': '加载中...',
        'today_no_festival': '今日无节日',
        'no_countdown': '近期无倒计时',
        'countdown_to': '距离{festival}还有 {n} 天',
        'sunrise_sunset': '日出 {sr} / 日落 {ss}',
        'sunrise_sunset_unavailable': '日出日落暂不可用',
        'location_unconfigured': '未配置城市',
        'location_failed': '定位失败',
        'ip_fallback_marker': '（IP 定位）',
        # lunar.py 输出转换（默认中文 cnlunar 输出，zh 模式直接用）
        'lunar_year_pattern': '{ganzhi}年（{zodiac}）',
        'lunar_date_pattern': '{lunar_month}{lunar_day}',
        'lunar_day_gz_pattern': '{day_gz}日',
        'lunar_term_pattern': '（{term}）',
        # 日期格式（DATE_NOW）
        'date_format_tpl': '{y}年{m}月{d}日',
        # 月历标题（CALENDAR_MONTH）
        'calendar_month_tpl': '{y}年{m:02d}月',
    },
    'en': {
        'html_lang': 'en',
        'title': 'iKindle Calendar',
        'meta_description': 'iKindle — 6-inch KINDLE E-Ink calendar dashboard. Auto-location, lunar calendar, traditional festivals, Hitokoto.',
        'meta_keywords': 'kindle, dashboard, paperwhite, e-ink, calendar, e-ink, desktop, clock, calendar, weather',
        'og_title': 'iKindle Calendar',
        'og_description': '6-inch KINDLE E-Ink calendar dashboard',
        'weekdays': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'week_number': 'Week {n}',
        'offline_banner': 'Network disconnected, some features unavailable',
        'loading': 'Loading...',
        'today_no_festival': 'No festival today',
        'no_countdown': 'No upcoming countdown',
        'countdown_to': '{n} days until {festival}',
        'sunrise_sunset': 'Sunrise {sr} / Sunset {ss}',
        'sunrise_sunset_unavailable': 'Sunrise/Sunset unavailable',
        'location_unconfigured': 'City not configured',
        'location_failed': 'Location failed',
        'ip_fallback_marker': '(IP-based)',
        # lunar.py 输出转换（英文模式：转为 'Year of Zodiac' + 月日英文 + 节气英文）
        'lunar_year_pattern': '{zodiac_en} Year',
        'lunar_date_pattern': '{month_en} {day_en}',  # month_en 是英文月份（如 "May"），day_en 是 "7th"
        'lunar_day_gz_pattern': '{day_gz_en} Day',
        'lunar_term_pattern': '({term_en})',
        # 日期格式
        'date_format_tpl': '{month_en} {d}, {y}',
        # 月历标题
        'calendar_month_tpl': '{month_en} {y}',
    }
}


def get_strings(lang='zh'):
    """
    获取指定语言的字符串字典。

    :param lang: 'zh' 或 'en'（不区分大小写）
    :return: 字典（详见 STRINGS）
    """
    lang = (lang or 'zh').lower()
    if lang not in STRINGS:
        lang = 'zh'  # 未知语言降级到中文
    return STRINGS[lang]


def get_weekday_short(weekday_idx, lang='zh'):
    """获取周几的简短表示（weekday_idx: 0=周日, 6=周六）"""
    s = get_strings(lang)
    return s['weekdays'][weekday_idx]


def format_date(y, m, d, lang='zh'):
    """格式化日期：2026-06-21 → 中文 '2026年06月21日' 或英文 'June 21, 2026'"""
    s = get_strings(lang)
    if lang == 'en':
        month_en = EN_MONTHS_FULL[m - 1]
        return s['date_format_tpl'].format(y=y, m=m, d=d, month_en=month_en)
    else:
        return s['date_format_tpl'].format(y=y, m=m, d=d)


def format_calendar_month(y, m, lang='zh'):
    """格式化月历标题：2026年06月 / June 2026"""
    s = get_strings(lang)
    if lang == 'en':
        month_en = EN_MONTHS_FULL[m - 1]
        return s['calendar_month_tpl'].format(y=y, m=m, month_en=month_en)
    else:
        return s['calendar_month_tpl'].format(y=y, m=m)


def translate_lunar(cn_lunar_text, lang='zh'):
    """
    将 cnlunar 中文输出翻译为对应语言。
    输入示例：'丙午年（马）五月小初七丙寅日（夏至）'
    输出：
      zh: 原样
      en: 'Horse Year, May 7th (Summer Solstice)'
    """
    if lang == 'zh' or not cn_lunar_text:
        return cn_lunar_text

    if lang != 'en':
        return cn_lunar_text  # 其他语言暂无支持

    # 英文模式：解析中文再重组
    import re
    parts = []

    # 1. 干支年 + 生肖：'丙午年（马）'
    m_year = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])年(?:（([鼠牛虎兔龙蛇马羊猴鸡狗猪])）)?', cn_lunar_text)
    if m_year:
        ganzhi = m_year.group(1)
        zodiac = m_year.group(2) or ''
        # 英文模式优先用生肖（更地道），无生肖才用干支拼音
        zodiac_en = ZODIAC_EN.get(zodiac, zodiac) if zodiac else ''
        if zodiac_en:
            parts.append(zodiac_en + ' Year')
        else:
            g = HEAVENLY_STEMS_EN.get(ganzhi[0], ganzhi[0])
            b = EARTHLY_BRANCHES_EN.get(ganzhi[1], ganzhi[1])
            parts.append(g + b + ' Year')

    # 2. 农历月日：'五月小初七'
    m_date = re.search(r'((?:正|二|三|四|五|六|七|八|九|十|冬|腊)月(?:大|小)?(?:初|十|廿|卅)?(?:[一二三四五六七八九十]+))', cn_lunar_text)
    if m_date:
        cn_date = m_date.group(1)
        # 解析月份
        month_cn_map = {'正': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                        '七': 7, '八': 8, '九': 9, '十': 10, '冬': 11, '腊': 12}
        month_cn = cn_date[0]
        month_num = month_cn_map.get(month_cn, 0)
        month_en = EN_MONTHS_FULL[month_num - 1] if 1 <= month_num <= 12 else ''
        # 解析日期
        day_cn = cn_date.replace(month_cn + '月', '').replace('大', '').replace('小', '')
        day_map = {
            '初一': '1st', '初二': '2nd', '初三': '3rd', '初四': '4th', '初五': '5th',
            '初六': '6th', '初七': '7th', '初八': '8th', '初九': '9th', '初十': '10th',
            '十一': '11th', '十二': '12th', '十三': '13th', '十四': '14th', '十五': '15th',
            '十六': '16th', '十七': '17th', '十八': '18th', '十九': '19th', '二十': '20th',
            '廿一': '21st', '廿二': '22nd', '廿三': '23rd', '廿四': '24th', '廿五': '25th',
            '廿六': '26th', '廿七': '27th', '廿八': '28th', '廿九': '29th', '三十': '30th'
        }
        day_en = day_map.get(day_cn, day_cn)
        if month_en and day_en:
            parts.append(month_en + ' ' + day_en)

    # 3. 节气：'（夏至）' 或 '（芒种后 5 天）' - 但要排除'（马）'这种生肖括号
    # 技巧：只在文本末尾找括号（节气总是在最后）
    m_term = re.search(r'（([^）]+)）$', cn_lunar_text)
    if m_term:
        term_cn = m_term.group(1)
        # 节气通常 2-3 字，生肖 1 字
        if len(term_cn) >= 2:
            # 处理 '芒种后 5 天' 格式
            m_offset = re.match(r'^(.+?)后\s*(\d+)\s*天$', term_cn)
            if m_offset:
                base_term = SOLAR_TERMS_EN.get(m_offset.group(1), m_offset.group(1))
                days = m_offset.group(2)
                parts.append('(' + days + ' days after ' + base_term + ')')
            else:
                term_en = SOLAR_TERMS_EN.get(term_cn, term_cn)
                parts.append('(' + term_en + ')')

    return ', '.join(parts) if parts else cn_lunar_text


if __name__ == '__main__':
    import sys
    lang = sys.argv[1] if len(sys.argv) > 1 else 'zh'
    s = get_strings(lang)
    for k, v in s.items():
        print(f'{k}: {v}')