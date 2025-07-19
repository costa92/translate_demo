#!/usr/bin/env python
"""
SiliconFlow查询示例

本示例演示如何使用SiliconFlow模型进行知识库查询。
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入简化版知识库
from src.knowledge_base import KnowledgeBase


class SiliconFlowQueryDemo:
    """SiliconFlow查询示例类"""
    
    def __init__(self):
        """初始化示例"""
        self.kb = KnowledgeBase()
        
        # 在实际应用中，这些配置会从环境变量或配置文件中读取
        self.api_key = os.environ.get("SILICONFLOW_API_KEY", "your_api_key_here")
        self.model = os.environ.get("SILICONFLOW_MODEL", "siliconflow-7b")
        
        # 高级配置选项
        self.model_config = {
            "temperature": 0.5,           # 控制生成文本的随机性，值越低越确定性
            "top_p": 0.95,                # 控制采样的概率质量，值越低越集中
            "max_tokens": 2048,           # 生成文本的最大长度
            "presence_penalty": 0.1,      # 控制重复惩罚
            "frequency_penalty": 0.1,     # 控制词频惩罚
            "stop_sequences": None,       # 停止生成的序列
            "stream": False,              # 是否流式输出
            "precision": "float16"        # 计算精度：float32, float16, int8
        }
        
        # 检索配置
        self.retrieval_config = {
            "strategy": "semantic",       # 检索策略：semantic, keyword, hybrid
            "top_k": 3,                   # 返回的最大结果数
            "min_score": 0.6,             # 最小相似度分数
            "semantic_weight": 1.0,       # 语义搜索权重
            "keyword_weight": 0.0,        # 关键词搜索权重
            "reranking": False            # 是否进行重排序
        }
        
        # 硬件配置
        self.hardware_config = {
            "device": "cuda",             # 计算设备：cuda, cpu
            "num_gpus": 1,                # 使用的GPU数量
            "gpu_memory_limit": None,     # GPU内存限制（GB）
            "batch_size": 1               # 批处理大小
        }
    
    def add_sample_documents(self):
        """添加示例文档到知识库"""
        print("正在添加示例文档...")
        
        # 添加关于半导体技术的文档
        semiconductor_doc = """
        # 半导体技术发展

        半导体技术是现代电子设备的基础，其发展经历了多个重要阶段。
        
        ## 摩尔定律
        
        摩尔定律是由英特尔创始人之一戈登·摩尔提出的，它指出集成电路上的晶体管数量大约每两年翻一番。
        这一定律在过去几十年中一直指导着半导体行业的发展，但近年来随着物理极限的接近，其发展速度有所放缓。
        
        ## 先进制程
        
        半导体制程是指制造芯片时的最小特征尺寸，通常以纳米(nm)为单位。目前最先进的量产制程包括：
        
        1. 台积电的3nm制程
        2. 三星的4nm制程
        3. 英特尔的Intel 7制程（相当于其他厂商的7nm）
        
        ## 新型半导体材料
        
        除了传统的硅基半导体，新型半导体材料也在不断发展：
        
        1. 碳化硅(SiC)：适用于高温、高压环境
        2. 氮化镓(GaN)：适用于高频、高效率应用
        3. 石墨烯：具有优异的导电性和热导率
        """
        
        result1 = self.kb.add_document(
            content=semiconductor_doc,
            metadata={
                "title": "半导体技术发展",
                "source": "research",
                "date": datetime.now().isoformat()
            }
        )
        
        print(f"文档已添加，ID: {result1.document_id}")
        print(f"创建了 {len(result1.chunk_ids)} 个文本块")
        
        # 添加关于AI芯片的文档
        ai_chip_doc = """
        # AI芯片技术
        
        AI芯片是专为人工智能工作负载优化的集成电路，具有特殊的架构设计。
        
        ## 主要类型
        
        1. **GPU (图形处理器)**
           - 由NVIDIA、AMD等公司生产
           - 擅长并行计算，适合深度学习训练
           - 例如NVIDIA的A100、H100系列
        
        2. **TPU (张量处理器)**
           - 由Google开发的ASIC
           - 专为TensorFlow框架优化
           - 适合大规模机器学习推理和训练
        
        3. **NPU (神经网络处理器)**
           - 由华为、苹果等公司开发
           - 针对移动设备的AI应用优化
           - 低功耗、高效率
        
        4. **FPGA (现场可编程门阵列)**
           - 可重配置硬件
           - 适合特定AI算法的定制实现
           - 提供灵活性和效率的平衡
        
        ## 性能指标
        
        评估AI芯片性能的主要指标包括：
        
        1. 计算能力：通常以TOPS（每秒万亿次操作）或FLOPS（每秒浮点运算次数）衡量
        2. 内存带宽：影响数据传输速度
        3. 能效比：每瓦特可执行的操作数
        4. 支持的精度：FP32、FP16、INT8等
        """
        
        result2 = self.kb.add_document(
            content=ai_chip_doc,
            metadata={
                "title": "AI芯片技术",
                "source": "technical",
                "date": datetime.now().isoformat()
            }
        )
        
        print(f"文档已添加，ID: {result2.document_id}")
        print(f"创建了 {len(result2.chunk_ids)} 个文本块")
    
    def run_queries(self):
        """执行查询示例"""
        print("\n执行查询...")
        
        # 基本查询
        print("\n=== 基本查询 ===")
        basic_queries = [
            "摩尔定律是什么？它目前面临什么挑战？",
            "目前最先进的半导体制程是什么？",
            "有哪些主要类型的AI芯片？它们各有什么特点？"
        ]
        
        results = []
        
        for i, query in enumerate(basic_queries):
            print(f"\n基本查询 {i+1}: {query}")
            result = self.kb.query(query)
            
            print(f"回答: {result.answer}")
            print("来源:")
            for j, chunk in enumerate(result.chunks[:2]):  # 只显示前两个来源
                print(f"  {j+1}. {chunk.text[:100]}...")
            
            # 保存结果
            results.append({
                "query": query,
                "answer": result.answer,
                "sources": [chunk.text for chunk in result.chunks]
            })
        
        # 高级查询：技术比较
        print("\n=== 技术比较查询 ===")
        comparison_query = "比较碳化硅(SiC)和氮化镓(GaN)这两种半导体材料的特点和应用"
        print(f"查询: {comparison_query}")
        
        # 在实际实现中，这里可能会使用特殊的比较模板
        result = self.kb.query(comparison_query)
        
        print(f"回答: {result.answer}")
        print("来源:")
        for j, chunk in enumerate(result.chunks[:2]):
            print(f"  {j+1}. {chunk.text[:100]}...")
        
        results.append({
            "query": comparison_query,
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        })
        
        # 高级查询：性能分析
        print("\n=== 性能分析查询 ===")
        performance_query = "分析不同AI芯片架构的性能指标和优缺点"
        print(f"查询: {performance_query}")
        print("过滤条件: source=technical")
        
        # 在实际实现中，这里会传递元数据过滤条件
        result = self.kb.query(performance_query, metadata_filter={"source": "technical"})
        
        print(f"回答: {result.answer}")
        print("来源:")
        for j, chunk in enumerate(result.chunks[:2]):
            print(f"  {j+1}. {chunk.text[:100]}...")
        
        results.append({
            "query": performance_query,
            "filter": {"source": "technical"},
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        })
        
        # 高级查询：技术预测
        print("\n=== 技术预测查询 ===")
        forecast_query = "根据当前半导体技术发展趋势，预测未来5年可能的突破点"
        print(f"查询: {forecast_query}")
        
        # 在实际实现中，这里可能会使用特殊的预测模板
        result = self.kb.query(forecast_query)
        
        print(f"回答: {result.answer}")
        print("来源:")
        for j, chunk in enumerate(result.chunks[:2]):
            print(f"  {j+1}. {chunk.text[:100]}...")
        
        results.append({
            "query": forecast_query,
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        })
        
        # 将结果保存到文件
        print("\n保存查询结果到 siliconflow_query_results.json...")
        with open("siliconflow_query_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def show_model_info(self):
        """显示模型信息"""
        print("\n=== SiliconFlow模型信息 ===")
        print(f"当前模型: {self.model}")
        print("\n可用模型:")
        print("- siliconflow-7b: 7B参数通用模型")
        print("- siliconflow-13b: 13B参数增强模型")
        print("- siliconflow-tech: 技术领域专用模型")
        print("- siliconflow-code: 代码生成专用模型")
        
        print("\n模型配置:")
        for key, value in self.model_config.items():
            print(f"- {key}: {value}")
        
        print("\n检索配置:")
        for key, value in self.retrieval_config.items():
            print(f"- {key}: {value}")
            
        print("\n硬件配置:")
        for key, value in self.hardware_config.items():
            print(f"- {key}: {value}")
    
    def benchmark(self):
        """运行性能基准测试"""
        print("\n=== 性能基准测试 ===")
        print("测试环境:")
        print(f"- 模型: {self.model}")
        print(f"- 设备: {self.hardware_config['device']}")
        print(f"- 精度: {self.model_config['precision']}")
        
        import time
        
        # 测试查询延迟
        print("\n测试查询延迟...")
        test_query = "半导体技术的未来发展趋势是什么？"
        
        start_time = time.time()
        self.kb.query(test_query)
        end_time = time.time()
        
        print(f"查询延迟: {(end_time - start_time):.2f}秒")
        
        # 测试批量查询吞吐量
        print("\n测试批量查询吞吐量...")
        test_queries = [
            "什么是摩尔定律？",
            "什么是先进制程？",
            "什么是AI芯片？",
            "什么是GPU？",
            "什么是TPU？"
        ]
        
        start_time = time.time()
        for query in test_queries:
            self.kb.query(query)
        end_time = time.time()
        
        total_time = end_time - start_time
        qps = len(test_queries) / total_time
        
        print(f"总时间: {total_time:.2f}秒")
        print(f"查询吞吐量: {qps:.2f}查询/秒")
    
    def run(self):
        """运行完整示例"""
        print("====================================================================")
        print("                    SiliconFlow查询示例")
        print("====================================================================\n")
        
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="SiliconFlow查询示例")
        parser.add_argument("--model", type=str, help="指定SiliconFlow模型")
        parser.add_argument("--api-key", type=str, help="指定API密钥")
        parser.add_argument("--device", type=str, choices=["cuda", "cpu"], help="指定计算设备")
        parser.add_argument("--precision", type=str, choices=["float32", "float16", "int8"], help="指定计算精度")
        parser.add_argument("--info", action="store_true", help="显示模型信息")
        parser.add_argument("--benchmark", action="store_true", help="运行性能基准测试")
        parser.add_argument("--skip-docs", action="store_true", help="跳过添加示例文档")
        args = parser.parse_args()
        
        # 应用命令行参数
        if args.model:
            self.model = args.model
            print(f"使用指定模型: {self.model}")
        
        if args.api_key:
            self.api_key = args.api_key
            print("使用指定API密钥")
            
        if args.device:
            self.hardware_config["device"] = args.device
            print(f"使用指定设备: {args.device}")
            
        if args.precision:
            self.model_config["precision"] = args.precision
            print(f"使用指定精度: {args.precision}")
        
        # 显示模型信息
        if args.info:
            self.show_model_info()
            return
            
        # 运行性能基准测试
        if args.benchmark:
            if not args.skip_docs:
                self.add_sample_documents()
            self.benchmark()
            return
        
        # 添加示例文档
        if not args.skip_docs:
            self.add_sample_documents()
        else:
            print("跳过添加示例文档")
        
        # 执行查询
        self.run_queries()
        
        print("\n示例运行完成！")
        print("在实际应用中，您需要：")
        print("1. 设置SILICONFLOW_API_KEY环境变量")
        print("2. 配置适当的模型参数")
        print("3. 根据需要调整查询参数")
        print("\n命令行选项:")
        print("--model MODEL      指定SiliconFlow模型")
        print("--api-key KEY      指定API密钥")
        print("--device DEVICE    指定计算设备 (cuda, cpu)")
        print("--precision PREC   指定计算精度 (float32, float16, int8)")
        print("--info             显示模型信息")
        print("--benchmark        运行性能基准测试")
        print("--skip-docs        跳过添加示例文档")


if __name__ == "__main__":
    demo = SiliconFlowQueryDemo()
    demo.run()