#!/usr/bin/env python
"""
统一知识库系统演示启动脚本

这个脚本启动最小化 API 服务器并打开演示页面。
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def open_browser():
    """在浏览器中打开演示页面"""
    # 等待服务器启动
    time.sleep(2)
    
    # 获取演示页面的绝对路径
    demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api_demo.html'))
    
    # 将文件路径转换为 URL
    demo_url = f"file://{demo_path}"
    
    print(f"在浏览器中打开演示页面: {demo_url}")
    webbrowser.open(demo_url)

def main():
    """主函数"""
    print("启动统一知识库系统演示...")
    
    # 在新线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 导入并启动 API 服务器
    try:
        from examples.minimal_api_server import run_app
        print("启动最小化 API 服务器...")
        print("API 文档将在 http://localhost:8000/docs 可用")
        run_app()
    except Exception as e:
        print(f"启动 API 服务器时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()