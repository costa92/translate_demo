#!/usr/bin/env python
"""
DeepSeek查询示例

本示例演示如何使用DeepSeek模型进行知识库查询。
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

# 导入简化版知识库
from knowledge_base import KnowledgeBase


class DeepSeekResponse:
    """模拟DeepSeek API响应"""
    
    def __init__(self, text: str, usage: Dict[str, int], model: str):
        self.text = text
        self.usage = usage
        self.model = model


def call_deepseek_api(
    prompt: str, 
    api_key: str, 
    model: str, 
    config: Dict[str, Any]
) -> DeepSeekResponse:
    """
    模拟调用DeepSeek API，但基于提供的上下文生成回答
    
    在实际应用中，这个函数会使用requests或类似库调用真实的DeepSeek API
    """
    # 模拟API调用延迟
    time.sleep(random.uniform(0.5, 1.5))
    
    # 从提示词中提取上下文和问题
    context_start = prompt.find("参考文档:")
    context_end = prompt.find("问题:")
    question_start = prompt.find("问题:") + 3
    question_end = prompt.find("请提供详细")
    
    if context_start != -1 and context_end != -1 and question_start != -1:
        context = prompt[context_start + 5:context_end].strip()
        question = prompt[question_start:question_end].strip() if question_end != -1 else prompt[question_start:].strip()
    else:
        context = ""
        question = prompt
    
    # 基于上下文生成回答
    text = "根据提供的参考文档，我无法回答这个问题。"
    
    # 如果上下文不为空，尝试从中提取相关信息
    if context:
        # 检查问题中的关键词
        if "DeepSeek Chat" in question and ("特点" in question or "什么" in question):
            if "DeepSeek Chat" in context and "特点" in context:
                # 提取关于DeepSeek Chat的信息
                chat_info = ""
                for line in context.split("\n"):
                    if "DeepSeek Chat" in line or (chat_info and line.strip().startswith(("1.", "2.", "3.", "4.", "5."))):
                        chat_info += line + "\n"
                
                if chat_info:
                    text = "DeepSeek Chat是DeepSeek AI推出的对话模型，具有以下特点：" + chat_info
        
        elif ("评估" in question and "语言模型" in question) or "评估指标" in question or ("评估" in question and "维度" in question) or "考虑哪些维度" in question:
            # 打印调试信息
            print(f"检测到评估相关查询: {question}")
            print(f"上下文长度: {len(context)}")
            print(f"上下文前100个字符: {context[:100]}")
            
            # 检查上下文中是否包含评估相关信息
            if "评估" in context or "AI语言模型评估指标" in context or "通用能力评估" in context:
                print("找到评估相关信息")
                # 提取关于评估的信息
                eval_info = ""
                for line in context.split("\n"):
                    if "评估" in line or "通用能力" in line or "特定任务" in line or "安全性" in line or "语言理解能力" in line or "知识广度" in line or "推理能力" in line or "创造力" in line:
                        eval_info += line + "\n"
                        print(f"提取行: {line}")
                
                if eval_info:
                    text = "评估大型语言模型的性能需要考虑多个维度：\n" + eval_info
                    print(f"生成回答: {text[:100]}...")
        
        elif "DeepSeek Coder" in question and ("编程任务" in question or "适合" in question):
            if "DeepSeek Coder" in context:
                # 提取关于DeepSeek Coder的信息
                coder_info = ""
                for line in context.split("\n"):
                    if "DeepSeek Coder" in line or (coder_info and line.strip().startswith(("1.", "2.", "3.", "4.", "5."))):
                        coder_info += line + "\n"
                
                if coder_info:
                    text = "DeepSeek Coder适合多种编程任务：" + coder_info
        
        elif "编程语言" in question:
            if "编程语言" in context:
                # 提取关于编程语言的信息
                lang_info = ""
                for line in context.split("\n"):
                    if "编程语言" in line:
                        lang_info += line + "\n"
                
                if lang_info:
                    text = "DeepSeek Coder支持多种编程语言：" + lang_info
        
        # 如果没有匹配到特定模式，尝试基于上下文生成通用回答
        if text == "根据提供的参考文档，我无法回答这个问题。" and context:
            # 简单地返回与问题最相关的上下文部分
            question_words = set(question.lower().replace("？", "").split())
            
            relevant_lines = []
            for line in context.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                # 计算相关性分数
                relevance = sum(1 for word in question_words if word in line.lower())
                if relevance > 0:
                    relevant_lines.append((relevance, line))
            
            # 按相关性排序
            relevant_lines.sort(reverse=True)
            
            if relevant_lines:
                text = "根据参考文档，"
                for _, line in relevant_lines[:3]:  # 取前3个最相关的行
                    text += line + " "
    
    # 模拟token使用情况
    prompt_tokens = len(prompt) // 4
    completion_tokens = len(text) // 4
    total_tokens = prompt_tokens + completion_tokens
    
    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }
    
    return DeepSeekResponse(text=text, usage=usage, model=model)


class DeepSeekQueryDemo:
    """DeepSeek查询示例类"""
    
    def __init__(self):
        """初始化示例"""
        self.kb = KnowledgeBase()
        
        # 在实际应用中，这些配置会从环境变量或配置文件中读取
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "your_api_key_here")
        self.model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

        # print(self.api_key,   self.model )
        
        # 高级配置选项
        self.model_config = {
            "temperature": 0.7,           # 控制生成文本的随机性，值越低越确定性
            "top_p": 0.9,                 # 控制采样的概率质量，值越低越集中
            "max_tokens": 1024,           # 生成文本的最大长度
            "presence_penalty": 0.0,      # 控制重复惩罚
            "frequency_penalty": 0.0,     # 控制词频惩罚
            "stop_sequences": None,       # 停止生成的序列
            "stream": False               # 是否流式输出
        }
        
        # 检索配置
        self.retrieval_config = {
            "strategy": "hybrid",         # 检索策略：semantic, keyword, hybrid
            "top_k": 5,                   # 返回的最大结果数
            "min_score": 0.5,             # 最小相似度分数
            "semantic_weight": 0.7,       # 语义搜索权重
            "keyword_weight": 0.3,        # 关键词搜索权重
            "reranking": True             # 是否进行重排序
        }
    
    def add_sample_documents(self):
        """添加示例文档到知识库"""
        print("正在添加示例文档...")
        
        # 添加关于DeepSeek的文档
        deepseek_doc = """
        # DeepSeek AI

        DeepSeek AI是一家专注于大型语言模型研发的人工智能公司，致力于构建先进的AI模型和应用。
        
        ## DeepSeek Chat
        
        DeepSeek Chat是DeepSeek AI推出的对话模型，具有以下特点：
        
        1. 强大的多语言能力，尤其是中文和英文
        2. 出色的代码生成和理解能力
        3. 长上下文支持，可处理更长的对话历史
        4. 知识更新至2023年
        5. 提供多种规格的模型，从7B到67B参数
        
        ## DeepSeek Coder
        
        DeepSeek Coder是专为代码生成优化的模型：
        
        1. 支持多种编程语言，包括Python、Java、C++、JavaScript等
        2. 能够理解复杂的编程任务和需求
        3. 提供详细的代码解释和注释
        4. 可以辅助调试和优化代码
        5. 支持代码补全和重构
        """
        
        result1 = self.kb.add_document(
            content=deepseek_doc,
            metadata={
                "title": "DeepSeek AI介绍",
                "source": "documentation",
                "date": datetime.now().isoformat()
            }
        )
        
        print(f"文档已添加，ID: {result1.document_id}")
        print(f"创建了 {len(result1.chunk_ids)} 个文本块")
        
        # 添加关于AI模型评估的文档
        evaluation_doc = """
        # AI语言模型评估指标
        
        评估大型语言模型的性能需要考虑多个维度：
        
        ## 通用能力评估
        
        1. **语言理解能力**：模型对自然语言的理解深度和准确性
        2. **知识广度**：模型包含的知识范围和准确性
        3. **推理能力**：模型进行逻辑推理和解决问题的能力
        4. **创造力**：模型生成新颖且有价值内容的能力
        
        ## 特定任务评估
        
        1. **代码生成**：生成功能正确、高效代码的能力
        2. **数学问题**：解决数学问题的准确性
        3. **多语言支持**：处理不同语言的能力
        4. **上下文理解**：在长对话中保持连贯性的能力
        
        ## 安全性评估
        
        1. **拒绝有害请求**：识别并拒绝生成有害内容的能力
        2. **减少偏见**：避免在输出中表现社会偏见的能力
        3. **事实准确性**：提供准确信息并避免虚构内容的能力
        """
        
        result2 = self.kb.add_document(
            content=evaluation_doc,
            metadata={
                "title": "AI语言模型评估指标",
                "source": "research",
                "date": datetime.now().isoformat()
            }
        )
        
        print(f"文档已添加，ID: {result2.document_id}")
        print(f"创建了 {len(result2.chunk_ids)} 个文本块")
        
        print(f"文档已添加，ID: {result2.document_id}")
        print(f"创建了 {len(result2.chunk_ids)} 个文本块")
    
    def generate_chinese_answer(self, query, chunks):
        """生成中文回答
        
        使用DeepSeek API（或模拟API）基于检索到的文档块生成回答。
        """
        # 提取检索到的文本内容
        context = ""
        print(f"\n为查询 '{query}' 找到 {len(chunks)} 个相关文档块:")
        for i, chunk in enumerate(chunks):
            print(f"文档块 {i+1}:")
            print(f"- 元数据: {chunk.metadata}")
            print(f"- 内容: {chunk.text[:100]}...")
            context += chunk.text + "\n\n"
        
        # 构建提示词
        prompt = f"""
