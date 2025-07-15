import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseStorageProvider, RetrievedChunk

class NotionStorageProvider(BaseStorageProvider):
    """
    Notion存储提供者，将知识块存储为Notion数据库中的页面。
    需要配置: notion_token, database_id
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.notion_token = config.get("notion_token")
        self.database_id = config.get("database_id")
        
        if not self.notion_token:
            raise ValueError("notion_token is required in config")
        if not self.database_id:
            raise ValueError("database_id is required in config")
        
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # 验证数据库是否存在并有正确的属性
        self._verify_database()

    def _verify_database(self):
        """验证数据库是否存在并具有必要的属性"""
        try:
            url = f"https://api.notion.com/v1/databases/{self.database_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise ValueError(f"无法访问数据库 {self.database_id}: {response.text}")
            
            db_info = response.json()
            properties = db_info.get("properties", {})
            
            # 检查必要的属性
            required_properties = ["chunk_id", "content", "category", "metadata"]
            missing_properties = []
            
            for prop in required_properties:
                if prop not in properties:
                    missing_properties.append(prop)
            
            if missing_properties:
                print(f"⚠️  数据库缺少属性: {missing_properties}")
                print("请确保Notion数据库包含以下属性:")
                print("- chunk_id (标题)")
                print("- content (富文本)")
                print("- category (选择)")
                print("- metadata (富文本)")
                
        except Exception as e:
            print(f"数据库验证失败: {e}")

    def store(self, chunks: List[Any]) -> bool:
        """将知识块存储到Notion数据库中"""
        print(f"[NotionProvider] 存储 {len(chunks)} 个知识块...")
        
        success_count = 0
        
        for chunk in chunks:
            try:
                # 构造页面数据
                page_data = {
                    "parent": {"database_id": self.database_id},
                    "properties": {
                        "chunk_id": {
                            "title": [{"text": {"content": chunk.id}}]
                        },
                        "content": {
                            "rich_text": [{"text": {"content": chunk.text_content[:2000]}}]  # Notion限制
                        },
                        "category": {
                            "select": {"name": chunk.category}
                        },
                        "metadata": {
                            "rich_text": [{"text": {"content": json.dumps(chunk.metadata, ensure_ascii=False)}}]
                        }
                    }
                }
                
                # 创建页面
                response = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=self.headers,
                    json=page_data
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"✅ 成功存储: {chunk.id}")
                else:
                    print(f"❌ 存储失败: {chunk.id} - {response.text}")
                    
            except Exception as e:
                print(f"❌ 存储异常: {chunk.id} - {str(e)}")
        
        print(f"[NotionProvider] 存储完成: {success_count}/{len(chunks)} 成功")
        return success_count > 0

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """从Notion数据库检索知识块"""
        print(f"[NotionProvider] 检索前 {top_k} 个知识块...")
        
        try:
            # 构建查询
            query_data = {
                "page_size": top_k,
                "sorts": [{"timestamp": "created_time", "direction": "descending"}]
            }
            
            # 添加过滤器
            if filters:
                query_filters = []
                for key, value in filters.items():
                    if key == "category":
                        query_filters.append({
                            "property": "category",
                            "select": {"equals": value}
                        })
                
                if query_filters:
                    query_data["filter"] = {"and": query_filters}
            
            # 执行查询
            response = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.headers,
                json=query_data
            )
            
            if response.status_code != 200:
                print(f"❌ 检索失败: {response.text}")
                return []
            
            results = response.json().get("results", [])
            retrieved_chunks = []
            
            for page in results:
                try:
                    properties = page.get("properties", {})
                    
                    # 提取数据
                    chunk_id = self._extract_title(properties.get("chunk_id"))
                    content = self._extract_rich_text(properties.get("content"))
                    metadata_str = self._extract_rich_text(properties.get("metadata"))
                    
                    # 解析metadata
                    metadata = {}
                    if metadata_str:
                        try:
                            metadata = json.loads(metadata_str)
                        except json.JSONDecodeError:
                            metadata = {"raw": metadata_str}
                    
                    retrieved_chunks.append(
                        RetrievedChunk(
                            id=chunk_id,
                            text_content=content,
                            score=0.9,  # 固定分数，实际应该基于相关性
                            metadata=metadata
                        )
                    )
                    
                except Exception as e:
                    print(f"❌ 处理页面数据失败: {str(e)}")
                    continue
            
            print(f"[NotionProvider] 检索完成: 找到 {len(retrieved_chunks)} 个知识块")
            return retrieved_chunks
            
        except Exception as e:
            print(f"❌ 检索异常: {str(e)}")
            return []

    def get_all_chunk_ids(self) -> List[str]:
        """获取所有知识块ID"""
        print("[NotionProvider] 获取所有知识块ID...")
        
        try:
            chunk_ids = []
            has_more = True
            next_cursor = None
            
            while has_more:
                query_data = {
                    "page_size": 100,
                    "sorts": [{"timestamp": "created_time", "direction": "descending"}]
                }
                
                if next_cursor:
                    query_data["start_cursor"] = next_cursor
                
                response = requests.post(
                    f"https://api.notion.com/v1/databases/{self.database_id}/query",
                    headers=self.headers,
                    json=query_data
                )
                
                if response.status_code != 200:
                    print(f"❌ 获取ID失败: {response.text}")
                    break
                
                data = response.json()
                results = data.get("results", [])
                
                for page in results:
                    try:
                        properties = page.get("properties", {})
                        chunk_id = self._extract_title(properties.get("chunk_id"))
                        if chunk_id:
                            chunk_ids.append(chunk_id)
                    except Exception as e:
                        print(f"❌ 处理页面ID失败: {str(e)}")
                        continue
                
                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor")
            
            print(f"[NotionProvider] 找到 {len(chunk_ids)} 个知识块ID")
            return chunk_ids
            
        except Exception as e:
            print(f"❌ 获取ID异常: {str(e)}")
            return []

    def _extract_title(self, title_property: Optional[Dict]) -> str:
        """从title属性中提取文本"""
        if not title_property or "title" not in title_property:
            return ""
        
        title_array = title_property["title"]
        if not title_array:
            return ""
        
        return title_array[0].get("text", {}).get("content", "")

    def _extract_rich_text(self, rich_text_property: Optional[Dict]) -> str:
        """从rich_text属性中提取文本"""
        if not rich_text_property or "rich_text" not in rich_text_property:
            return ""
        
        rich_text_array = rich_text_property["rich_text"]
        if not rich_text_array:
            return ""
        
        return "".join([item.get("text", {}).get("content", "") for item in rich_text_array])

    def delete_chunk(self, chunk_id: str) -> bool:
        """删除指定的知识块"""
        print(f"[NotionProvider] 删除知识块: {chunk_id}")
        
        try:
            # 先找到对应的页面
            query_data = {
                "filter": {
                    "property": "chunk_id",
                    "title": {"equals": chunk_id}
                }
            }
            
            response = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.headers,
                json=query_data
            )
            
            if response.status_code != 200:
                print(f"❌ 查找页面失败: {response.text}")
                return False
            
            results = response.json().get("results", [])
            if not results:
                print(f"❌ 未找到知识块: {chunk_id}")
                return False
            
            # 删除页面（实际是归档）
            page_id = results[0]["id"]
            delete_response = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=self.headers,
                json={"archived": True}
            )
            
            if delete_response.status_code == 200:
                print(f"✅ 成功删除: {chunk_id}")
                return True
            else:
                print(f"❌ 删除失败: {delete_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 删除异常: {str(e)}")
            return False

    def update_chunk(self, chunk_id: str, new_content: str, new_metadata: Dict = None) -> bool:
        """更新知识块内容"""
        print(f"[NotionProvider] 更新知识块: {chunk_id}")
        
        try:
            # 先找到对应的页面
            query_data = {
                "filter": {
                    "property": "chunk_id",
                    "title": {"equals": chunk_id}
                }
            }
            
            response = requests.post(
                f"https://api.notion.com/v1/databases/{self.database_id}/query",
                headers=self.headers,
                json=query_data
            )
            
            if response.status_code != 200:
                print(f"❌ 查找页面失败: {response.text}")
                return False
            
            results = response.json().get("results", [])
            if not results:
                print(f"❌ 未找到知识块: {chunk_id}")
                return False
            
            # 更新页面
            page_id = results[0]["id"]
            update_data = {
                "properties": {
                    "content": {
                        "rich_text": [{"text": {"content": new_content[:2000]}}]
                    }
                }
            }
            
            if new_metadata:
                update_data["properties"]["metadata"] = {
                    "rich_text": [{"text": {"content": json.dumps(new_metadata, ensure_ascii=False)}}]
                }
            
            update_response = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers=self.headers,
                json=update_data
            )
            
            if update_response.status_code == 200:
                print(f"✅ 成功更新: {chunk_id}")
                return True
            else:
                print(f"❌ 更新失败: {update_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 更新异常: {str(e)}")
            return False
