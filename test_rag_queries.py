#!/usr/bin/env python3
"""
RAG查询测试 - 测试知识库系统的检索和问答能力
包含20个不同类型的查询，涵盖各种场景
"""

import asyncio
import logging
import time
from knowledge_base import KnowledgeBase, Config, Document
from knowledge_base.core.types import DocumentType

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出
logger = logging.getLogger(__name__)


# 测试文档数据
TEST_DOCUMENTS = [
    Document(
        id="python_basics",
        content="""Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python设计哲学强调代码的可读性和简洁性，其语法允许程序员用更少的代码行表达想法。Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。Python拥有动态类型系统和垃圾回收功能，能够自动进行内存管理。Python的标准库非常丰富，被称为"内置电池"。""",
        type=DocumentType.TEXT,
        metadata={"topic": "programming", "language": "python", "level": "basic"}
    ),
    Document(
        id="fastapi_framework",
        content="""FastAPI是一个现代、快速（高性能）的Web框架，用于构建Python API。它基于标准Python类型提示，支持异步编程。FastAPI的主要特点包括：快速编码、减少bug、直观易用、符合标准。它自动生成API文档，支持OpenAPI和JSON Schema。FastAPI基于Starlette构建，性能与NodeJS和Go相当。它还提供了自动数据验证、序列化和文档生成功能。""",
        type=DocumentType.TEXT,
        metadata={"topic": "web_framework", "language": "python", "level": "intermediate"}
    ),
    Document(
        id="machine_learning",
        content="""机器学习是人工智能的一个分支，它使用算法和统计模型来让计算机系统能够有效地执行特定任务，而无需明确的指令。机器学习算法通过训练数据来构建数学模型，以便对新数据进行预测或决策。主要的机器学习类型包括监督学习、无监督学习和强化学习。常见的机器学习算法有线性回归、决策树、随机森林、支持向量机和神经网络等。""",
        type=DocumentType.TEXT,
        metadata={"topic": "ai", "field": "machine_learning", "level": "intermediate"}
    ),
    Document(
        id="data_structures",
        content="""数据结构是计算机科学中组织和存储数据的方式。常见的数据结构包括数组、链表、栈、队列、树、图和哈希表。每种数据结构都有其特定的用途和性能特征。数组提供快速的随机访问，链表支持动态插入和删除，栈遵循后进先出原则，队列遵循先进先出原则。树结构用于层次化数据，图用于表示复杂的关系网络，哈希表提供快速的键值查找。""",
        type=DocumentType.TEXT,
        metadata={"topic": "computer_science", "field": "data_structures", "level": "basic"}
    ),
    Document(
        id="database_systems",
        content="""数据库系统是用于存储、管理和检索数据的软件系统。关系型数据库使用表格结构存储数据，支持SQL查询语言。主要的关系型数据库包括MySQL、PostgreSQL、Oracle和SQL Server。NoSQL数据库适用于大规模、分布式的数据存储需求，包括文档数据库（如MongoDB）、键值数据库（如Redis）、列族数据库（如Cassandra）和图数据库（如Neo4j）。数据库设计需要考虑数据完整性、性能优化和扩展性。""",
        type=DocumentType.TEXT,
        metadata={"topic": "database", "field": "systems", "level": "intermediate"}
    ),
    Document(
        id="web_security",
        content="""Web安全是保护Web应用程序和网站免受各种网络攻击的实践。常见的Web安全威胁包括SQL注入、跨站脚本攻击（XSS）、跨站请求伪造（CSRF）、会话劫持和拒绝服务攻击（DDoS）。防护措施包括输入验证、输出编码、使用HTTPS、实施访问控制、定期安全审计和保持软件更新。Web应用防火墙（WAF）可以提供额外的保护层。安全开发生命周期（SDLC）应该将安全考虑融入到开发的每个阶段。""",
        type=DocumentType.TEXT,
        metadata={"topic": "security", "field": "web_security", "level": "advanced"}
    ),
    Document(
        id="cloud_computing",
        content="""云计算是通过互联网提供计算服务的模式，包括服务器、存储、数据库、网络、软件、分析和智能服务。云计算的主要服务模型包括基础设施即服务（IaaS）、平台即服务（PaaS）和软件即服务（SaaS）。部署模型包括公有云、私有云、混合云和多云。主要的云服务提供商有Amazon Web Services（AWS）、Microsoft Azure、Google Cloud Platform（GCP）和阿里云。云计算的优势包括成本效益、可扩展性、灵活性和可靠性。""",
        type=DocumentType.TEXT,
        metadata={"topic": "cloud", "field": "computing", "level": "intermediate"}
    ),
    Document(
        id="algorithms",
        content="""算法是解决问题的一系列明确指令或规则。算法分析主要关注时间复杂度和空间复杂度。常见的算法包括排序算法（如快速排序、归并排序、堆排序）、搜索算法（如二分搜索、深度优先搜索、广度优先搜索）、动态规划算法和贪心算法。算法设计技术包括分治法、动态规划、贪心策略和回溯法。选择合适的算法对于程序的性能至关重要。大O记号用于描述算法的渐近复杂度。""",
        type=DocumentType.TEXT,
        metadata={"topic": "computer_science", "field": "algorithms", "level": "intermediate"}
    )
]