基于以下参考文档，用中文回答问题。如果参考文档中没有相关信息，请回答"根据提供的参考文档，我无法回答这个问题"。

参考文档:
{context}

问题: {query}

请提供详细、准确、有条理的中文回答:
"""
        
        # 调用DeepSeek API（或模拟API）
        try:
            print(f"正在调用DeepSeek API (模型: {self.model})...")
            start_time = time.time()
            
            response = call_deepseek_api(prompt, self.api_key, self.model, self.model_config)
            
            end_time = time.time()
            print(f"API调用完成，耗时: {end_time - start_time:.2f}秒")
            print(f"Token使用情况: 提示词 {response.usage['prompt_tokens']}，回答 {response.usage['completion_tokens']}，总计 {response.usage['total_tokens']}")
            
            return response.text
            
        except Exception as e:
            print(f"API调用失败: {e}")
            print("使用备用方法生成回答...")
            
            # 检查是否有相关内容
            if not chunks:
                return "根据提供的参考文档，我无法回答这个问题。"
            
            # 提取与查询相关的内容
            relevant_text = ""
            for chunk in chunks:
                # 简单的相关性判断
                query_words = set(query.lower().replace("？", "").split())
                chunk_text = chunk.text.lower()
                
                # 计算查询词在文档中出现的次数
                relevance = sum(1 for word in query_words if word in chunk_text)
                
                if relevance > 0:
                    relevant_text += chunk.text + "\n"
            
            if relevant_text:
                # 根据相关文本生成回答
                return f"根据参考文档，{relevant_text[:200]}..."
            else:
                return "根据提供的参考文档，我无法回答这个问题。"
    
    def run_queries(self):
        """执行查询示例"""
        print("\n执行查询...")
        
        # 基本查询
        print("\n=== 基本查询 ===")
        basic_queries = [
            "DeepSeek Chat有哪些主要特点？",
            "如何评估大型语言模型的性能？",
            "DeepSeek Coder适合哪些编程任务？"
        ]
        
        results = []
        
        for i, query in enumerate(basic_queries):
            print(f"\n基本查询 {i+1}: {query}")
            
            # 获取原始查询结果
            result = self.kb.query(query)
            
            # 生成中文回答
            chinese_answer = self.generate_chinese_answer(query, result.chunks)
            
            # 替换回答为中文
            result.answer = chinese_answer
            
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
        
        # 高级查询：使用元数据过滤
        print("\n=== 带元数据过滤的查询 ===")
        metadata_query = "评估大型语言模型的性能需要考虑哪些维度？"
        print(f"查询: {metadata_query}")
        print("过滤条件: source=research")
        
        # 在实际实现中，这里会传递元数据过滤条件
        result = self.kb.query(metadata_query, metadata_filter={"source": "research"})
        
        # 如果没有找到结果，尝试不使用元数据过滤
        if not result.chunks:
            print("使用元数据过滤没有找到结果，尝试不使用过滤...")
            result = self.kb.query(metadata_query)
        
        # 生成中文回答
        chinese_answer = self.generate_chinese_answer(metadata_query, result.chunks)
        result.answer = chinese_answer
        
        print(f"回答: {result.answer}")
        print("来源:")
        for j, chunk in enumerate(result.chunks[:2]):
            print(f"  {j+1}. {chunk.text[:100]}...")
        
        results.append({
            "query": metadata_query,
            "filter": {"source": "research"},
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        })
        
        # 高级查询：多轮对话
        print("\n=== 多轮对话查询 ===")
        conversation = [
            {"role": "user", "content": "DeepSeek Chat是什么？"},
            {"role": "assistant", "content": "DeepSeek Chat是DeepSeek AI推出的对话模型，具有强大的多语言能力、出色的代码生成和理解能力、长上下文支持等特点。"},
            {"role": "user", "content": "它支持哪些编程语言？"}
        ]
        
        print("多轮对话:")
        for msg in conversation:
            print(f"- {msg['role']}: {msg['content']}")
        
        # 在实际实现中，这里会处理多轮对话
        # 构建增强查询，将上下文信息添加到查询中
        enhanced_query = f"DeepSeek Chat支持哪些编程语言？"  # 将"它"替换为上下文中的实体
        print(f"增强查询: {enhanced_query}")
        
        result = self.kb.query(enhanced_query)
        
        # 生成中文回答
        chinese_answer = self.generate_chinese_answer(conversation[-1]["content"], result.chunks)
        result.answer = chinese_answer
        
        print(f"回答: {result.answer}")
        print("来源:")
        for j, chunk in enumerate(result.chunks[:2]):
            print(f"  {j+1}. {chunk.text[:100]}...")
        
        results.append({
            "conversation": conversation,
            "answer": result.answer,
            "sources": [chunk.text for chunk in result.chunks]
        })
        
        # 将结果保存到文件
        print("\n保存查询结果到 deepseek_query_results.json...")
        with open("deepseek_query_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def show_model_info(self):
        """显示模型信息"""
        print("\n=== DeepSeek模型信息 ===")
        print(f"当前模型: {self.model}")
        print("\n可用模型:")
        print("- deepseek-chat: 通用对话模型")
        print("- deepseek-coder: 代码生成优化模型")
        print("- deepseek-chat-7b: 7B参数版本")
        print("- deepseek-chat-67b: 67B参数版本")
        
        print("\n模型配置:")
        for key, value in self.model_config.items():
            print(f"- {key}: {value}")
        
        print("\n检索配置:")
        for key, value in self.retrieval_config.items():
            print(f"- {key}: {value}")
    
    def run(self):
        """运行完整示例"""
        print("====================================================================")
        print("                    DeepSeek查询示例")
        print("====================================================================\n")
        
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="DeepSeek查询示例")
        parser.add_argument("--model", type=str, help="指定DeepSeek模型")
        parser.add_argument("--api-key", type=str, help="指定API密钥")
        parser.add_argument("--info", action="store_true", help="显示模型信息")
        parser.add_argument("--skip-docs", action="store_true", help="跳过添加示例文档")
        parser.add_argument("--use-real-api", action="store_true", help="使用真实API而不是模拟API")
        parser.add_argument("--temperature", type=float, help="设置温度参数")
        parser.add_argument("--top-p", type=float, help="设置top_p参数")
        parser.add_argument("--max-tokens", type=int, help="设置最大生成token数")
        args = parser.parse_args()
        
        # 应用命令行参数
        if args.model:
            self.model = args.model
            print(f"使用指定模型: {self.model}")
        
        if args.api_key:
            self.api_key = args.api_key
            print("使用指定API密钥")
            
        if args.temperature is not None:
            self.model_config["temperature"] = args.temperature
            print(f"设置温度参数: {args.temperature}")
            
        if args.top_p is not None:
            self.model_config["top_p"] = args.top_p
            print(f"设置top_p参数: {args.top_p}")
            
        if args.max_tokens is not None:
            self.model_config["max_tokens"] = args.max_tokens
            print(f"设置最大生成token数: {args.max_tokens}")
        
        # 显示模型信息
        if args.info:
            self.show_model_info()
            return
            
        # 检查是否使用真实API
        if args.use_real_api:
            print("警告: 当前版本不支持真实API调用，将使用模拟API")
            print("要使用真实API，请修改代码中的call_deepseek_api函数")
            
            # 检查API密钥
            if self.api_key == "your_api_key_here":
                print("错误: 使用真实API需要提供有效的API密钥")
                print("请使用--api-key参数或设置DEEPSEEK_API_KEY环境变量")
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
        print("1. 设置DEEPSEEK_API_KEY环境变量")
        print("2. 配置适当的模型参数")
        print("3. 根据需要调整查询参数")
        print("\n命令行选项:")
        print("--model MODEL      指定DeepSeek模型")
        print("--api-key KEY      指定API密钥")
        print("--info             显示模型信息")
        print("--skip-docs        跳过添加示例文档")
        print("--use-real-api     使用真实API而不是模拟API")
        print("--temperature VAL  设置温度参数")
        print("--top-p VAL        设置top_p参数")
        print("--max-tokens NUM   设置最大生成token数")

     



if __name__ == "__main__":
    demo = DeepSeekQueryDemo()
    demo.run()