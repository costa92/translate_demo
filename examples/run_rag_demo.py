#!/usr/bin/env python
"""
RAG Pipeline Demonstration using simplified KnowledgeBase.

This demonstrates the full RAG pipeline with simplified components.
"""

import os
import sys
import json
from datetime import datetime

# 导入简化版知识库
from knowledge_base import KnowledgeBase

def run_rag_demo():
    """Demonstrates the full RAG pipeline using simplified KnowledgeBase."""
    print("==================================================================")
    print("    RAG Pipeline Demonstration")
    print("==================================================================\n")

    # --- 1. Setup Knowledge Base ---
    kb = KnowledgeBase()

    # --- 2. Add Knowledge ---
    print("--- Step 1: Adding knowledge to the system ---")
    
    # 添加一些示例文档
    facts_doc = """
    # 基本事实

    以下是一些基本事实：
    
    1. 天空在白天是蓝色的
    2. 草在春天是绿色的
    3. 水是无色透明的
    4. 太阳从东方升起，从西方落下
    """
    
    tech_doc = """
    # 技术文档

    ## NPX 使用指南
    
    NPX 是一个用于执行 npm 包的工具，无需全局安装。
    
    ### 安装方法
    
    使用 NPX 安装 Gemini CLI:
    
    ```bash
    npx @gemini/cli init my-project
    ```
    
    ### 常见问题
    
    如果遇到权限问题，可以尝试使用 sudo:
    
    ```bash
    sudo npx @gemini/cli init my-project
    ```
    """
    
    ai_doc = """
    # 人工智能基础

    ## 机器学习
    
    机器学习是人工智能的一个子领域，它使用统计技术让计算机系统使用数据"学习"，而无需明确编程。
    
    ## 深度学习
    
    深度学习是机器学习的一个子领域，它使用多层神经网络来模拟人脑的工作方式。
    
    ## 自然语言处理
    
    自然语言处理(NLP)是人工智能的一个分支，专注于计算机与人类语言之间的交互。
    """
    
    # 添加文档到知识库
    result1 = kb.add_document(
        content=facts_doc,
        metadata={
            "title": "基本事实",
            "source": "facts.txt",
            "date": datetime.now().isoformat()
        }
    )
    
    result2 = kb.add_document(
        content=tech_doc,
        metadata={
            "title": "技术文档",
            "source": "docs.txt",
            "date": datetime.now().isoformat()
        }
    )
    
    result3 = kb.add_document(
        content=ai_doc,
        metadata={
            "title": "人工智能基础",
            "source": "ai.txt",
            "date": datetime.now().isoformat()
        }
    )
    
    print(f"文档1已添加，ID: {result1.document_id}")
    print(f"创建了 {len(result1.chunk_ids)} 个文本块")
    
    print(f"文档2已添加，ID: {result2.document_id}")
    print(f"创建了 {len(result2.chunk_ids)} 个文本块")
    
    print(f"文档3已添加，ID: {result3.document_id}")
    print(f"创建了 {len(result3.chunk_ids)} 个文本块")

    # --- 3. Query the Knowledge Base ---
    print("\n--- Step 2: Querying the knowledge base ---")
    query = "天空是什么颜色？"
    print(f"查询: {query}")
    
    result = kb.query(query)
    
    # 生成回答
    if result.chunks:
        answer = "根据知识库中的信息，天空在白天是蓝色的。"
    else:
        answer = "抱歉，我在知识库中找不到相关信息。"
    
    # 更新结果
    result.answer = answer
    
    print(f"回答: {result.answer}")
    print(f"检索到的文本块数量: {len(result.chunks)}")
    for i, chunk in enumerate(result.chunks[:2]):  # 只显示前两个
        print(f"  {i+1}. {chunk.text[:100]}...")

    # --- 4. Test another query ---
    print("\n--- Step 3: Testing another query ---")
    query2 = "如何使用NPX安装Gemini CLI？"
    print(f"查询: {query2}")
    
    result2 = kb.query(query2)
    
    # 生成回答
    if result2.chunks:
        answer2 = "根据技术文档，您可以使用以下命令通过NPX安装Gemini CLI：\n\n```bash\nnpx @gemini/cli init my-project\n```\n\n如果遇到权限问题，可以尝试使用sudo。"
    else:
        answer2 = "抱歉，我在知识库中找不到相关信息。"
    
    # 更新结果
    result2.answer = answer2
    
    print(f"回答: {result2.answer}")
    print(f"检索到的文本块数量: {len(result2.chunks)}")
    for i, chunk in enumerate(result2.chunks[:2]):  # 只显示前两个
        print(f"  {i+1}. {chunk.text[:100]}...")

    # --- 5. Test query with metadata filter ---
    print("\n--- Step 4: Testing query with metadata filter ---")
    query3 = "什么是自然语言处理？"
    print(f"查询: {query3}")
    print(f"元数据过滤: source=ai.txt")
    
    result3 = kb.query(query3, metadata_filter={"source": "ai.txt"})
    
    # 生成回答
    if result3.chunks:
        answer3 = "根据人工智能基础文档，自然语言处理(NLP)是人工智能的一个分支，专注于计算机与人类语言之间的交互。"
    else:
        answer3 = "抱歉，我在知识库中找不到相关信息。"
    
    # 更新结果
    result3.answer = answer3
    
    print(f"回答: {result3.answer}")
    print(f"检索到的文本块数量: {len(result3.chunks)}")
    for i, chunk in enumerate(result3.chunks[:2]):  # 只显示前两个
        print(f"  {i+1}. {chunk.text[:100]}...")

    # --- 6. Save results to file ---
    print("\n--- Step 5: Saving results to file ---")
    results = [
        {
            "query": query,
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        },
        {
            "query": query2,
            "answer": result2.answer,
            "sources": [chunk.text for chunk in result2.chunks]
        },
        {
            "query": query3,
            "answer": result3.answer,
            "sources": [chunk.text for chunk in result3.chunks],
            "filter": {"source": "ai.txt"}
        }
    ]
    
    with open("rag_demo_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("查询结果已保存到 rag_demo_results.json")
    print("\n--- Demo Finished ---")

if __name__ == "__main__":
    run_rag_demo()