# 20个测试查询
TEST_QUERIES = [
    # 基础事实查询
    {"query": "Python是什么时候发布的？", "expected_topics": ["python", "programming"]},
    {"query": "Who created Python?", "expected_topics": ["python", "programming"]},
    
    # 特性和功能查询
    {"query": "FastAPI有哪些主要特点？", "expected_topics": ["web_framework", "fastapi"]},
    {"query": "What are the advantages of FastAPI?", "expected_topics": ["web_framework", "fastapi"]},
    
    # 概念解释查询
    {"query": "什么是机器学习？", "expected_topics": ["ai", "machine_learning"]},
    {"query": "Explain supervised learning", "expected_topics": ["ai", "machine_learning"]},
    
    # 分类和类型查询
    {"query": "有哪些常见的数据结构？", "expected_topics": ["computer_science", "data_structures"]},
    {"query": "What are the types of NoSQL databases?", "expected_topics": ["database", "systems"]},
    
    # 比较查询
    {"query": "数组和链表有什么区别？", "expected_topics": ["computer_science", "data_structures"]},
    {"query": "Compare IaaS, PaaS, and SaaS", "expected_topics": ["cloud", "computing"]},
    
    # 安全相关查询
    {"query": "常见的Web安全威胁有哪些？", "expected_topics": ["security", "web_security"]},
    {"query": "How to prevent SQL injection attacks?", "expected_topics": ["security", "web_security"]},
    
    # 技术实现查询
    {"query": "如何选择合适的算法？", "expected_topics": ["computer_science", "algorithms"]},
    {"query": "What is time complexity?", "expected_topics": ["computer_science", "algorithms"]},
    
    # 应用场景查询
    {"query": "云计算适用于什么场景？", "expected_topics": ["cloud", "computing"]},
    {"query": "When should I use a hash table?", "expected_topics": ["computer_science", "data_structures"]},
    
    # 复合查询
    {"query": "Python在机器学习中的应用", "expected_topics": ["python", "ai"]},
    {"query": "Database security best practices", "expected_topics": ["database", "security"]},
    
    # 开放性查询
    {"query": "如何成为一名优秀的程序员？", "expected_topics": ["programming"]},
    {"query": "Future trends in cloud computing", "expected_topics": ["cloud", "computing"]}
]


async def setup_knowledge_base():
    """设置知识库并添加测试文档"""
    config = Config()
    config.storage.provider = "memory"
    config.embedding.provider = "sentence_transformers"
    config.generation.provider = "ollama"
    
    kb = KnowledgeBase(config)
    await kb.initialize()
    
    print("📚 添加测试文档到知识库...")
    result = await kb.add_documents(TEST_DOCUMENTS)
    
    if result.success:
        print(f"✅ 成功添加 {len(TEST_DOCUMENTS)} 个文档，生成 {result.chunks_created} 个chunks")
    else:
        print(f"❌ 文档添加失败: {result.error_message}")
        return None
    
    return kb


async def run_rag_queries(kb: KnowledgeBase):
    """运行RAG查询测试"""
    print(f"\n🔍 开始运行 {len(TEST_QUERIES)} 个RAG查询测试...\n")
    
    results = []
    total_time = 0
    
    for i, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        expected_topics = test_case["expected_topics"]
        
        print(f"[{i:2d}/20] 查询: {query}")
        
        start_time = time.time()
        try:
            # 执行查询
            result = await kb.query(query, top_k=3)
            query_time = time.time() - start_time
            total_time += query_time
            
            # 分析结果
            source_count = len(result.sources)
            confidence = result.confidence
            
            # 检查是否找到相关内容
            has_relevant_content = source_count > 0 and confidence > 0.3
            
            # 简化答案显示
            answer_preview = result.answer[:100] + "..." if len(result.answer) > 100 else result.answer
            
            print(f"    答案: {answer_preview}")
            print(f"    来源: {source_count} 个chunks, 置信度: {confidence:.2f}, 用时: {query_time:.3f}s")
            
            if has_relevant_content:
                print(f"    ✅ 找到相关内容")
            else:
                print(f"    ⚠️  相关性较低")
            
            results.append({
                "query": query,
                "success": has_relevant_content,
                "source_count": source_count,
                "confidence": confidence,
                "time": query_time,
                "answer_length": len(result.answer)
            })
            
        except Exception as e:
            print(f"    ❌ 查询失败: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e),
                "time": time.time() - start_time
            })
        
        print()  # 空行分隔
    
    return results, total_time


