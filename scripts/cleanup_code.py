#!/usr/bin/env python
"""
清理多余代码脚本
"""
import os
import re
import shutil
from pathlib import Path

def is_test_file(file_path):
    """判断是否为测试文件"""
    return (
        file_path.name.startswith('test_') or 
        file_path.name.endswith('_test.py') or
        'tests' in file_path.parts
    )

def is_example_file(file_path):
    """判断是否为示例文件"""
    return 'examples' in file_path.parts

def is_temp_file(file_path):
    """判断是否为临时文件"""
    temp_patterns = [
        r'\.tmp$', r'\.bak$', r'\.swp$', r'~$',
        r'\.pyc$', r'__pycache__'
    ]
    return any(re.search(pattern, str(file_path)) for pattern in temp_patterns)

def is_duplicate_implementation(file_path):
    """判断是否为重复实现"""
    # 检查是否为旧的知识库实现
    if 'src/agents/knowledge_base' in str(file_path):
        return True
    return False

def cleanup_code():
    """清理多余代码"""
    # 要保留的核心目录
    core_dirs = [
        'src/knowledge_base',
        'tests/unit',
        'tests/integration',
        'examples',
        'docs',
    ]
    
    # 要删除的文件和目录
    to_delete = []
    
    # 遍历项目目录
    for root, dirs, files in os.walk('.'):
        root_path = Path(root)
        
        # 跳过.git和其他版本控制目录
        if '.git' in root_path.parts or '.tox' in root_path.parts:
            continue
            
        # 检查是否为重复实现
        if is_duplicate_implementation(root_path):
            to_delete.append(root_path)
            continue
        
        # 检查文件
        for file in files:
            file_path = root_path / file
            
            # 跳过核心目录中的文件
            if any(str(file_path).startswith(core_dir) for core_dir in core_dirs):
                continue
                
            # 检查是否为临时文件
            if is_temp_file(file_path):
                to_delete.append(file_path)
                continue
                
            # 检查是否为Python文件
            if file.endswith('.py'):
                # 检查是否为测试文件但不在tests目录中
                if is_test_file(file_path) and not any('tests' in core_dir and str(file_path).startswith(core_dir) for core_dir in core_dirs):
                    to_delete.append(file_path)
    
    # 打印要删除的文件和目录
    print("以下文件和目录将被删除:")
    for path in to_delete:
        print(f"  - {path}")
    
    # 确认删除
    confirm = input("确认删除这些文件和目录? (y/n): ")
    if confirm.lower() == 'y':
        for path in to_delete:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"已删除: {path}")
            except Exception as e:
                print(f"删除 {path} 时出错: {e}")
    else:
        print("操作已取消")

if __name__ == "__main__":
    cleanup_code()