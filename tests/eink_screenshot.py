#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eink_screenshot.py —— 用 Chrome headless 截 E-Ink 灰度模拟图

工作流程：
  1. 启动本地 HTTP server（中间件模式：拦截 dashboard.html，注入 grayscale CSS）
  2. Chrome headless 截图（1072×1448 KWP4 viewport）
  3. 关闭 server

输出：
  /tmp/ikindle_grayscale/kpw4_eink_<timestamp>.png

灰度策略（模拟 16 级灰阶墨水屏）：
  - CSS filter: grayscale(1) contrast(1.05)
  - 关闭字体抗锯齿（-webkit-font-smoothing: none）

注：这只是模拟，真实 KWP4 渲染仍有差异（见 README）。
"""
import http.server
import socketserver
import threading
import subprocess
import os
import sys
import time
from datetime import datetime

PORT = 8769
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = "/tmp/ikindle_grayscale"

# KWP4 viewport 尺寸（两种方向）
VIEWPORTS = {
    'portrait': (1072, 1448),   # 竖屏（默认）
    'landscape': (1448, 1072),  # 横屏
}

GRAYSCALE_INJECT = """
<style id="eink-mock">
/* E-Ink 16 级灰阶模拟 */
html, body { filter: grayscale(1) contrast(1.08) brightness(0.98); }
* {
  -webkit-font-smoothing: none !important;
  -moz-osx-font-smoothing: unset !important;
  text-rendering: geometricPrecision !important;
}
/* 墨水屏常见浅灰文字在 16 阶下会糊成一团，强制加深 */
.muted, .secondary, .small-text { color: #333 !important; }
</style>
"""


class GrayscaleMiddlewareHandler(http.server.SimpleHTTPRequestHandler):
    """拦截 dashboard.html 注入 grayscale CSS，其他文件原样服务"""

    def do_GET(self):
        if self.path.endswith('/dashboard.html') or self.path == '/dashboard.html':
            try:
                with open(os.path.join(PROJECT_DIR, 'dashboard.html'), 'r', encoding='utf-8') as f:
                    html = f.read()
                # 在 </head> 前注入
                html = html.replace('</head>', GRAYSCALE_INJECT + '</head>')
                content = html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"[middleware] 注入失败: {e}", file=sys.stderr)
                # 失败则走默认处理
        super().do_GET()

    def log_message(self, format, *args):
        # 静默
        pass


def screenshot(orientation='portrait'):
    """
    主流程
    :param orientation: 'portrait' (1072x1448) 或 'landscape' (1448x1072)
    """
    if orientation not in VIEWPORTS:
        raise ValueError(f"orientation 必须是 {list(VIEWPORTS.keys())} 之一")

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.chdir(PROJECT_DIR)

    # 启动 server
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    httpd = ReusableTCPServer(("127.0.0.1", PORT), GrayscaleMiddlewareHandler)
    # 显式设置 SO_REUSEADDR，避免 TIME_WAIT 导致端口占用
    httpd.socket.setsockopt(
        __import__('socket').SOL_SOCKET,
        __import__('socket').SO_REUSEADDR, 1
    )
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    width, height = VIEWPORTS[orientation]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(
        SCREENSHOT_DIR, f"kpw4_eink_{orientation}_{timestamp}.png"
    )

    # Chrome 截图
    cmd = [
        'google-chrome', '--headless', '--disable-gpu', '--no-sandbox',
        f'--window-size={width},{height}', '--hide-scrollbars',
        f'--screenshot={output_path}',
        f'http://127.0.0.1:{PORT}/dashboard.html'
    ]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30
    )
    httpd.shutdown()

    if proc.returncode != 0:
        print(f"[chrome] 失败 (exit={proc.returncode}): {proc.stderr}", file=sys.stderr)
        httpd.server_close()
        return None

    if not os.path.exists(output_path):
        print(f"[chrome] 截图未生成: {output_path}", file=sys.stderr)
        httpd.server_close()
        return None

    size = os.path.getsize(output_path)
    print(f"[chrome] 截图成功 ({orientation}): {output_path} ({size} bytes)")
    httpd.server_close()
    return output_path


def screenshot_both():
    """截两种方向的截图（VIS-003 横屏验证）"""
    paths = {}
    for orient in ['portrait', 'landscape']:
        p = screenshot(orientation=orient)
        if p:
            paths[orient] = p
    return paths


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='E-Ink 灰度模拟截图')
    parser.add_argument(
        '--orientation', '-o',
        choices=['portrait', 'landscape', 'both'],
        default='portrait',
        help='截图方向 (默认 portrait)'
    )
    args = parser.parse_args()

    if args.orientation == 'both':
        paths = screenshot_both()
        sys.exit(0 if len(paths) == 2 else 1)
    else:
        path = screenshot(orientation=args.orientation)
        sys.exit(0 if path else 1)