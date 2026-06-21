#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wttr_parse.py —— 解析 wttr.in j1 JSON 输出，生成 sunrise-sunset 和 location

输入（stdin）：
    wttr.in j1 JSON（来自 build.sh 的 curl）

输出（stdout）：
    "{sun_str}^^^{loc_str}" 格式（^^^ 是分隔符，build.sh 用 sed 切）

依赖：
    无（只用 stdlib）
"""
import json
import sys
import re


def to_24h(s):
    """'05:45 AM' / '08:37 PM' → '05:45' / '20:37'（24h 制）"""
    m = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', s.strip(), re.IGNORECASE)
    if not m:
        return s
    h, mi, ap = int(m.group(1)), m.group(2), m.group(3).upper()
    if ap == 'PM' and h != 12:
        h += 12
    elif ap == 'AM' and h == 12:
        h = 0
    return '%02d:%s' % (h, mi)


def main():
    sunrise_sunset_tpl = sys.argv[1] if len(sys.argv) > 1 else '日出 {sr} / 日落 {ss}'

    try:
        d = json.loads(sys.stdin.read())
    except Exception as e:
        sys.stderr.write('wttr_parse: JSON 解析失败: {}\n'.format(e))
        sys.exit(0)  # 退出 0 让 build.sh 走兜底分支

    try:
        today = d['weather'][0]
        sunrise = to_24h(today['astronomy'][0]['sunrise'])
        sunset = to_24h(today['astronomy'][0]['sunset'])
        area = d.get('nearest_area', [{}])[0]
        city_name = area.get('areaName', [{}])[0].get('value', '')
        country = area.get('country', [{}])[0].get('value', '')
        sun_str = sunrise_sunset_tpl.format(sr=sunrise, ss=sunset)
        loc_str = ''
        if city_name:
            loc_str = city_name
            if country and country != city_name:
                loc_str += ' / ' + country
        # ^^^ 分隔符（sun_str 和 loc_str 都不会包含 ^^^）
        sys.stdout.write(sun_str + '^^^' + loc_str)
    except Exception as e:
        sys.stderr.write('wttr_parse: 数据提取失败: {}\n'.format(e))
        sys.exit(0)


if __name__ == '__main__':
    main()