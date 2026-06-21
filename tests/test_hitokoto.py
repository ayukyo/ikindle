#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_hitokoto.py —— refresh_hitokoto.sh 端到端集成测试

运行：python3 -m unittest tests.test_hitokoto -v

策略：
  1. 备份当前 hitokoto_cache.json
  2. 端到端运行 refresh_hitokoto.sh
  3. 验证产出 JSON 结构（必需字段、非空 hitokoto）
  4. 还原原文件
"""
import unittest
import subprocess
import os
import json
import shutil
import tempfile


class TestHitokotoRefresh(unittest.TestCase):
    """refresh_hitokoto.sh 端到端测试"""

    CACHE_FILE = 'hitokoto_cache.json'
    REQUIRED_FIELDS = {'hitokoto', 'from', 'creator', 'created_at'}

    def setUp(self):
        """备份原缓存文件"""
        if os.path.exists(self.CACHE_FILE):
            self._backup_fd, self._backup_path = tempfile.mkstemp(
                prefix='hitokoto_cache.bak.', suffix='.json'
            )
            shutil.copy2(self.CACHE_FILE, self._backup_path)
            self._had_backup = True
        else:
            self._backup_path = None
            self._had_backup = False

    def tearDown(self):
        """还原原缓存文件"""
        if self._had_backup and self._backup_path:
            shutil.copy2(self._backup_path, self.CACHE_FILE)
            os.unlink(self._backup_path)
        elif os.path.exists(self.CACHE_FILE):
            # 脚本运行前没有缓存，测试后清理
            os.unlink(self.CACHE_FILE)

    def test_refresh_script_runs(self):
        """refresh_hitokoto.sh 应能成功执行"""
        result = subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        self.assertEqual(
            result.returncode, 0,
            f"refresh_hitokoto.sh 失败 (exit={result.returncode}): {result.stderr}"
        )

    def test_cache_file_created(self):
        """应生成 hitokoto_cache.json"""
        # 显式先删，确保脚本真的写出来了
        if os.path.exists(self.CACHE_FILE):
            os.unlink(self.CACHE_FILE)
        subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        self.assertTrue(
            os.path.exists(self.CACHE_FILE),
            "hitokoto_cache.json 未生成"
        )

    def test_cache_json_valid(self):
        """hitokoto_cache.json 应是合法 JSON"""
        subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data, dict, "缓存应为 JSON object")

    def test_cache_has_required_fields(self):
        """缓存必须包含 hitokoto / from / creator / created_at 字段"""
        subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertTrue(
            self.REQUIRED_FIELDS.issubset(data.keys()),
            f"缺失字段: {self.REQUIRED_FIELDS - set(data.keys())}"
        )

    def test_hitokoto_text_non_empty(self):
        """hitokoto 字段应为非空字符串"""
        subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIsInstance(data.get('hitokoto'), str)
        self.assertGreater(
            len(data['hitokoto'].strip()), 0,
            "hitokoto 不能为空字符串"
        )

    def test_created_at_format(self):
        """created_at 应符合 YYYY-MM-DD HH:MM:SS 格式"""
        subprocess.run(
            ['bash', 'refresh_hitokoto.sh'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        from datetime import datetime
        try:
            datetime.strptime(data['created_at'], '%Y-%m-%d %H:%M:%S')
        except (KeyError, ValueError) as e:
            self.fail(f"created_at 格式错误: {data.get('created_at')} ({e})")


if __name__ == '__main__':
    unittest.main(verbosity=2)