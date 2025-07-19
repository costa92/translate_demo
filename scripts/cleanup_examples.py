#!/usr/bin/env python
"""
清理无用的示例代码

这个脚本将删除不再需要的示例代码，只保留核心示例。
"""

import os
import sys
import shutil
from pathlib import Path

# 要保留的核心示例
CORE_EXAMPLES = [
    'core_demos',
    '__pycache__'  # 不删除缓存目录
]

def cleanup_examples():
    """清理无用的示例代码"""
    examples_dir = Path('examples')
    
    # 确保目录存在
    if not examples_dir.exists() or not examples_dir.is_dir():
        print(f"错误: {examples_dir} 目录不存在")
        return False
    
    # 获取所有示例文件和目录
    items = list(examples_dir.iterdir())
    
    # 要删除的项目
    to_delete = []
    
    for item in items:
        if item.name not in CORE_EXAMPLES:
            to_delete.append(item)
    
    # 打印要删除的项目
    print("以下项目将被删除:")
    for item in to_delete:
        print(f"  - {item}")
    
    # 确认删除
    confirm = input("确认删除这些项目? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return False
    
    # 删除项目
    for item in to_delete:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"已删除: {item}")
        except Exception as e:
            print(f"删除 {item} 时出错: {e}")
    
    print("清理完成")
    return True

def main():
    """主函数"""
    print("清理无用的示例代码...")
    if cleanup_examples():
        print("示例代码已清理")
    else:
        print("清理操作未完成")

if __name__ == "__main__":
    main()