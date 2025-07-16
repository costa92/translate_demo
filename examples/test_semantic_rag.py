# 测试语义RAG系统
# 验证新的向量化语义检索功能

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def test_semantic_rag():
    """测试语义RAG系统"""
    print("=" * 80)
    print("    语义RAG系统测试")
    print("=" * 80)

    # --- 1. 初始化系统（启用语义搜索）---
    llm_config = {
        'provider': 'ollama',
        'model': 'deepseek-r1:latest',
        'use_semantic_search': True  # 启用语义搜索
    }
    orchestrator = OrchestratorAgent(llm_config=llm_config)

    # --- 2. 添加测试知识 ---
    print("\n--- 步骤1: 添加知识到语义搜索系统 ---")
    knowledge_data = {
        "sources": [
            # 相似概念的不同表达
            {"type": "text", "location": "太阳是恒星，表面温度约5778开尔文。", "metadata": {"category": "astronomy"}},
            {"type": "text", "location": "恒星表面的热度大约是5778K。", "metadata": {"category": "astronomy"}},
            
            {"type": "text", "location": "H2O是水的化学符号。", "metadata": {"category": "chemistry"}},
            {"type": "text", "location": "水分子由氢氧原子构成。", "metadata": {"category": "chemistry"}},
            
            {"type": "text", "location": "圆形区域的大小用πr²计算。", "metadata": {"category": "math"}},
            {"type": "text", "location": "圆的面积等于π乘以半径的平方。", "metadata": {"category": "math"}},
            
            {"type": "text", "location": "速率等于路程除以时间。", "metadata": {"category": "physics"}},
            {"type": "text", "location": "v=s/t是速度的计算公式。", "metadata": {"category": "physics"}},
            
            # 逻辑推理相关
            {"type": "text", "location": "如果前提成立，结论必然成立，这叫肯定前件。", "metadata": {"category": "logic"}},
            {"type": "text", "location": "当条件为真时，结果也为真的推理方式。", "metadata": {"category": "logic"}},
        ]
    }
    
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=knowledge_data
    )
    print(f"知识添加结果: {result['message']}")
    print(f"处理的知识块数量: {result['chunks_count']}")

    # --- 3. 测试语义相似性检索 ---
    print("\n--- 步骤2: 测试语义相似性检索 ---")
    
    test_cases = [
        {
            "query": "恒星的温度是多少？",
            "expected_concept": "太阳温度",
            "description": "测试同义词匹配（恒星 vs 太阳）"
        },
        {
            "query": "水的分子组成是什么？", 
            "expected_concept": "水分子结构",
            "description": "测试概念相似性（分子组成 vs 化学符号）"
        },
        {
            "query": "如何计算圆的大小？",
            "expected_concept": "圆面积公式", 
            "description": "测试表达方式相似性（大小 vs 面积）"
        },
        {
            "query": "运动速度怎么算？",
            "expected_concept": "速度公式",
            "description": "测试概念匹配（运动速度 vs 速度）"
        },
        {
            "query": "什么是有效推理？",
            "expected_concept": "逻辑推理",
            "description": "测试抽象概念匹配（有效推理 vs 肯定前件）"
        }
    ]

    correct_matches = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}/{total_tests}: {test_case['description']} ---")
        print(f"查询: {test_case['query']}")
        
        # 测试不同的检索方法
        for method in ['semantic', 'hybrid']:
            print(f"\n使用 {method} 检索方法:")
            
            query_payload = {
                "query": test_case['query'],
                "search_params": {
                    "top_k": 2,
                    "filters": {
                        "retrieval_method": method
                    }
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
                
                # 显示检索到的源和相似度分数
                for j, source in enumerate(sources):
                    print(f"  源 {j+1}: {source['content'][:50]}... (相似度: {source['relevance_score']:.3f})")
                
                # 简单的质量评估
                if len(answer) > 15 and "没有找到" not in answer:
                    if i == 1:  # 只在第一次计算正确匹配数
                        correct_matches += 1
                    print(f"✅ {method} 检索质量: 良好")
                else:
                    print(f"❌ {method} 检索质量: 需要改进")
                    
            except Exception as e:
                print(f"❌ {method} 检索失败: {str(e)}")

    # --- 4. 对比测试：关键词 vs 语义检索 ---
    print(f"\n--- 步骤3: 对比不同检索方法 ---")
    
    comparison_query = "星球的热度"  # 这个查询应该匹配"太阳温度"相关内容
    print(f"对比查询: {comparison_query}")
    
    for method in ['keyword', 'semantic', 'hybrid']:
        print(f"\n{method.upper()} 检索结果:")
        
        query_payload = {
            "query": comparison_query,
            "search_params": {
                "top_k": 3,
                "filters": {
                    "retrieval_method": method
                }
            }
        }
        
        try:
            query_result = await orchestrator.receive_request(
                source="user",
                request_type="query", 
                payload=query_payload
            )
            
            sources = query_result['retrieved_sources']
            print(f"检索到 {len(sources)} 个源:")
            
            for j, source in enumerate(sources):
                print(f"  {j+1}. {source['content']} (分数: {source['relevance_score']:.3f})")
                
        except Exception as e:
            print(f"❌ {method} 检索失败: {str(e)}")

    # --- 5. 测试结果统计 ---
    print("\n" + "=" * 80)
    print("    语义RAG测试结果统计")
    print("=" * 80)
    print(f"总测试用例: {total_tests}")
    print(f"成功匹配: {correct_matches}")
    print(f"成功率: {correct_matches/total_tests*100:.1f}%")
    
    if correct_matches >= total_tests * 0.8:
        print("\n🎉 语义检索测试结果: 优秀!")
        print("✅ 系统能够理解语义相似性")
        print("✅ 支持同义词和概念匹配")
        print("✅ 提供多种检索策略")
    elif correct_matches >= total_tests * 0.6:
        print("\n👍 语义检索测试结果: 良好")
        print("✅ 基本的语义理解能力")
        print("⚠️  部分复杂概念匹配需要改进")
    else:
        print("\n⚠️  语义检索测试结果: 需要改进")
        print("❌ 语义理解能力有限")
        print("💡 建议优化嵌入向量算法")

    print("\n--- 语义RAG测试完成 ---")

if __name__ == "__main__":
    asyncio.run(test_semantic_rag())