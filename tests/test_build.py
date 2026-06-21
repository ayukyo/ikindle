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
            'meta http-equiv="refresh" content="300"',
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
