#!/usr/bin/env python3
"""
高级RAG测试 - 测试复杂查询场景和系统边界
"""

import asyncio
import logging
import time
import json
from knowledge_base import KnowledgeBase, Config, Document
from knowledge_base.core.types import DocumentType

# 配置日志
logging.basicConfig(level=logging.ERROR)  # 只显示错误
logger = logging.getLogger(__name__)


# 更丰富的测试文档
ADVANCED_DOCUMENTS = [
    Document(
        id="python_advanced",
        content="""Python高级特性包括装饰器、生成器、上下文管理器和元类。装饰器用于修改函数或类的行为，生成器提供内存高效的迭代方式。上下文管理器通过__enter__和__exit__方法管理资源，元类控制类的创建过程。Python还支持多重继承、属性描述符、异步编程等高级概念。GIL（全局解释器锁）限制了Python的多线程性能，但可以通过多进程或异步编程来解决。""",
        type=DocumentType.TEXT,
        metadata={"topic": "python", "level": "advanced", "concepts": ["decorators", "generators", "metaclass"]}
    ),
    Document(
        id="ai_ethics",
        content="""人工智能伦理是研究AI系统对社会、个人和环境影响的学科。主要关注点包括算法偏见、隐私保护、透明度、责任归属和社会公平。AI偏见可能来源于训练数据、算法设计或应用场景。解决方案包括多样化数据集、公平性约束、可解释AI和伦理审查。AI治理需要技术专家、政策制定者、伦理学家和社会各界的共同参与。""",
        type=DocumentType.TEXT,
        metadata={"topic": "ai", "field": "ethics", "level": "advanced", "concerns": ["bias", "privacy", "fairness"]}
    ),
    Document(
        id="quantum_computing",
        content="""量子计算利用量子力学原理进行信息处理，具有超越经典计算机的潜力。量子比特（qubit）可以同时处于0和1的叠加态，量子纠缠允许量子比特之间的瞬时关联。主要量子算法包括Shor算法（因数分解）和Grover算法（搜索）。当前的量子计算机仍处于NISQ（噪声中等规模量子）阶段，面临量子退相干、错误率高等挑战。IBM、Google、微软等公司在量子计算领域投入巨大。""",
        type=DocumentType.TEXT,
        metadata={"topic": "quantum", "field": "computing", "level": "expert", "algorithms": ["shor", "grover"]}
    ),
    Document(
        id="blockchain_tech",
        content="""区块链是一种分布式账本技术，通过密码学哈希链接区块，确保数据不可篡改。共识机制包括工作量证明（PoW）、权益证明（PoS）和委托权益证明（DPoS）。智能合约是运行在区块链上的自执行代码，以太坊是最著名的智能合约平台。区块链应用包括加密货币、供应链管理、数字身份、去中心化金融（DeFi）等。挑战包括可扩展性、能耗、监管合规等问题。""",
        type=DocumentType.TEXT,
        metadata={"topic": "blockchain", "applications": ["cryptocurrency", "defi", "supply_chain"], "level": "intermediate"}
    ),
    Document(
        id="cybersecurity_trends",
        content="""网络安全威胁不断演进，包括高级持续威胁（APT）、勒索软件、零日漏洞和社会工程攻击。防护策略采用纵深防御理念，包括网络分段、零信任架构、威胁情报和行为分析。新兴技术如AI和机器学习被用于威胁检测和响应自动化。云安全、IoT安全和移动安全成为新的关注点。网络安全人才短缺是全球性问题，需要加强教育培训和国际合作。""",
        type=DocumentType.TEXT,
        metadata={"topic": "security", "threats": ["apt", "ransomware", "zero_day"], "level": "expert"}
    )
]

