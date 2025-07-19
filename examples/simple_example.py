#!/usr/bin/env python
"""
统一知识库系统简单示例

这个示例展示了统一知识库系统的基本使用方法。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # 尝试从 src 导入
    from src.knowledge_base import KnowledgeBase
    from src.knowledge_base.core.config import Config
    print("成功从 src.knowledge_base 导入模块")
except ImportError:
    try:
        # 尝试直接导入
        from knowledge_base import KnowledgeBase
        from knowledge_base.core.config import Config
        print("成功从 knowledge_base 导入模块")
    except ImportError:
        print("错误: 无法导入必要的模块。请确保项目已正确安装。")
        print("尝试运行: pip install -e .")
        sys.exit(1)


def main():
    """运行简单示例"""
    try:
        # 创建配置
        config = Config()
        config.storage.provider = "memory"
        config.embedding.provider = "sentence_transformers"
        config.embedding.model = "all-MiniLM-L6-v2"
        config.generation.provider = "openai"
        config.generation.model = "gpt-3.5-turbo"
        
        # 初始化知识库
        print("初始化知识库...")
        kb = KnowledgeBase(config)
        
        # 添加一些示例文档
        print("添加示例文档...")
        documents = [
            {
                "title": "统一知识库系统简介",
                "content": """
                统一知识库系统是一个综合性的知识管理平台，它结合了文档存储、处理、检索和生成功能。
                系统采用分层架构，支持多种存储后端，包括内存存储、Notion、向量数据库和云存储。
                系统还提供灵活的文档处理功能，支持多种分块策略和元数据提取。
                """
            },
            {
                "title": "系统架构",
                "content": """
                统一知识库系统采用模块化设计，主要包括以下组件：
                1. 核心组件：提供基础接口和配置管理
                2. 存储组件：负责文档的存储和检索
                3. 处理组件：负责文档的处理和分块
                4. 检索组件：负责文档的搜索和排序
                5. 生成组件：负责基于检索结果生成回答
                6. 代理组件：提供多代理协作功能
                7. API组件：提供RESTful和WebSocket接口
                """
            },
            {
                "title": "使用场景",
                "content": """
                统一知识库系统适用于多种场景，包括：
                1. 企业知识管理：整合企业内部文档，提供智能检索和问答功能
                2. 个人知识管理：管理个人笔记和资料，提供智能助手功能
                3. 客户支持：基于产品文档提供自动化客户支持
                4. 研究辅助：整合研究论文和资料，辅助研究工作
                5. 教育培训：基于教材和课程资料提供个性化学习辅助
                """
            }
        ]
        
        for i, doc in enumerate(documents):
            result = kb.add_text(doc["content"], metadata={"title": doc["title"]})
            print(f"  文档 {i+1} 添加成功，ID: {result.document_id}")
        
        # 查询知识库
        print("\n查询知识库...")
        queries = [
            "统一知识库系统是什么？",
            "系统的主要组件有哪些？",
            "这个系统适用于哪些场景？"
        ]
        
        for i, query in enumerate(queries):
            print(f"\n问题 {i+1}: {query}")
            result = kb.query(query)
            print(f"回答: {result.answer}")
            print("来源:")
            for j, chunk in enumerate(result.chunks[:2]):  # 只显示前两个来源
                print(f"  {j+1}. {chunk.text[:100]}...")
        
        # 显示可用的存储提供商
        print("\n可用的存储提供商:")
        providers = kb.get_storage_providers()
        for provider in providers:
            print(f"  - {provider}")
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保项目已正确安装，并且所有依赖都已满足。")
        print("尝试运行: pip install -e .")
        sys.exit(1)


if __name__ == "__main__":
    main()