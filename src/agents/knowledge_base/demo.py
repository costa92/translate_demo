#!/usr/bin/env python3
"""
快速演示脚本：展示知识库多智能体系统的基本功能
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from orchestrator_agent import OrchestratorAgent

def main():
    print("🚀 知识库多智能体系统演示")
    print("=" * 50)
    
    # 初始化系统
    print("\n1️⃣ 初始化系统...")
    orchestrator = OrchestratorAgent(storage_provider='memory')
    
    # 添加示例知识
    print("\n2️⃣ 添加示例知识...")
    sample_knowledge = {
        "sources": [
            {
                "type": "text",
                "location": "人工智能（AI）是计算机科学的一个分支，它致力于创建能够模拟、扩展和增强人类智能的系统。AI系统可以执行通常需要人类智能的任务，如视觉识别、语音理解、决策制定和语言翻译。",
                "metadata": {"topic": "AI", "category": "technology"}
            },
            {
                "type": "text",
                "location": "机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过大量数据进行训练，发现模式和规律，从而对新数据做出预测或决策。",
                "metadata": {"topic": "ML", "category": "technology"}
            },
            {
                "type": "text",
                "location": "自然语言处理（NLP）是人工智能的一个分支，专注于让计算机理解、解释和生成人类语言。NLP技术广泛应用于聊天机器人、机器翻译、文本摘要和情感分析等领域。",
                "metadata": {"topic": "NLP", "category": "technology"}
            }
        ]
    }
    
    result = orchestrator.receive_request("demo", "add_knowledge", sample_knowledge)
    if result.get("status") == "success":
        print(f"✅ 成功添加了 {result.get('chunks_count')} 个知识块")
    else:
        print(f"❌ 添加失败: {result.get('message')}")
        return
    
    # 交互式问答
    print("\n3️⃣ 交互式问答演示")
    print("您可以询问关于AI、机器学习、NLP的问题")
    print("输入 'quit' 退出")
    
    while True:
        try:
            query = input("\n🤔 请输入您的问题: ").strip()
            if query.lower() in ['quit', 'exit', '退出']:
                break
            
            if not query:
                print("请输入有效的问题")
                continue
            
            print(f"\n🔍 正在查询: {query}")
            result = orchestrator.receive_request("demo", "query", {"query": query})
            
            if result.get("status") == "success":
                print(f"\n💡 答案:")
                print(result.get("answer", ""))
                print(f"\n📚 找到 {result.get('sources_count', 0)} 个相关知识源")
            else:
                print(f"❌ 查询失败: {result.get('message')}")
                
        except KeyboardInterrupt:
            print("\n\n👋 感谢使用！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
    
    print("\n🎉 演示结束")

if __name__ == "__main__":
    main()