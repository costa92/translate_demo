#!/usr/bin/env python
"""
启动案例：统一知识库系统基本使用
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入知识库
try:
    # 尝试从 src 导入
    from src.knowledge_base import KnowledgeBase
    print("成功从 src.knowledge_base 导入模块")
except ImportError:
    try:
        # 尝试直接导入
        from knowledge_base import KnowledgeBase
        print("成功从 knowledge_base 导入模块")
    except ImportError:
        print("错误: 无法导入必要的模块。请确保项目已正确安装。")
        print("尝试运行: pip install -e .")
        sys.exit(1)

def main():
    """知识库系统基本使用示例"""
    try:
        # 初始化知识库
        kb = KnowledgeBase()
        
        # 添加文档
        print("添加文档到知识库...")
        doc_path = os.path.join(os.path.dirname(__file__), "../README.md")
        result = kb.add_document(doc_path)
        print(f"文档添加成功，ID: {result.document_id}")
        
        # 查询知识库
        print("\n查询知识库...")
        query = "这个系统有哪些主要功能？"
        result = kb.query(query)
        print(f"问题: {query}")
        print(f"回答: {result.answer}")
        print("\n来源:")
        for i, chunk in enumerate(result.chunks):
            print(f"  {i+1}. {chunk.text[:100]}...")
        
        # 显示存储提供商
        print("\n可用的存储提供商:")
        for provider in kb.get_storage_providers():
            print(f"  - {provider}")
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保项目已正确安装，并且所有依赖都已满足。")
        print("尝试运行: pip install -e .")
        sys.exit(1)

if __name__ == "__main__":
    main()