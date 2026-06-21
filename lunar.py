#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lunar.py —— 农历 / 干支 / 节气计算
====================================

依赖：
    pip install cnlunar

输入（环境变量）：
    LUNAR_DATE  YYYY-MM-DD（默认今天）

输出（stdout）：
    一行中文文本，形如：
        丙午年五月初六 庚寅日（芒种后 5 天）
"""
import os
import sys
from datetime import datetime

try:
    import cnlunar
except ImportError:
    # 降级：返回空字符串
    sys.stdout.write('')
    sys.exit(0)


def get_lunar_info(date_str: str) -> str:
    """获取农历信息字符串。"""
    try:
        # cnlunar 0.2.4 需要 datetime 对象，不再接受字符串
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        lunar = cnlunar.Lunar(dt)
    except Exception:
        return ''

    parts = []
    # 干支年 + 生肖（cnlunar 0.2.4 API：year8Char + chineseYearZodiac）
    year_gz = getattr(lunar, 'year8Char', '')
    year_zodiac = getattr(lunar, 'chineseYearZodiac', '')
    if year_gz and year_zodiac:
        parts.append(year_gz + '年（' + year_zodiac + '）')
    elif year_gz:
        parts.append(year_gz + '年')
    elif year_zodiac:
        parts.append(year_zodiac + '年')
    # 农历月日（cnlunar 0.2.4 API：lunarMonthCn + lunarDayCn）
    month_cn = getattr(lunar, 'lunarMonthCn', '')
    day_cn = getattr(lunar, 'lunarDayCn', '')
    if month_cn and day_cn:
        parts.append(month_cn + day_cn)
    # 干支日（cnlunar 0.2.4 API：day8Char）
    day_gz = getattr(lunar, 'day8Char', '')
    if day_gz:
        parts.append(day_gz + '日')
    # 节气（cnlunar 0.2.4 API：todaySolarTerms）
    if hasattr(lunar, 'todaySolarTerms') and lunar.todaySolarTerms:
        parts.append('（' + lunar.todaySolarTerms + '）')

    return ''.join(parts)


if __name__ == '__main__':
    date_str = os.environ.get('LUNAR_DATE', datetime.now().strftime('%Y-%m-%d'))
    sys.stdout.write(get_lunar_info(date_str))
