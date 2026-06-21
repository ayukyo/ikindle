#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
festivals_parse.py —— 解析 festivals.json，提取今日节日 + 近期倒计时

输入：
    argv[1]：festivals.json 路径
    env TODAY_MM_DD：今日 MM-DD
    env I18N_JSON：i18n 字典 JSON（用于选择 label_zh / label_en）
    env COUNTDOWN_TPL_EN：英文倒计时模板
    env COUNTDOWN_TPL_ZH：中文倒计时模板

输出（stdout）：
    "{label1}|{label2}||{countdown}" 格式
    - 标签用 | 分隔（多节日）
    - 倒计时单独一栏（最多 30 天内）
"""
import json
import os
import sys
from datetime import datetime


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    festivals_path = sys.argv[1]
    today_mm_dd = os.environ.get('TODAY_MM_DD', '')
    i18n_json = os.environ.get('I18N_JSON', '{}')

    try:
        i18n = json.loads(i18n_json)
    except Exception:
        i18n = {}

    lang = i18n.get('html_lang', 'zh-CN')[:2]  # 'zh' or 'en'
    label_key = 'label_en' if lang == 'en' else 'label_zh'
    countdown_tpl_en = os.environ.get('COUNTDOWN_TPL_EN',
                                      '{n} days until {festival}')
    countdown_tpl_zh = os.environ.get('COUNTDOWN_TPL_ZH',
                                      '距离{festival}还有 {n} 天')

    try:
        with open(festivals_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        sys.stderr.write('festivals_parse: 读取失败: {}\n'.format(e))
        sys.exit(0)

    labels = []
    countdown = ''

    for item in data:
        if item.get('date') == today_mm_dd:
            # 今日节日：按语言选 label
            name = item.get(label_key) or item.get('label_en') or item.get('label_zh', '')
            labels.append(name)
        elif (item.get('countdown')
              and item.get('date')
              and not item['date'].startswith('L')
              and not item['date'].startswith('MEM')):
            # 倒计时候选：公历日期 + 启用倒计时
            try:
                now = datetime.now()
                target = datetime.strptime(
                    str(now.year) + '-' + item['date'], '%Y-%m-%d'
                )
                if target < now:
                    target = target.replace(year=now.year + 1)
                diff = (target - now).days
                if 0 < diff <= 30:
                    name = (item.get(label_key)
                            or item.get('label_en')
                            or item.get('label_zh', ''))
                    if lang == 'en':
                        countdown = countdown_tpl_en.format(
                            n=str(diff), festival=name
                        )
                    else:
                        countdown = countdown_tpl_zh.format(
                            festival=name, n=str(diff)
                        )
                    break  # 只取最近一个
            except Exception:
                pass

    sys.stdout.write('|'.join(labels) + '||' + countdown)


if __name__ == '__main__':
    main()