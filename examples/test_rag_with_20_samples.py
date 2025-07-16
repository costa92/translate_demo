# RAG系统20条测试数据演示
# 测试改进后的RAG问答系统的精确性和多样性

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def test_rag_with_20_samples():
    """使用20条测试数据全面测试RAG系统"""
    print("=" * 80)
    print("    RAG系统20条测试数据演示")
    print("=" * 80)

    # --- 1. 初始化系统 ---
    orchestrator = OrchestratorAgent()

    # --- 2. 添加20条知识数据 ---
    print("\n--- 步骤1: 添加20条知识到系统 ---")
    knowledge_data = {
        "sources": [
            # 科学知识
            {"type": "text", "location": "太阳是太阳系的中心恒星，表面温度约5778K。", "metadata": {"category": "science", "topic": "astronomy"}},
            {"type": "text", "location": "水的化学分子式是H2O，由两个氢原子和一个氧原子组成。", "metadata": {"category": "science", "topic": "chemistry"}},
            {"type": "text", "location": "光速在真空中约为每秒30万公里。", "metadata": {"category": "science", "topic": "physics"}},
            {"type": "text", "location": "DNA是脱氧核糖核酸的缩写，携带遗传信息。", "metadata": {"category": "science", "topic": "biology"}},
            
            # 技术知识
            {"type": "text", "location": "Python是一种高级编程语言，以简洁易读著称。", "metadata": {"category": "technology", "topic": "programming"}},
            {"type": "text", "location": "Git是分布式版本控制系统，用于跟踪代码变更。", "metadata": {"category": "technology", "topic": "tools"}},
            {"type": "text", "location": "Docker是容器化平台，可以打包应用及其依赖。", "metadata": {"category": "technology", "topic": "devops"}},
            {"type": "text", "location": "React是Facebook开发的JavaScript前端框架。", "metadata": {"category": "technology", "topic": "web"}},
            
            # 历史知识
            {"type": "text", "location": "中国的万里长城建于公元前7世纪，是世界文化遗产。", "metadata": {"category": "history", "topic": "china"}},
            {"type": "text", "location": "第二次世界大战于1939年开始，1945年结束。", "metadata": {"category": "history", "topic": "world"}},
            {"type": "text", "location": "古埃及金字塔建于公元前2580-2510年间。", "metadata": {"category": "history", "topic": "ancient"}},
            {"type": "text", "location": "美国独立宣言签署于1776年7月4日。", "metadata": {"category": "history", "topic": "america"}},
            
            # 地理知识
            {"type": "text", "location": "珠穆朗玛峰是世界最高峰，海拔8848.86米。", "metadata": {"category": "geography", "topic": "mountains"}},
            {"type": "text", "location": "亚马逊河是世界上流量最大的河流。", "metadata": {"category": "geography", "topic": "rivers"}},
            {"type": "text", "location": "撒哈拉沙漠是世界第三大沙漠。", "metadata": {"category": "geography", "topic": "deserts"}},
            {"type": "text", "location": "太平洋是世界上最大的海洋。", "metadata": {"category": "geography", "topic": "oceans"}},
            
            # 文化知识
            {"type": "text", "location": "莎士比亚是英国著名剧作家，代表作有《哈姆雷特》。", "metadata": {"category": "culture", "topic": "literature"}},
            {"type": "text", "location": "贝多芬是德国古典音乐作曲家，创作了九部交响曲。", "metadata": {"category": "culture", "topic": "music"}},
            {"type": "text", "location": "达芬奇的《蒙娜丽莎》是世界著名画作。", "metadata": {"category": "culture", "topic": "art"}},
            {"type": "text", "location": "奥运会每四年举办一次，起源于古希腊。", "metadata": {"category": "culture", "topic": "sports"}},
        ]
    }
    
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=knowledge_data
    )
    print(f"知识添加结果: {result['message']}")
    print(f"处理的知识块数量: {result['chunks_count']}")

    # --- 3. 20个测试问题 ---
    print("\n--- 步骤2: 测试20个问题 ---")
    test_questions = [
        # 科学问题
        "太阳的表面温度是多少？",
        "水的分子式是什么？",
        "光速是多少？",
        "DNA的全称是什么？",
        
        # 技术问题
        "Python语言有什么特点？",
        "Git是什么？",
        "Docker的作用是什么？",
        "React是谁开发的？",
        
        # 历史问题
        "万里长城什么时候建造的？",
        "第二次世界大战什么时候结束？",
        "金字塔建于什么时期？",
        "美国独立宣言什么时候签署？",
        
        # 地理问题
        "世界最高峰是什么？",
        "世界上流量最大的河流是哪条？",
        "撒哈拉沙漠排名第几？",
        "最大的海洋是哪个？",
        
        # 文化问题
        "莎士比亚的代表作是什么？",
        "贝多芬创作了几部交响曲？",
        "蒙娜丽莎是谁画的？",
        "奥运会多久举办一次？"
    ]

    # 测试每个问题
    correct_answers = 0
    total_questions = len(test_questions)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 问题 {i}/20 ---")
        print(f"问题: {question}")
        
        query_payload = {
            "query": question,
            "search_params": {
                "top_k": 3
            }
        }
        
        try:
            query_result = await orchestrator.receive_request(
                source="user",
                request_type="query",
                payload=query_payload
            )
            
            answer = query_result['answer']
            sources_count = len(query_result['retrieved_sources'])
            
            print(f"答案: {answer}")
            print(f"检索到的相关源数量: {sources_count}")
            
            # 简单的答案质量评估
            if len(answer) > 10 and "没有找到" not in answer:
                correct_answers += 1
                print("✅ 答案质量: 良好")
            else:
                print("❌ 答案质量: 需要改进")
                
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")

    # --- 4. 测试结果统计 ---
    print("\n" + "=" * 80)
    print("    测试结果统计")
    print("=" * 80)
    print(f"总问题数: {total_questions}")
    print(f"成功回答: {correct_answers}")
    print(f"成功率: {correct_answers/total_questions*100:.1f}%")
    
    if correct_answers >= total_questions * 0.8:
        print("🎉 测试结果: 优秀 (成功率 >= 80%)")
    elif correct_answers >= total_questions * 0.6:
        print("👍 测试结果: 良好 (成功率 >= 60%)")
    else:
        print("⚠️  测试结果: 需要改进 (成功率 < 60%)")

    print("\n--- 测试完成 ---")

if __name__ == "__main__":
    asyncio.run(test_rag_with_20_samples())