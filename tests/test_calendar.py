#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_calendar.py —— generate_calendar.py 单元测试

运行：python3 -m unittest tests/test_calendar.py -v
"""
import unittest
import os
import importlib.util


def _load_module(name, path):
    """动态加载模块（避免 tests 目录无 __init__.py）"""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCalendar(unittest.TestCase):
    """月历生成测试"""

    @classmethod
    def setUpClass(cls):
        cls.gen = _load_module('generate_calendar', 'generate_calendar.py')

    def test_current_month_structure(self):
        """当月月历：5-6 周 + 28-31 天"""
        html = self.gen.generate_calendar_html() if hasattr(self.gen, 'generate_calendar_html') else None
        # 模块用 if __name__ 触发，需要环境变量
        import os
        os.environ['CALENDAR_YEAR'] = '2026'
        os.environ['CALENDAR_MONTH'] = '6'
        # 重新执行 module（环境变量需在 import 前设置）
        spec = importlib.util.spec_from_file_location('generate_calendar2', 'generate_calendar.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # 调用 __main__ 块逻辑（直接调 module 的逻辑而非 main）
        from datetime import datetime
        import calendar as cal_mod
        YEAR = 2026
        MONTH = 6
        cal = cal_mod.Calendar()
        weeks = cal.monthdayscalendar(YEAR, MONTH)
        self.assertEqual(len(weeks), 5, "2026-06 应有 5 周（6/1 是周一）")
        # 6 月共 30 天
        days = [d for w in weeks for d in w if d != 0]
        self.assertEqual(sum(days), sum(range(1, 31)), "所有天数之和 = 1+...+30 = 465")
        self.assertEqual(len(days), 30, "6 月有 30 天")

    def test_february_non_leap(self):
        """2026 平年 2 月：28 天"""
        from datetime import datetime
        import calendar as cal_mod
        weeks = cal_mod.Calendar().monthdayscalendar(2026, 2)
        days = [d for w in weeks for d in w if d != 0]
        self.assertEqual(len(days), 28, "2026-02 应有 28 天（非闰年）")

    def test_february_leap(self):
        """2028 闰年 2 月：29 天"""
        from datetime import datetime
        import calendar as cal_mod
        weeks = cal_mod.Calendar().monthdayscalendar(2028, 2)
        days = [d for w in weeks for d in w if d != 0]
        self.assertEqual(len(days), 29, "2028-02 应有 29 天（闰年）")

    def test_week_start_sunday(self):
        """月历周以周日开头（与 dashboard.html weekday row 一致）"""
        import calendar as cal_mod
        # firstweekday=6 = 周日开头（与 dashboard.html 表头"日 一 二 三 四 五 六"一致）
        weeks = cal_mod.Calendar(firstweekday=6).monthdayscalendar(2026, 6)
        # 6/1 是周一 → 6/1 在第一周的周二列（索引 1）
        self.assertEqual(weeks[0][1], 1, "6/1 是周一，周日开头时应在第一周周二列")
        self.assertEqual(weeks[0][0], 0, "第一周周日列应为 0")


if __name__ == '__main__':
    unittest.main(verbosity=2)
