# 测试使用 DeepSeek (Ollama) 的 RAG 系统

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def test_deepseek_rag():
    """测试使用 DeepSeek 的 RAG 系统"""
    print("=" * 80)
    print("    DeepSeek RAG 系统测试")
    print("=" * 80)

    # --- 1. 初始化系统（使用 Ollama DeepSeek）---
    llm_config = {
        'provider': 'ollama',
        'model': 'deepseek-r1:latest',
        'use_semantic_search': True
    }
    print(f"配置的 LLM 提供商: {llm_config['provider']}")
    print(f"配置的模型: {llm_config['model']}")
    
    orchestrator = OrchestratorAgent(llm_config=llm_config)

    # --- 2. 添加测试知识 ---
    print("\n--- 步骤1: 添加知识到系统 ---")
    knowledge_data = {
        "sources": [
            {"type": "text", "location": "太阳是恒星，表面温度约5778开尔文。", "metadata": {"category": "astronomy"}},
            {"type": "text", "location": "水分子由氢氧原子构成。", "metadata": {"category": "chemistry"}},
            {"type": "text", "location": "圆的面积等于π乘以半径的平方。", "metadata": {"category": "math"}},
        ]
    }
    
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=knowledge_data
    )
    print(f"知识添加结果: {result['message']}")
    print(f"处理的知识块数量: {result['chunks_count']}")

    # --- 3. 测试问答 ---
    print("\n--- 步骤2: 测试问答 ---")
    
    test_questions = [
        "太阳的温度是多少？",
        "水分子是什么组成的？",
        "如何计算圆的面积？"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 问题 {i}: {question} ---")
        
        query_payload = {
            "query": question,
            "search_params": {
                "top_k": 2
            }
        }
        
        try:
            query_result = await orchestrator.receive_request(
                source="user",
                request_type="query",
                payload=query_payload
            )
            
            answer = query_result['answer']
            sources = query_result['retrieved_sources']
            
            print(f"答案: {answer}")
            print(f"检索到 {len(sources)} 个相关源")
            
            for j, source in enumerate(sources):
                print(f"  源 {j+1}: {source['content'][:50]}... (相似度: {source['relevance_score']:.3f})")
                
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")

    print("\n--- DeepSeek RAG 测试完成 ---")

if __name__ == "__main__":
    asyncio.run(test_deepseek_rag())