#!/usr/bin/env python3

"""
测试导入是否正常工作
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 打印Python路径
print("Python路径:")
for path in sys.path:
    print(f"  - {path}")

# 检查文件是否存在
llm_path = os.path.join(project_root, 'src', 'llm', 'base.py')
print(f"\n检查文件是否存在: {llm_path}")
print(f"文件存在: {os.path.exists(llm_path)}")

# 尝试直接导入
try:
    import src.llm.base
    print("\n直接导入src.llm.base成功！")
    print(f"LLMFactory: {src.llm.base.LLMFactory}")
    print(f"LLM: {src.llm.base.LLM}")
except Exception as e:
    print(f"\n直接导入src.llm.base失败: {e}")

# 尝试通过translate_demo导入
try:
    from src.translate_demo.llm import LLMFactory, LLM
    print("\n通过translate_demo导入成功！")
    print(f"LLMFactory: {LLMFactory}")
    print(f"LLM: {LLM}")
except Exception as e:
    print(f"\n通过translate_demo导入失败: {e}")