def analyze_results(results, total_time):
    """分析测试结果"""
    print("=" * 60)
    print("📊 RAG查询测试结果分析")
    print("=" * 60)
    
    successful_queries = [r for r in results if r.get("success", False)]
    failed_queries = [r for r in results if not r.get("success", False)]
    
    print(f"总查询数量: {len(results)}")
    print(f"成功查询: {len(successful_queries)} ({len(successful_queries)/len(results)*100:.1f}%)")
    print(f"失败查询: {len(failed_queries)} ({len(failed_queries)/len(results)*100:.1f}%)")
    print(f"总用时: {total_time:.2f}s")
    print(f"平均用时: {total_time/len(results):.3f}s")
    
    if successful_queries:
        avg_confidence = sum(r["confidence"] for r in successful_queries) / len(successful_queries)
        avg_sources = sum(r["source_count"] for r in successful_queries) / len(successful_queries)
        avg_answer_length = sum(r["answer_length"] for r in successful_queries) / len(successful_queries)
        
        print(f"\n成功查询统计:")
        print(f"  平均置信度: {avg_confidence:.2f}")
        print(f"  平均来源数: {avg_sources:.1f}")
        print(f"  平均答案长度: {avg_answer_length:.0f} 字符")
    
    # 显示失败的查询
    if failed_queries:
        print(f"\n失败的查询:")
        for i, result in enumerate(failed_queries, 1):
            query = result["query"]
            error = result.get("error", "置信度过低")
            print(f"  {i}. {query} - {error}")
    
    # 性能分析
    query_times = [r["time"] for r in results]
    fastest = min(query_times)
    slowest = max(query_times)
    
    print(f"\n性能分析:")
    print(f"  最快查询: {fastest:.3f}s")
    print(f"  最慢查询: {slowest:.3f}s")
    print(f"  时间标准差: {(sum((t - total_time/len(results))**2 for t in query_times) / len(query_times))**0.5:.3f}s")


async def test_specific_scenarios():
    """测试特定场景"""
    print("\n🧪 特定场景测试")
    print("-" * 40)
    
    config = Config()
    config.storage.provider = "memory"
    config.generation.provider = "ollama"
    
    async with KnowledgeBase(config) as kb:
        # 添加文档
        await kb.add_documents(TEST_DOCUMENTS[:3])  # 只添加前3个文档
        
        # 测试1: 多语言查询
        print("1. 多语言查询测试")
        queries = [
            "What is Python?",  # 英文查询
            "Python是什么？",   # 中文查询
            "Python programming language"  # 英文关键词
        ]
        
        for query in queries:
            result = await kb.query(query)
            print(f"   查询: {query}")
            print(f"   置信度: {result.confidence:.2f}, 来源: {len(result.sources)}")
        
        # 测试2: 边界情况
        print("\n2. 边界情况测试")
        edge_cases = [
            "",  # 空查询
            "a",  # 单字符
            "非常具体的不存在的技术概念xyz123",  # 不存在的概念
            "Python " * 100  # 重复词汇
        ]
        
        for query in edge_cases:
            try:
                result = await kb.query(query)
                print(f"   查询: '{query[:30]}...' - 成功, 置信度: {result.confidence:.2f}")
            except Exception as e:
                print(f"   查询: '{query[:30]}...' - 失败: {type(e).__name__}")


async def main():
    """主测试函数"""
    print("🚀 RAG查询测试开始")
    print("=" * 60)
    
    try:
        # 设置知识库
        kb = await setup_knowledge_base()
        if not kb:
            return
        
        # 运行RAG查询测试
        results, total_time = await run_rag_queries(kb)
        
        # 分析结果
        analyze_results(results, total_time)
        
        # 关闭知识库
        await kb.close()
        
        # 特定场景测试
        await test_specific_scenarios()
        
        print("\n✅ 所有RAG查询测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())