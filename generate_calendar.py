#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_calendar.py —— 生成当月月历 HTML
============================================

输入（环境变量）：
    CALENDAR_YEAR  YYYY（默认当前年）
    CALENDAR_MONTH MM（默认当前月）

输出（stdout）：
    月历 HTML 片段，由 <div class="calendar-day"> / <div class="calendar-blank"> 组成。
    今日单元格带 class="today"。
"""
import calendar
import os
from datetime import datetime

YEAR = int(os.environ.get('CALENDAR_YEAR', datetime.now().year))
MONTH = int(os.environ.get('CALENDAR_MONTH', datetime.now().month))

cal = calendar.Calendar(firstweekday=6)  # firstweekday=6 = 周日开头（与 dashboard.html 表头一致）
weeks = cal.monthdayscalendar(YEAR, MONTH)
today_day = datetime.now().day if (YEAR == datetime.now().year and MONTH == datetime.now().month) else None

lines = []
for week in weeks:
    lines.append('<div class="calendar-week">')
    for day in week:
        if day == 0:
            lines.append('<div class="calendar-blank"></div>')
        else:
            classes = 'calendar-day'
            if day == today_day:
                classes += ' today'
            lines.append('<div class="' + classes + '">' + str(day) + '</div>')
    lines.append('</div>')

print('\n'.join(lines))
