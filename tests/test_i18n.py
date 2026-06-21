#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_i18n.py —— i18n.py 单元测试

运行：python3 -m unittest tests.test_i18n -v

覆盖：
- 字符串字典完整性（zh/en 都有必需字段）
- format_date / format_calendar_month 中英文输出
- translate_lunar 解析各种 cnlunar 输出格式
- 未知语言降级到中文
"""
import unittest
import os
import sys

# 让 tests/ 能 import i18n.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from i18n import (
    get_strings, format_date, format_calendar_month,
    translate_lunar, get_weekday_short
)


class TestI18nStrings(unittest.TestCase):
    """字符串字典完整性"""

    REQUIRED_KEYS = [
        'html_lang', 'title', 'meta_description', 'meta_keywords',
        'og_title', 'og_description', 'weekdays', 'week_number',
        'offline_banner', 'loading', 'today_no_festival',
        'no_countdown', 'countdown_to', 'sunrise_sunset',
        'sunrise_sunset_unavailable', 'location_unconfigured',
        'location_failed', 'ip_fallback_marker',
        'lunar_year_pattern', 'lunar_date_pattern',
        'lunar_day_gz_pattern', 'lunar_term_pattern',
        'date_format_tpl', 'calendar_month_tpl',
    ]

    def test_required_keys_present(self):
        """所有语言字典应包含必需字段"""
        for lang in ['zh', 'en']:
            s = get_strings(lang)
            for key in self.REQUIRED_KEYS:
                self.assertIn(key, s, f"[{lang}] 缺失字段: {key}")

    def test_weekdays_length_7(self):
        """weekdays 应为 7 元素列表"""
        for lang in ['zh', 'en']:
            s = get_strings(lang)
            self.assertEqual(len(s['weekdays']), 7,
                             f"[{lang}] weekdays 长度应为 7，实际 {len(s['weekdays'])}")

    def test_unknown_lang_fallback(self):
        """未知语言应降级到中文"""
        s = get_strings('klingon')
        self.assertEqual(s['title'], get_strings('zh')['title'])

    def test_chinese_title(self):
        """中文标题"""
        s = get_strings('zh')
        self.assertEqual(s['title'], 'iKindle 台历')

    def test_english_title(self):
        """英文标题"""
        s = get_strings('en')
        self.assertEqual(s['title'], 'iKindle Calendar')


class TestFormatDate(unittest.TestCase):
    """日期格式化"""

    def test_format_date_zh(self):
        """中文日期格式"""
        self.assertEqual(format_date(2026, 6, 21, 'zh'), '2026年6月21日')

    def test_format_date_en(self):
        """英文日期格式"""
        self.assertEqual(format_date(2026, 6, 21, 'en'), 'June 21, 2026')

    def test_format_calendar_month_zh(self):
        """中文月历标题"""
        self.assertEqual(format_calendar_month(2026, 6, 'zh'), '2026年06月')

    def test_format_calendar_month_en(self):
        """英文月历标题"""
        self.assertEqual(format_calendar_month(2026, 6, 'en'), 'June 2026')

    def test_format_date_january_en(self):
        """英文 January"""
        self.assertEqual(format_date(2026, 1, 1, 'en'), 'January 1, 2026')

    def test_format_date_december_en(self):
        """英文 December"""
        self.assertEqual(format_date(2026, 12, 31, 'en'), 'December 31, 2026')


class TestTranslateLunar(unittest.TestCase):
    """农历翻译"""

    def test_translate_passthrough_zh(self):
        """中文模式应原样返回"""
        text = '丙午年（马）五月小初七丙寅日（夏至）'
        self.assertEqual(translate_lunar(text, 'zh'), text)

    def test_translate_zodiac_year_en(self):
        """英文模式：干支年 + 生肖"""
        text = '丙午年（马）五月小初七丙寅日（夏至）'
        result = translate_lunar(text, 'en')
        self.assertIn('Horse Year', result)
        self.assertNotIn('（马）', result, "不应有未翻译的生肖括号")

    def test_translate_lunar_date_en(self):
        """英文模式：月日"""
        result = translate_lunar('丙午年（马）五月小初七丙寅日（夏至）', 'en')
        self.assertIn('May', result)
        self.assertIn('7th', result)

    def test_translate_solar_term_en(self):
        """英文模式：节气"""
        result = translate_lunar('丙午年（马）五月小初七丙寅日（夏至）', 'en')
        self.assertIn('Summer Solstice', result)

    def test_translate_solar_term_with_offset_en(self):
        """英文模式：节气 + N 天（如 '芒种后 5 天'）"""
        result = translate_lunar('丙午年（马）五月初六 庚寅日（芒种后 5 天）', 'en')
        self.assertIn('Grain in Ear', result)
        self.assertIn('5 days after', result)

    def test_translate_lunar_no_zodiac_en(self):
        """英文模式：无生肖时退回干支"""
        result = translate_lunar('丙午年五月十五', 'en')
        # 无生肖括号，应回退到 BingWu Year
        self.assertIn('Year', result)

    def test_translate_empty(self):
        """空字符串应原样返回"""
        self.assertEqual(translate_lunar('', 'en'), '')


class TestGetWeekdayShort(unittest.TestCase):
    """周几简写"""

    def test_zh_weekdays(self):
        """中文：日 一 二 三 四 五 六"""
        self.assertEqual(get_weekday_short(0, 'zh'), '日')
        self.assertEqual(get_weekday_short(1, 'zh'), '一')
        self.assertEqual(get_weekday_short(6, 'zh'), '六')

    def test_en_weekdays(self):
        """英文：Sun Mon Tue Wed Thu Fri Sat"""
        self.assertEqual(get_weekday_short(0, 'en'), 'Sun')
        self.assertEqual(get_weekday_short(1, 'en'), 'Mon')
        self.assertEqual(get_weekday_short(6, 'en'), 'Sat')


if __name__ == '__main__':
    unittest.main(verbosity=2)