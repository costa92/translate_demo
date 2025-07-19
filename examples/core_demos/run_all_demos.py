#!/usr/bin/env python
"""
统一知识库系统示例启动脚本

这个脚本提供了一个菜单，用户可以选择运行不同的示例。
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印标题"""
    clear_screen()
    print("=" * 60)
    print("         统一知识库系统示例启动器         ")
    print("=" * 60)
    print()

def print_menu():
    """打印菜单"""
    print("请选择要运行的示例：")
    print()
    print("1. 独立示例 (不依赖外部模块)")
    print("2. 最小化API服务器")
    print("3. 完整演示 (API服务器 + 演示页面)")
    print("4. 打开API演示页面 (需要先启动API服务器)")
    print()
    print("0. 退出")
    print()

def run_standalone_example():
    """运行独立示例"""
    print_header()
    print("正在运行独立示例...")
    print()
    
    script_path = os.path.join(os.path.dirname(__file__), "standalone_example.py")
    subprocess.run([sys.executable, script_path])
    
    print()
    input("按回车键返回菜单...")

def run_minimal_api_server():
    """运行最小化API服务器"""
    print_header()
    print("正在启动最小化API服务器...")
    print("API文档将在 http://localhost:8000/docs 可用")
    print()
    print("按 Ctrl+C 停止服务器并返回菜单")
    print()
    
    script_path = os.path.join(os.path.dirname(__file__), "minimal_api_server.py")
    try:
        subprocess.run([sys.executable, script_path])
    except KeyboardInterrupt:
        print()
        print("服务器已停止")
    
    print()
    input("按回车键返回菜单...")

def run_full_demo():
    """运行完整演示"""
    print_header()
    print("正在启动完整演示...")
    print("API服务器将在 http://localhost:8000 启动")
    print("演示页面将在浏览器中打开")
    print()
    print("按 Ctrl+C 停止服务器并返回菜单")
    print()
    
    script_path = os.path.join(os.path.dirname(__file__), "run_demo.py")
    try:
        subprocess.run([sys.executable, script_path])
    except KeyboardInterrupt:
        print()
        print("服务器已停止")
    
    print()
    input("按回车键返回菜单...")

def open_api_demo():
    """打开API演示页面"""
    print_header()
    print("正在打开API演示页面...")
    print()
    
    demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "api_demo.html"))
    demo_url = f"file://{demo_path}"
    
    print(f"在浏览器中打开: {demo_url}")
    webbrowser.open(demo_url)
    
    print()
    print("注意: 请确保API服务器已经启动，否则演示页面将无法工作")
    print()
    input("按回车键返回菜单...")

def main():
    """主函数"""
    while True:
        print_header()
        print_menu()
        
        choice = input("请输入选项 (0-4): ")
        
        if choice == '0':
            print("谢谢使用，再见！")
            break
        elif choice == '1':
            run_standalone_example()
        elif choice == '2':
            run_minimal_api_server()
        elif choice == '3':
            run_full_demo()
        elif choice == '4':
            open_api_demo()
        else:
            print("无效的选项，请重新输入")
            input("按回车键继续...")

if __name__ == "__main__":
    main()