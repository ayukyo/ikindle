#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_festivals.py —— festivals.json + 农历匹配单元测试

运行：python3 -m unittest tests/test_festivals.py -v
"""
import unittest
import json
import os
from datetime import datetime


class TestFestivals(unittest.TestCase):
    """节日配置 + 农历匹配测试"""

    @classmethod
    def setUpClass(cls):
        with open('festivals.json', 'r', encoding='utf-8') as f:
            cls.data = json.load(f)

    def test_festivals_loaded(self):
        """festivals.json 应加载至少 20 个节日"""
        self.assertGreaterEqual(len(self.data), 20, "至少 20 个节日条目")

    def test_festivals_structure(self):
        """每个节日应有 date / label_zh / label_en / type / countdown 字段（i18n 双语）"""
        required_fields = {'date', 'label_zh', 'label_en', 'type', 'countdown'}
        for item in self.data:
            self.assertTrue(
                required_fields.issubset(item.keys()),
                f"节日 {item} 缺失字段"
            )

    def test_festivals_bilingual_labels(self):
        """label_zh 和 label_en 应均为非空字符串"""
        for item in self.data:
            self.assertIsInstance(item.get('label_zh'), str)
            self.assertIsInstance(item.get('label_en'), str)
            self.assertGreater(len(item['label_zh']), 0)
            self.assertGreater(len(item['label_en']), 0)

    def test_festivals_type_values(self):
        """type 应为 public / traditional / memorial"""
        valid_types = {'public', 'traditional', 'memorial'}
        for item in self.data:
            self.assertIn(item['type'], valid_types, f"非法 type: {item}")

    def test_public_festivals_date_format(self):
        """公历节日 date 格式 MM-DD"""
        for item in self.data:
            if item['type'] == 'public':
                parts = item['date'].split('-')
                self.assertEqual(len(parts), 2, f"公历日期格式错误: {item['date']}")
                mm, dd = int(parts[0]), int(parts[1])
                self.assertTrue(1 <= mm <= 12, f"月份越界: {item['date']}")
                self.assertTrue(1 <= dd <= 31, f"日期越界: {item['date']}")

    def test_traditional_festivals_lunar_prefix(self):
        """传统节日 date 应以 L 前缀标识农历"""
        for item in self.data:
            if item['type'] == 'traditional':
                self.assertTrue(
                    item['date'].startswith('L'),
                    f"传统节日应有 L 前缀: {item['date']}"
                )

    def test_countdown_is_boolean(self):
        """countdown 字段应为布尔"""
        for item in self.data:
            self.assertIsInstance(
                item['countdown'], bool,
                f"countdown 应为 bool: {item}"
            )

    def test_today_match(self):
        """模拟今日匹配逻辑"""
        from datetime import datetime
        today = datetime.now().strftime('%m-%d')
        matched = [item for item in self.data if item['date'] == today]
        # 不强制有匹配，只验证逻辑
        for m in matched:
            self.assertIn(m['type'], {'public', 'traditional', 'memorial'})


class TestLunarMatching(unittest.TestCase):
    """农历日期匹配测试（依赖 cnlunar）"""

    def test_cnlunar_import(self):
        """cnlunar 应可导入"""
        try:
            import cnlunar
            self.assertTrue(True)
        except ImportError:
            self.skipTest("cnlunar 未安装")

    def test_lunar_today_match_summer_solstice(self):
        """2026-06-21 是夏至节气（公历 6/21 附近）"""
        try:
            import cnlunar
        except ImportError:
            self.skipTest("cnlunar 未安装")
        from datetime import datetime
        dt = datetime(2026, 6, 21)
        lunar = cnlunar.Lunar(dt)
        # cnlunar 0.2.4 API: todaySolarTerms
        self.assertIn('夏至', str(getattr(lunar, 'todaySolarTerms', '')))

    def test_lunar_year_shengxiao(self):
        """2026 是丙午年（马年）"""
        try:
            import cnlunar
        except ImportError:
            self.skipTest("cnlunar 未安装")
        from datetime import datetime
        dt = datetime(2026, 6, 21)
        lunar = cnlunar.Lunar(dt)
        # cnlunar 0.2.4 API: chineseYearZodiac + year8Char
        zodiac = getattr(lunar, 'chineseYearZodiac', '')
        ganzhi = getattr(lunar, 'year8Char', '')
        self.assertEqual(zodiac, '马', f"2026 生肖: {zodiac}")
        self.assertEqual(ganzhi, '丙午', f"2026 干支: {ganzhi}")

    def test_lunar_month_day(self):
        """2026-06-21 农历：丙午年五月初七（节气前一日）"""
        try:
            import cnlunar
        except ImportError:
            self.skipTest("cnlunar 未安装")
        from datetime import datetime
        dt = datetime(2026, 6, 21)
        lunar = cnlunar.Lunar(dt)
        # 2026-06-21 是农历五月初七
        self.assertIn('五月', getattr(lunar, 'lunarMonthCn', ''))
        self.assertIn('初七', getattr(lunar, 'lunarDayCn', ''))


if __name__ == '__main__':
    unittest.main(verbosity=2)
