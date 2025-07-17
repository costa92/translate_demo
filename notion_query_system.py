#!/usr/bin/env python3
"""
Notion Query System
从环境变量获取 Notion 凭据，查询数据库内容并回答问题。
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, List, Optional
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotionQuerySystem:
    """Notion 查询系统，用于从 Notion 数据库获取内容并回答问题。"""
    
    def __init__(self):
        """初始化 Notion 查询系统。"""
        # 从环境变量获取凭据
        self.api_key = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        
        if not self.api_key:
            raise ValueError("未找到 NOTION_API_KEY 或 NOTION_KEY 环境变量")
        if not self.database_id:
            raise ValueError("未找到 NOTION_DATABASE_ID 环境变量")
        
        self.base_url = "https://api.notion.com/v1"
        self.client = None
        
        # 内存缓存
        self._content_cache = []
        self._cache_loaded = False
        self._last_cache_time = None
        
        logger.info(f"Notion 查询系统初始化完成")
        logger.info(f"数据库 ID: {self.database_id}")
    
    async def __aenter__(self):
        """异步上下文管理器入口。"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出。"""
        if self.client:
            await self.client.aclose()
    
    async def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息。"""
        try:
            response = await self.client.get(f"/databases/{self.database_id}")
            
            if response.status_code != 200:
                raise Exception(f"无法访问数据库: {response.status_code} - {response.text}")
            
            db_info = response.json()
            return {
                "title": self._extract_title(db_info.get("title", [])),
                "properties": list(db_info.get("properties", {}).keys()),
                "created_time": db_info.get("created_time"),
                "last_edited_time": db_info.get("last_edited_time"),
                "url": db_info.get("url")
            }
            
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            raise
    
    async def search_content(self, query: str = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        搜索数据库内容。
        
        Args:
            query: 搜索查询（可选）
            filters: 过滤条件（可选）
        
        Returns:
            搜索结果列表
        """
        try:
            # 构建查询参数
            query_data = {
                "page_size": 100
            }
            
            # 添加过滤条件
            if filters:
                query_data["filter"] = filters
            
            # 添加搜索查询
            if query:
                # 注意：Notion API 的搜索功能有限，这里使用基本的文本过滤
                if "filter" not in query_data:
                    query_data["filter"] = {}
                
                # 动态构建搜索条件，基于实际的数据库属性
                search_conditions = []
                
                # 获取数据库信息以了解可用属性
                try:
                    db_info = await self.get_database_info()
                    properties = db_info.get("properties", [])
                    
                    for prop_name in properties:
                        # 为不同类型的属性添加搜索条件
                        if prop_name.lower() in ["name", "title", "chunk id"]:
                            search_conditions.append({
                                "property": prop_name,
                                "title": {
                                    "contains": query
                                }
                            })
                        elif prop_name.lower() in ["text", "content", "description"]:
                            search_conditions.append({
                                "property": prop_name,
                                "rich_text": {
                                    "contains": query
                                }
                            })
                    
                    if search_conditions:
                        if len(search_conditions) == 1:
                            query_data["filter"] = search_conditions[0]
                        else:
                            query_data["filter"] = {"or": search_conditions}
                    
                except Exception as e:
                    logger.warning(f"无法获取数据库属性信息，使用默认搜索: {e}")
                    # 回退到基本搜索
                    search_conditions = [
                        {
                            "property": "Name",
                            "title": {
                                "contains": query
                            }
                        }
                    ]
                    query_data["filter"] = search_conditions[0]
            
            all_results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                if start_cursor:
                    query_data["start_cursor"] = start_cursor
                
                response = await self.client.post(
                    f"/databases/{self.database_id}/query",
                    json=query_data
                )
                
                if response.status_code != 200:
                    raise Exception(f"查询失败: {response.status_code} - {response.text}")
                
                data = response.json()
                results = data.get("results", [])
                
                # 处理结果
                for page in results:
                    processed_page = self._process_page(page)
                    if processed_page:
                        all_results.append(processed_page)
                
                # 检查是否有更多页面
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
            
            logger.info(f"找到 {len(all_results)} 条记录")
            return all_results
            
        except Exception as e:
            logger.error(f"搜索内容失败: {e}")
            raise
    
    async def load_all_content_to_cache(self) -> None:
        """一次性加载所有内容到内存缓存。"""
        if self._cache_loaded:
            logger.info("内容已缓存，跳过重新加载")
            return
        
        logger.info("🔄 开始加载所有 Notion 内容到缓存...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 获取所有页面基本信息
            pages = await self.search_content()
            logger.info(f"找到 {len(pages)} 个页面，开始获取内容...")
            
            # 批量获取页面内容
            for i, page in enumerate(pages, 1):
                page_id = page.get("page_id")
                if page_id:
                    logger.info(f"获取页面内容 {i}/{len(pages)}: {page.get('properties', {}).get('Name', 'Unknown')}")
                    content = await self.get_page_content(page_id)
                    page["content"] = content
                    page["full_text"] = self._create_searchable_text(page)  # 创建可搜索的文本
            
            # 保存到缓存
            self._content_cache = pages
            self._cache_loaded = True
            self._last_cache_time = asyncio.get_event_loop().time()
            
            load_time = self._last_cache_time - start_time
            logger.info(f"✅ 缓存加载完成！共 {len(pages)} 个页面，耗时 {load_time:.2f} 秒")
            
        except Exception as e:
            logger.error(f"❌ 缓存加载失败: {e}")
            raise
    
    def _create_searchable_text(self, page: Dict[str, Any]) -> str:
        """创建页面的可搜索文本，包含标题和内容。"""
        text_parts = []
        
        # 添加页面标题
        props = page.get("properties", {})
        title = props.get("Name", props.get("Title", ""))
        if title:
            text_parts.append(title)
        
        # 添加页面内容
        content = page.get("content", "")
        if content:
            text_parts.append(content)
        
        # 添加其他属性
        for key, value in props.items():
            if key not in ["Name", "Title"] and value:
                text_parts.append(str(value))
        
        return "\n".join(text_parts).lower()  # 转换为小写便于搜索
    
    async def get_all_content(self) -> List[Dict[str, Any]]:
        """获取数据库中的所有内容，优先使用缓存。"""
        if not self._cache_loaded:
            await self.load_all_content_to_cache()
        
        return self._content_cache.copy()  # 返回缓存的副本
    
    def search_in_cache(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """在缓存中搜索相关内容，避免重复 API 调用。"""
        if not self._cache_loaded:
            return []
        
        query_lower = query.lower()
        results = []
        
        for page in self._content_cache:
            score = 0
            matched_fields = []
            
            # 搜索可搜索文本
            full_text = page.get("full_text", "")
            if query_lower in full_text:
                # 计算匹配次数作为相关性分数
                score += full_text.count(query_lower)
                matched_fields.append("content")
            
            # 搜索标题（给予更高权重）
            props = page.get("properties", {})
            title = props.get("Name", "").lower()
            if query_lower in title:
                score += 3  # 标题匹配给予更高分数
                matched_fields.append("title")
            
            if score > 0:
                results.append({
                    "page": page,
                    "score": score,
                    "matched_fields": matched_fields
                })
        
        # 按相关性排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回页面数据
        return [result["page"] for result in results[:top_k]]
    
    async def answer_question(self, question: str) -> Dict[str, Any]:
        """
        基于数据库内容回答问题，优先使用缓存搜索。
        
        Args:
            question: 用户问题
        
        Returns:
            包含答案和相关信息的字典
        """
        try:
            logger.info(f"处理问题: {question}")
            
            # 确保缓存已加载
            if not self._cache_loaded:
                await self.load_all_content_to_cache()
            
            # 在缓存中搜索相关内容
            relevant_content = self.search_in_cache(question, top_k=5)
            
            if not relevant_content:
                # 如果没有找到相关内容，使用所有内容
                logger.info("未找到直接相关内容，使用所有缓存内容...")
                relevant_content = self._content_cache[:3]  # 限制为前3条
            
            # 生成答案
            answer = self._generate_answer(question, relevant_content)
            
            return {
                "question": question,
                "answer": answer,
                "sources": relevant_content,
                "source_count": len(relevant_content),
                "timestamp": asyncio.get_event_loop().time(),
                "cache_used": True
            }
            
        except Exception as e:
            logger.error(f"回答问题失败: {e}")
            return {
                "question": question,
                "answer": f"抱歉，处理您的问题时出现错误: {str(e)}",
                "sources": [],
                "source_count": 0,
                "error": str(e),
                "cache_used": False
            }
    
    async def search_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        根据关键词搜索内容。
        
        Args:
            keywords: 关键词列表
        
        Returns:
            搜索结果列表
        """
        all_results = []
        
        for keyword in keywords:
            try:
                results = await self.search_content(query=keyword)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"搜索关键词 '{keyword}' 失败: {e}")
        
        # 去重（基于 page_id）
        seen_ids = set()
        unique_results = []
        for result in all_results:
            page_id = result.get("page_id")
            if page_id and page_id not in seen_ids:
                seen_ids.add(page_id)
                unique_results.append(result)
        
        return unique_results
    
    async def get_content_by_property(self, property_name: str, property_value: str) -> List[Dict[str, Any]]:
        """
        根据属性值获取内容。
        
        Args:
            property_name: 属性名称
            property_value: 属性值
        
        Returns:
            匹配的内容列表
        """
        try:
            filters = {
                "property": property_name,
                "rich_text": {
                    "equals": property_value
                }
            }
            
            return await self.search_content(filters=filters)
            
        except Exception as e:
            logger.error(f"根据属性搜索失败: {e}")
            return []
    
    def _extract_title(self, title_array: List[Dict]) -> str:
        """从 Notion 标题数组中提取文本。"""
        if not title_array:
            return "未知"
        
        return title_array[0].get("plain_text", "未知")
    
    def _extract_text_property(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """从 Notion 属性中提取文本内容。"""
        if not prop:
            return None
        
        # 处理标题属性
        if "title" in prop and prop["title"]:
            return prop["title"][0].get("text", {}).get("content")
        
        # 处理富文本属性
        if "rich_text" in prop and prop["rich_text"]:
            return prop["rich_text"][0].get("text", {}).get("content")
        
        # 处理选择属性
        if "select" in prop and prop["select"]:
            return prop["select"].get("name")
        
        # 处理多选属性
        if "multi_select" in prop and prop["multi_select"]:
            return ", ".join([item.get("name", "") for item in prop["multi_select"]])
        
        # 处理数字属性
        if "number" in prop:
            return str(prop["number"])
        
        # 处理日期属性
        if "date" in prop and prop["date"]:
            return prop["date"].get("start")
        
        # 处理 URL 属性
        if "url" in prop:
            return prop["url"]
        
        return None
    
    def _process_page(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理 Notion 页面数据。"""
        try:
            properties = page.get("properties", {})
            
            # 提取基本信息
            processed = {
                "page_id": page.get("id"),
                "url": page.get("url"),
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time"),
                "properties": {},
                "content": None  # 将在后续获取页面内容
            }
            
            # 处理所有属性
            for prop_name, prop_data in properties.items():
                value = self._extract_text_property(prop_data)
                if value:
                    processed["properties"][prop_name] = value
            
            return processed
            
        except Exception as e:
            logger.error(f"处理页面数据失败: {e}")
            return None
    
    async def get_page_content(self, page_id: str) -> Optional[str]:
        """获取页面的实际内容。"""
        try:
            response = await self.client.get(f"/blocks/{page_id}/children")
            
            if response.status_code != 200:
                logger.error(f"获取页面内容失败: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            blocks = data.get("results", [])
            
            content_parts = []
            for block in blocks:
                block_content = self._extract_block_content(block)
                if block_content:
                    content_parts.append(block_content)
            
            return "\n".join(content_parts) if content_parts else None
            
        except Exception as e:
            logger.error(f"获取页面内容异常: {e}")
            return None
    
    def _extract_block_content(self, block: Dict[str, Any]) -> Optional[str]:
        """从块中提取文本内容。"""
        try:
            block_type = block.get("type")
            
            if not block_type:
                return None
            
            block_data = block.get(block_type, {})
            
            # 处理不同类型的块
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                rich_text = block_data.get("rich_text", [])
                return self._extract_rich_text_content(rich_text)
            
            elif block_type == "code":
                rich_text = block_data.get("rich_text", [])
                language = block_data.get("language", "")
                code_content = self._extract_rich_text_content(rich_text)
                return f"```{language}\n{code_content}\n```" if code_content else None
            
            elif block_type == "quote":
                rich_text = block_data.get("rich_text", [])
                quote_content = self._extract_rich_text_content(rich_text)
                return f"> {quote_content}" if quote_content else None
            
            elif block_type == "callout":
                rich_text = block_data.get("rich_text", [])
                return self._extract_rich_text_content(rich_text)
            
            elif block_type == "toggle":
                rich_text = block_data.get("rich_text", [])
                return self._extract_rich_text_content(rich_text)
            
            return None
            
        except Exception as e:
            logger.warning(f"提取块内容失败: {e}")
            return None
    
    def _extract_rich_text_content(self, rich_text_array: List[Dict[str, Any]]) -> Optional[str]:
        """从富文本数组中提取纯文本内容。"""
        if not rich_text_array:
            return None
        
        text_parts = []
        for text_obj in rich_text_array:
            if "text" in text_obj:
                content = text_obj["text"].get("content", "")
                if content:
                    text_parts.append(content)
        
        return "".join(text_parts) if text_parts else None
    
    def _generate_answer(self, question: str, content: List[Dict[str, Any]]) -> str:
        """
        基于内容生成答案。
        
        Args:
            question: 用户问题
            content: 相关内容列表
        
        Returns:
            生成的答案
        """
        if not content:
            return "抱歉，我在数据库中没有找到相关信息来回答您的问题。"
        
        # 检测问题语言
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in question)
        
        # 构建答案
        if is_chinese:
            answer_parts = ["根据数据库中的信息：\n"]
        else:
            answer_parts = ["Based on the information in the database:\n"]
        
        # 添加相关内容
        for i, item in enumerate(content[:3], 1):  # 限制为前3条
            props = item.get("properties", {})
            page_content = item.get("content", "")
            
            # 获取页面标题
            page_title = props.get("Name", props.get("Title", f"页面 {i}"))
            
            answer_parts.append(f"\n{i}. **{page_title}**")
            
            # 如果有页面内容，显示内容
            if page_content:
                # 限制内容长度，避免过长
                if len(page_content) > 500:
                    content_preview = page_content[:500] + "..."
                else:
                    content_preview = page_content
                answer_parts.append(f"\n   内容: {content_preview}")
            else:
                # 如果没有页面内容，显示属性信息
                relevant_props = []
                for key, value in props.items():
                    if key not in ["Created", "Start Index", "End Index"] and value:
                        relevant_props.append(f"{key}: {value}")
                
                if relevant_props:
                    answer_parts.append(f"\n   {'; '.join(relevant_props)}")
            
            # 添加页面链接
            page_url = item.get("url")
            if page_url:
                answer_parts.append(f"\n   链接: {page_url}")
        
        # 添加来源信息
        if is_chinese:
            answer_parts.append(f"\n\n以上信息来自 {len(content)} 条数据库记录。")
        else:
            answer_parts.append(f"\n\nThis information is based on {len(content)} database records.")
        
        return "".join(answer_parts)


async def main():
    """主函数，演示如何使用 Notion 查询系统。"""
    print("🔍 Notion 查询系统")
    print("=" * 50)
    
    try:
        async with NotionQuerySystem() as query_system:
            # 获取数据库信息
            print("📊 获取数据库信息...")
            db_info = await query_system.get_database_info()
            
            print(f"数据库名称: {db_info['title']}")
            print(f"属性: {', '.join(db_info['properties'])}")
            print(f"创建时间: {db_info['created_time']}")
            print(f"URL: {db_info.get('url', 'N/A')}")
            
            # 获取所有内容
            print(f"\n📋 获取数据库内容...")
            all_content = await query_system.get_all_content()
            print(f"找到 {len(all_content)} 条记录")
            
            # 显示前几条记录
            for i, item in enumerate(all_content[:3], 1):
                print(f"\n记录 {i}:")
                props = item.get("properties", {})
                for key, value in props.items():
                    if value and len(str(value)) < 100:  # 只显示较短的值
                        print(f"  {key}: {value}")
            
            # 交互式问答
            print(f"\n💬 交互式问答 (输入 'quit' 退出)")
            print("-" * 30)
            
            while True:
                try:
                    question = input("\n请输入您的问题: ").strip()
                    
                    if question.lower() in ['quit', 'exit', '退出', 'q']:
                        break
                    
                    if not question:
                        continue
                    
                    # 回答问题
                    result = await query_system.answer_question(question)
                    
                    print(f"\n问题: {result['question']}")
                    print(f"答案: {result['answer']}")
                    print(f"参考来源: {result['source_count']} 条记录")
                    
                    if result.get('error'):
                        print(f"错误: {result['error']}")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"处理问题时出错: {e}")
            
            print("\n👋 感谢使用 Notion 查询系统！")
    
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n请设置以下环境变量:")
        print("export NOTION_API_KEY='your_notion_api_key'")
        print("export NOTION_DATABASE_ID='your_database_id'")
        print("\n或者:")
        print("export NOTION_KEY='your_notion_api_key'")
        print("export NOTION_DATABASE_ID='your_database_id'")
    
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        logger.error(f"系统错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())