# 复杂查询测试用例
COMPLEX_QUERIES = [
    # 多概念关联查询
    {
        "query": "Python装饰器和生成器的区别是什么？",
        "type": "comparison",
        "expected_concepts": ["decorators", "generators"],
        "difficulty": "medium"
    },
    {
        "query": "How does quantum entanglement relate to quantum computing algorithms?",
        "type": "relationship",
        "expected_concepts": ["quantum", "algorithms"],
        "difficulty": "hard"
    },
    
    # 跨领域查询
    {
        "query": "AI伦理在区块链应用中的考虑因素",
        "type": "cross_domain",
        "expected_concepts": ["ai", "ethics", "blockchain"],
        "difficulty": "hard"
    },
    {
        "query": "量子计算对网络安全的影响",
        "type": "cross_domain",
        "expected_concepts": ["quantum", "security"],
        "difficulty": "hard"
    },
    
    # 深度技术查询
    {
        "query": "Shor算法如何威胁现有的加密系统？",
        "type": "technical_deep",
        "expected_concepts": ["shor", "encryption"],
        "difficulty": "expert"
    },
    {
        "query": "零信任架构如何防御APT攻击？",
        "type": "technical_deep",
        "expected_concepts": ["zero_trust", "apt"],
        "difficulty": "expert"
    },
    
    # 趋势分析查询
    {
        "query": "未来5年网络安全的主要挑战",
        "type": "trend_analysis",
        "expected_concepts": ["security", "future"],
        "difficulty": "medium"
    },
    {
        "query": "量子计算商业化的时间表和障碍",
        "type": "trend_analysis",
        "expected_concepts": ["quantum", "commercial"],
        "difficulty": "hard"
    },
    
    # 解决方案查询
    {
        "query": "如何解决AI算法中的偏见问题？",
        "type": "solution",
        "expected_concepts": ["ai", "bias", "fairness"],
        "difficulty": "medium"
    },
    {
        "query": "区块链可扩展性问题的解决方案",
        "type": "solution",
        "expected_concepts": ["blockchain", "scalability"],
        "difficulty": "medium"
    },
    
    # 对比分析查询
    {
        "query": "PoW vs PoS共识机制的优缺点",
        "type": "comparison",
        "expected_concepts": ["pow", "pos", "consensus"],
        "difficulty": "medium"
    },
    {
        "query": "传统计算与量子计算的根本差异",
        "type": "comparison",
        "expected_concepts": ["classical", "quantum", "computing"],
        "difficulty": "medium"
    },
    
    # 应用场景查询
    {
        "query": "智能合约在供应链管理中的具体应用",
        "type": "application",
        "expected_concepts": ["smart_contract", "supply_chain"],
        "difficulty": "medium"
    },
    {
        "query": "Python元类在实际项目中的使用场景",
        "type": "application",
        "expected_concepts": ["metaclass", "practical"],
        "difficulty": "hard"
    },
    
    # 挑战性查询
    {
        "query": "如何在保护隐私的同时实现AI系统的透明度？",
        "type": "paradox",
        "expected_concepts": ["privacy", "transparency", "ai"],
        "difficulty": "expert"
    },
    {
        "query": "量子计算机如何同时利用叠加态和纠缠态？",
        "type": "technical_complex",
        "expected_concepts": ["superposition", "entanglement"],
        "difficulty": "expert"
    }
]

# 边界测试用例
EDGE_CASES = [
    {"query": "", "expected": "validation_error"},
    {"query": "a", "expected": "low_confidence"},
    {"query": "xyz123不存在的概念", "expected": "no_match"},
    {"query": "Python " * 50, "expected": "handle_repetition"},
    {"query": "非常非常非常长的查询" * 20, "expected": "handle_long_query"},
    {"query": "🤖🔬💻🚀", "expected": "handle_emoji"},
    {"query": "SELECT * FROM users WHERE id=1; DROP TABLE users;", "expected": "handle_injection"},
]


async def setup_advanced_kb():
    """设置高级知识库"""
    config = Config()
    config.storage.provider = "memory"
    config.embedding.provider = "sentence_transformers"
    config.generation.provider = "ollama"
    
    kb = KnowledgeBase(config)
    await kb.initialize()
    
    print("📚 添加高级测试文档...")
    result = await kb.add_documents(ADVANCED_DOCUMENTS)
    
    if result.success:
        print(f"✅ 成功添加 {len(ADVANCED_DOCUMENTS)} 个高级文档，生成 {result.chunks_created} 个chunks")
    else:
        print(f"❌ 文档添加失败: {result.error_message}")
        return None
    
    return kb


