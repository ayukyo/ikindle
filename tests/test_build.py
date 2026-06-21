#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build.py —— build.sh 端到端集成测试

运行：bash tests/test_build.sh
"""
import unittest
import subprocess
import os


class TestBuild(unittest.TestCase):
    """build.sh 端到端测试"""

    def test_build_script_runs(self):
        """build.sh 应能成功执行"""
        result = subprocess.run(
            ['bash', 'build.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        self.assertEqual(result.returncode, 0, f"build.sh 失败: {result.stderr}")

    def test_dashboard_html_created(self):
        """build.sh 应生成 dashboard.html"""
        self.assertTrue(
            os.path.exists('dashboard.html'),
            "dashboard.html 未生成"
        )

    def test_dashboard_html_size(self):
        """dashboard.html 应大于 1KB（说明非空）"""
        size = os.path.getsize('dashboard.html')
        self.assertGreater(size, 1024, f"dashboard.html 太小: {size} 字节")

    def test_no_remaining_placeholders(self):
        """dashboard.html 中不应有未替换的 {{}} 占位符"""
        with open('dashboard.html', 'r') as f:
            content = f.read()
        self.assertNotIn('{{', content, "仍有未替换占位符")

    def test_no_ampm_in_sunrise_sunset(self):
        """VIS-004：日出日落不应包含 AM/PM（应统一 24h 制）"""
        with open('dashboard.html', 'r') as f:
            content = f.read()
        # 找到日出日落那行
        import re
        m = re.search(r'日出\s*[^<]*日落\s*[^<]*', content)
        self.assertIsNotNone(m, "未找到日出日落文本")
        text = m.group(0)
        self.assertNotIn('AM', text, f"日出日落仍含 AM: {text}")
        self.assertNotIn('PM', text, f"日出日落仍含 PM: {text}")

    def test_no_emoji_decorations(self):
        """VIS-001：dashboard.html 中不应有装饰性 emoji（墨水屏灰阶下糊成灰块）"""
        with open('dashboard.html', 'r') as f:
            content = f.read()
        # 检测常见装饰 emoji (U+1F300 - U+1FFFF 范围内的图形符号)
        import re
        emojis_found = re.findall(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF]', content)
        self.assertEqual(
            emojis_found, [],
            f"dashboard.html 仍含装饰性 emoji: {emojis_found}"
        )

    def test_dashboard_has_required_elements(self):
        """dashboard.html 应包含必需元素"""
        with open('dashboard.html', 'r') as f:
            content = f.read()
        required = [
            '<div class="time">',
            '<div class="date">',
            '<div class="lunar">',
            '<div class="weather" id="weather">',
            'src="app.js"',
            # VIS-006：刷新频率从 5min (300s) 改为 30min (1800s) 省电
            'meta http-equiv="refresh" content="1800"',
            # VIS-002：节日为空时应有兜底文案
            '今日无节日',
            '近期无倒计时',
            # VIS-004：日出日落应为 24h 制（不带 AM/PM）
            '日出 ',
        ]
        for elem in required:
            self.assertIn(elem, content, f"缺失元素: {elem}")

    def test_lunar_2026_summer_solstice(self):
        """2026-06-21 应显示夏至节气"""
        result = subprocess.run(
            ['bash', '-c', 'LUNAR_DATE=2026-06-21 python3 lunar.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        self.assertIn('夏至', result.stdout, f"2026-06-21 应输出夏至，实际: {result.stdout}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
