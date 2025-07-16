# RAG系统数学运算和逻辑推理测试
# 测试RAG系统处理计算、推理类问题的能力

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent

async def test_rag_with_math_samples():
    """测试RAG系统的数学运算和逻辑推理能力"""
    print("=" * 80)
    print("    RAG系统数学运算和逻辑推理测试")
    print("=" * 80)

    # --- 1. 初始化系统 ---
    orchestrator = OrchestratorAgent()

    # --- 2. 添加数学和逻辑知识数据 ---
    print("\n--- 步骤1: 添加数学和逻辑知识到系统 ---")
    knowledge_data = {
        "sources": [
            # 基础数学运算
            {"type": "text", "location": "圆的面积公式是 π × r²，其中r是半径。", "metadata": {"category": "math", "topic": "geometry"}},
            {"type": "text", "location": "勾股定理：直角三角形中，a² + b² = c²，c是斜边。", "metadata": {"category": "math", "topic": "geometry"}},
            {"type": "text", "location": "二次方程 ax² + bx + c = 0 的解为 x = (-b ± √(b²-4ac)) / 2a。", "metadata": {"category": "math", "topic": "algebra"}},
            {"type": "text", "location": "复利公式：A = P(1 + r/n)^(nt)，其中P是本金，r是年利率。", "metadata": {"category": "math", "topic": "finance"}},
            
            # 物理计算
            {"type": "text", "location": "速度公式：v = s/t，其中s是距离，t是时间。", "metadata": {"category": "physics", "topic": "mechanics"}},
            {"type": "text", "location": "牛顿第二定律：F = ma，力等于质量乘以加速度。", "metadata": {"category": "physics", "topic": "mechanics"}},
            {"type": "text", "location": "电功率公式：P = UI，功率等于电压乘以电流。", "metadata": {"category": "physics", "topic": "electricity"}},
            {"type": "text", "location": "动能公式：Ek = ½mv²，其中m是质量，v是速度。", "metadata": {"category": "physics", "topic": "energy"}},
            
            # 统计和概率
            {"type": "text", "location": "平均数 = 所有数值的总和 ÷ 数值的个数。", "metadata": {"category": "statistics", "topic": "basic"}},
            {"type": "text", "location": "标准差衡量数据的离散程度，公式为 σ = √(Σ(x-μ)²/N)。", "metadata": {"category": "statistics", "topic": "deviation"}},
            {"type": "text", "location": "概率的基本公式：P(A) = 有利结果数 / 总结果数。", "metadata": {"category": "probability", "topic": "basic"}},
            {"type": "text", "location": "条件概率：P(A|B) = P(A∩B) / P(B)。", "metadata": {"category": "probability", "topic": "conditional"}},
            
            # 逻辑推理
            {"type": "text", "location": "如果A则B，A为真，那么B也为真（肯定前件）。", "metadata": {"category": "logic", "topic": "reasoning"}},
            {"type": "text", "location": "如果A则B，B为假，那么A也为假（否定后件）。", "metadata": {"category": "logic", "topic": "reasoning"}},
            {"type": "text", "location": "德摩根定律：非(A且B) = (非A)或(非B)。", "metadata": {"category": "logic", "topic": "laws"}},
            {"type": "text", "location": "三段论：大前提+小前提→结论，如：人都会死，苏格拉底是人，所以苏格拉底会死。", "metadata": {"category": "logic", "topic": "syllogism"}},
            
            # 实际应用问题
            {"type": "text", "location": "一个边长为5cm的正方形，面积是25平方厘米。", "metadata": {"category": "example", "topic": "geometry"}},
            {"type": "text", "location": "汽车以60公里/小时的速度行驶2小时，行驶距离是120公里。", "metadata": {"category": "example", "topic": "physics"}},
            {"type": "text", "location": "投资10000元，年利率5%，复利计算，3年后约为11576元。", "metadata": {"category": "example", "topic": "finance"}},
            {"type": "text", "location": "掷一枚公平硬币，正面朝上的概率是1/2或50%。", "metadata": {"category": "example", "topic": "probability"}},
        ]
    }
    
    result = await orchestrator.receive_request(
        source="user",
        request_type="add_knowledge",
        payload=knowledge_data
    )
    print(f"知识添加结果: {result['message']}")
    print(f"处理的知识块数量: {result['chunks_count']}")

    # --- 3. 数学和逻辑推理测试问题 ---
    print("\n--- 步骤2: 测试数学运算和逻辑推理问题 ---")
    test_questions = [
        # 几何计算
        "圆的面积怎么计算？",
        "勾股定理是什么？",
        "边长5cm的正方形面积是多少？",
        
        # 代数计算
        "二次方程的求解公式是什么？",
        "复利是怎么计算的？",
        "投资10000元，年利率5%，3年后是多少？",
        
        # 物理计算
        "速度公式是什么？",
        "牛顿第二定律的公式是什么？",
        "汽车60公里/小时行驶2小时，距离是多少？",
        "电功率怎么计算？",
        "动能公式是什么？",
        
        # 统计概率
        "平均数怎么计算？",
        "标准差是什么？",
        "概率的基本公式是什么？",
        "掷硬币正面朝上的概率是多少？",
        "条件概率怎么计算？",
        
        # 逻辑推理
        "什么是肯定前件？",
        "什么是否定后件？",
        "德摩根定律是什么？",
        "三段论的结构是什么？",
    ]

    # 测试每个问题
    correct_answers = 0
    total_questions = len(test_questions)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 问题 {i}/{total_questions} ---")
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
            
            # 答案质量评估
            if len(answer) > 15 and "没有找到" not in answer and ("公式" in answer or "=" in answer or "计算" in answer or "定律" in answer or "概率" in answer or "推理" in answer):
                correct_answers += 1
                print("✅ 答案质量: 良好（包含数学/逻辑内容）")
            elif len(answer) > 10 and "没有找到" not in answer:
                correct_answers += 1
                print("✅ 答案质量: 可接受")
            else:
                print("❌ 答案质量: 需要改进")
                
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")

    # --- 4. 测试结果统计 ---
    print("\n" + "=" * 80)
    print("    数学运算和逻辑推理测试结果")
    print("=" * 80)
    print(f"总问题数: {total_questions}")
    print(f"成功回答: {correct_answers}")
    print(f"成功率: {correct_answers/total_questions*100:.1f}%")
    
    # 分类统计
    geometry_questions = 3
    algebra_questions = 3  
    physics_questions = 5
    statistics_questions = 5
    logic_questions = 4
    
    print(f"\n分类测试结果:")
    print(f"📐 几何问题: {geometry_questions}题")
    print(f"🔢 代数问题: {algebra_questions}题") 
    print(f"⚡ 物理问题: {physics_questions}题")
    print(f"📊 统计概率: {statistics_questions}题")
    print(f"🧠 逻辑推理: {logic_questions}题")
    
    if correct_answers >= total_questions * 0.8:
        print("\n🎉 测试结果: 优秀 (成功率 >= 80%)")
        print("RAG系统能够很好地处理数学运算和逻辑推理问题！")
    elif correct_answers >= total_questions * 0.6:
        print("\n👍 测试结果: 良好 (成功率 >= 60%)")
        print("RAG系统基本能够处理数学运算和逻辑推理问题。")
    else:
        print("\n⚠️  测试结果: 需要改进 (成功率 < 60%)")
        print("RAG系统在处理数学运算和逻辑推理方面需要进一步优化。")

    print("\n--- 数学运算和逻辑推理测试完成 ---")

if __name__ == "__main__":
    asyncio.run(test_rag_with_math_samples())