async def run_complex_queries(kb: KnowledgeBase):
    """运行复杂查询测试"""
    print(f"\n🧠 开始复杂查询测试 ({len(COMPLEX_QUERIES)} 个查询)...\n")
    
    results = []
    difficulty_stats = {"medium": 0, "hard": 0, "expert": 0}
    type_stats = {}
    
    for i, test_case in enumerate(COMPLEX_QUERIES, 1):
        query = test_case["query"]
        query_type = test_case["type"]
        difficulty = test_case["difficulty"]
        expected_concepts = test_case["expected_concepts"]
        
        print(f"[{i:2d}/{len(COMPLEX_QUERIES)}] {query_type.upper()} ({difficulty})")
        print(f"    查询: {query}")
        
        start_time = time.time()
        try:
            result = await kb.query(query, top_k=5)
            query_time = time.time() - start_time
            
            # 评估结果质量
            quality_score = evaluate_result_quality(result, expected_concepts)
            
            print(f"    答案: {result.answer[:80]}...")
            print(f"    质量: {quality_score:.2f}, 置信度: {result.confidence:.2f}, 用时: {query_time:.3f}s")
            
            results.append({
                "query": query,
                "type": query_type,
                "difficulty": difficulty,
                "quality_score": quality_score,
                "confidence": result.confidence,
                "time": query_time,
                "source_count": len(result.sources)
            })
            
            difficulty_stats[difficulty] += 1
            type_stats[query_type] = type_stats.get(query_type, 0) + 1
            
        except Exception as e:
            print(f"    ❌ 查询失败: {e}")
            results.append({
                "query": query,
                "type": query_type,
                "difficulty": difficulty,
                "error": str(e),
                "time": time.time() - start_time
            })
        
        print()
    
    return results, difficulty_stats, type_stats


async def run_edge_case_tests(kb: KnowledgeBase):
    """运行边界情况测试"""
    print("🔬 边界情况测试")
    print("-" * 40)
    
    edge_results = []
    
    for i, test_case in enumerate(EDGE_CASES, 1):
        query = test_case["query"]
        expected = test_case["expected"]
        
        print(f"[{i}] 测试: {expected}")
        print(f"    查询: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        try:
            result = await kb.query(query)
            status = "handled"
            confidence = result.confidence
            print(f"    结果: 正常处理, 置信度: {confidence:.2f}")
        except Exception as e:
            status = "error"
            confidence = 0.0
            print(f"    结果: 异常 - {type(e).__name__}")
        
        edge_results.append({
            "query": query,
            "expected": expected,
            "status": status,
            "confidence": confidence
        })
        print()
    
    return edge_results


def evaluate_result_quality(result, expected_concepts):
    """评估结果质量"""
    # 简单的质量评估算法
    base_score = result.confidence
    
    # 检查答案长度（太短或太长都不好）
    answer_length = len(result.answer)
    if 50 <= answer_length <= 300:
        length_bonus = 0.1
    elif 30 <= answer_length <= 500:
        length_bonus = 0.05
    else:
        length_bonus = -0.1
    
    # 检查来源数量
    source_bonus = min(0.1, len(result.sources) * 0.02)
    
    # 概念匹配检查（简化版）
    concept_bonus = 0.0
    answer_lower = result.answer.lower()
    for concept in expected_concepts:
        if concept.lower() in answer_lower:
            concept_bonus += 0.05
    
    quality_score = base_score + length_bonus + source_bonus + concept_bonus
    return min(1.0, max(0.0, quality_score))


def analyze_advanced_results(results, difficulty_stats, type_stats, edge_results):
    """分析高级测试结果"""
    print("=" * 60)
    print("📊 高级RAG测试结果分析")
    print("=" * 60)
    
    successful_results = [r for r in results if "error" not in r]
    failed_results = [r for r in results if "error" in r]
    
    print(f"复杂查询测试:")
    print(f"  总查询数: {len(results)}")
    print(f"  成功查询: {len(successful_results)} ({len(successful_results)/len(results)*100:.1f}%)")
    print(f"  失败查询: {len(failed_results)} ({len(failed_results)/len(results)*100:.1f}%)")
    
    if successful_results:
        avg_quality = sum(r["quality_score"] for r in successful_results) / len(successful_results)
        avg_confidence = sum(r["confidence"] for r in successful_results) / len(successful_results)
        avg_time = sum(r["time"] for r in successful_results) / len(successful_results)
        
        print(f"\n成功查询统计:")
        print(f"  平均质量分: {avg_quality:.2f}")
        print(f"  平均置信度: {avg_confidence:.2f}")
        print(f"  平均用时: {avg_time:.3f}s")
    
    # 难度分析
    print(f"\n难度分布:")
    for difficulty, count in difficulty_stats.items():
        success_rate = len([r for r in successful_results if r["difficulty"] == difficulty]) / count * 100
        print(f"  {difficulty}: {count}个查询, 成功率: {success_rate:.1f}%")
    
    # 类型分析
    print(f"\n查询类型分布:")
    for query_type, count in type_stats.items():
        success_rate = len([r for r in successful_results if r["type"] == query_type]) / count * 100
        print(f"  {query_type}: {count}个查询, 成功率: {success_rate:.1f}%")
    
    # 边界情况分析
    print(f"\n边界情况测试:")
    handled_count = len([r for r in edge_results if r["status"] == "handled"])
    error_count = len([r for r in edge_results if r["status"] == "error"])
    print(f"  正常处理: {handled_count}/{len(edge_results)}")
    print(f"  异常情况: {error_count}/{len(edge_results)}")
    
    # 性能分析
    if successful_results:
        times = [r["time"] for r in successful_results]
        print(f"\n性能分析:")
        print(f"  最快查询: {min(times):.3f}s")
        print(f"  最慢查询: {max(times):.3f}s")
        print(f"  时间中位数: {sorted(times)[len(times)//2]:.3f}s")


async def test_concurrent_queries(kb: KnowledgeBase):
    """测试并发查询性能"""
    print("\n⚡ 并发查询测试")
    print("-" * 40)
    
    # 准备并发查询
    concurrent_queries = [
        "Python装饰器的作用",
        "量子计算的优势",
        "区块链共识机制",
        "AI伦理问题",
        "网络安全威胁"
    ] * 4  # 20个并发查询
    
    print(f"执行 {len(concurrent_queries)} 个并发查询...")
    
    start_time = time.time()
    
    # 并发执行查询
    tasks = [kb.query(query) for query in concurrent_queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_time = time.time() - start_time
    
    # 分析结果
    successful = len([r for r in results if not isinstance(r, Exception)])
    failed = len([r for r in results if isinstance(r, Exception)])
    
    print(f"并发测试结果:")
    print(f"  总查询数: {len(concurrent_queries)}")
    print(f"  成功查询: {successful}")
    print(f"  失败查询: {failed}")
    print(f"  总用时: {total_time:.2f}s")
    print(f"  QPS: {len(concurrent_queries)/total_time:.1f}")
    print(f"  平均延迟: {total_time/len(concurrent_queries)*1000:.1f}ms")


async def main():
    """主测试函数"""
    print("🚀 高级RAG测试开始")
    print("=" * 60)
    
    try:
        # 设置知识库
        kb = await setup_advanced_kb()
        if not kb:
            return
        
        # 运行复杂查询测试
        results, difficulty_stats, type_stats = await run_complex_queries(kb)
        
        # 运行边界情况测试
        edge_results = await run_edge_case_tests(kb)
        
        # 分析结果
        analyze_advanced_results(results, difficulty_stats, type_stats, edge_results)
        
        # 并发测试
        await test_concurrent_queries(kb)
        
        # 关闭知识库
        await kb.close()
        
        print("\n✅ 高级RAG测试完成!")
        
        # 保存详细结果
        test_report = {
            "timestamp": time.time(),
            "complex_queries": results,
            "edge_cases": edge_results,
            "difficulty_stats": difficulty_stats,
            "type_stats": type_stats
        }
        
        with open("advanced_rag_results.json", "w", encoding="utf-8") as f:
            json.dump(test_report, f, ensure_ascii=False, indent=2)
        
        print("📄 详细结果已保存到 advanced_rag_results.json")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())