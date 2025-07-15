import json
import os
from typing import List, Dict, Any
from datetime import datetime
from .base import BaseStorageProvider, RetrievedChunk

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    print("⚠️  OSS2 not available. Please install: pip install oss2")

class OSSStorageProvider(BaseStorageProvider):
    """
    阿里云OSS存储提供者，将知识块存储为OSS对象。
    支持阿里云OSS、MinIO等S3兼容的对象存储。
    需要配置: endpoint, access_key_id, access_key_secret, bucket_name
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        if not OSS_AVAILABLE:
            raise ImportError("OSS2 library not available. Install with: pip install oss2")
        
        self.endpoint = config.get("endpoint")
        self.access_key_id = config.get("access_key_id")
        self.access_key_secret = config.get("access_key_secret")
        self.bucket_name = config.get("bucket_name")
        self.prefix = config.get("prefix", "knowledge_chunks/")
        
        # 验证必要配置
        required_configs = ["endpoint", "access_key_id", "access_key_secret", "bucket_name"]
        for config_key in required_configs:
            if not config.get(config_key):
                raise ValueError(f"{config_key} is required in config")
        
        # 初始化OSS客户端
        try:
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
            
            # 测试连接
            self._test_connection()
            
        except Exception as e:
            raise ValueError(f"Failed to initialize OSS client: {str(e)}")

    def _test_connection(self):
        """测试OSS连接"""
        try:
            # 尝试列出bucket信息
            bucket_info = self.bucket.get_bucket_info()
            print(f"✅ OSS连接成功: {bucket_info.name}")
        except Exception as e:
            raise ValueError(f"OSS连接测试失败: {str(e)}")

    def store(self, chunks: List[Any]) -> bool:
        """将知识块存储到OSS"""
        print(f"[OSSProvider] 存储 {len(chunks)} 个知识块...")
        
        success_count = 0
        
        for chunk in chunks:
            try:
                # 构造对象key
                object_key = f"{self.prefix}{chunk.id}.json"
                
                # 准备数据
                chunk_data = {
                    "id": chunk.id,
                    "original_id": chunk.original_id,
                    "text_content": chunk.text_content,
                    "vector": chunk.vector,
                    "category": chunk.category,
                    "entities": chunk.entities,
                    "relationships": chunk.relationships,
                    "metadata": chunk.metadata,
                    "created_time": datetime.now().isoformat(),
                    "updated_time": datetime.now().isoformat()
                }
                
                # 转换为JSON字符串
                json_data = json.dumps(chunk_data, ensure_ascii=False, indent=2)
                
                # 上传到OSS
                result = self.bucket.put_object(
                    object_key, 
                    json_data,
                    headers={'Content-Type': 'application/json; charset=utf-8'}
                )
                
                if result.status == 200:
                    success_count += 1
                    print(f"✅ 成功存储: {chunk.id}")
                else:
                    print(f"❌ 存储失败: {chunk.id} - Status: {result.status}")
                    
            except Exception as e:
                print(f"❌ 存储异常: {chunk.id} - {str(e)}")
        
        print(f"[OSSProvider] 存储完成: {success_count}/{len(chunks)} 成功")
        return success_count > 0

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """从OSS检索知识块"""
        print(f"[OSSProvider] 检索前 {top_k} 个知识块...")
        
        try:
            # 获取所有对象
            objects = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.prefix):
                if obj.key.endswith('.json'):
                    objects.append(obj)
            
            # 按修改时间排序
            objects.sort(key=lambda x: x.last_modified, reverse=True)
            
            # 限制数量
            objects = objects[:top_k]
            
            retrieved_chunks = []
            
            for obj in objects:
                try:
                    # 下载对象内容
                    content = self.bucket.get_object(obj.key).read()
                    chunk_data = json.loads(content.decode('utf-8'))
                    
                    # 应用过滤器
                    if filters:
                        skip = False
                        for key, value in filters.items():
                            if key == "category" and chunk_data.get("category") != value:
                                skip = True
                                break
                            elif key in chunk_data.get("metadata", {}):
                                if chunk_data["metadata"][key] != value:
                                    skip = True
                                    break
                        
                        if skip:
                            continue
                    
                    # 创建RetrievedChunk对象
                    retrieved_chunks.append(
                        RetrievedChunk(
                            id=chunk_data["id"],
                            text_content=chunk_data["text_content"],
                            score=0.9,  # 固定分数，实际应该基于向量相似度
                            metadata=chunk_data.get("metadata", {})
                        )
                    )
                    
                except Exception as e:
                    print(f"❌ 处理对象失败: {obj.key} - {str(e)}")
                    continue
            
            print(f"[OSSProvider] 检索完成: 找到 {len(retrieved_chunks)} 个知识块")
            return retrieved_chunks
            
        except Exception as e:
            print(f"❌ 检索异常: {str(e)}")
            return []

    def get_all_chunk_ids(self) -> List[str]:
        """获取所有知识块ID"""
        print("[OSSProvider] 获取所有知识块ID...")
        
        try:
            chunk_ids = []
            
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.prefix):
                if obj.key.endswith('.json'):
                    # 从对象key中提取chunk_id
                    chunk_id = obj.key.replace(self.prefix, '').replace('.json', '')
                    chunk_ids.append(chunk_id)
            
            print(f"[OSSProvider] 找到 {len(chunk_ids)} 个知识块ID")
            return chunk_ids
            
        except Exception as e:
            print(f"❌ 获取ID异常: {str(e)}")
            return []

    def delete_chunk(self, chunk_id: str) -> bool:
        """删除指定的知识块"""
        print(f"[OSSProvider] 删除知识块: {chunk_id}")
        
        try:
            object_key = f"{self.prefix}{chunk_id}.json"
            
            # 检查对象是否存在
            if not self.bucket.object_exists(object_key):
                print(f"❌ 知识块不存在: {chunk_id}")
                return False
            
            # 删除对象
            result = self.bucket.delete_object(object_key)
            
            if result.status == 204:
                print(f"✅ 成功删除: {chunk_id}")
                return True
            else:
                print(f"❌ 删除失败: {chunk_id} - Status: {result.status}")
                return False
                
        except Exception as e:
            print(f"❌ 删除异常: {str(e)}")
            return False

    def update_chunk(self, chunk_id: str, new_content: str, new_metadata: Dict = None) -> bool:
        """更新知识块内容"""
        print(f"[OSSProvider] 更新知识块: {chunk_id}")
        
        try:
            object_key = f"{self.prefix}{chunk_id}.json"
            
            # 检查对象是否存在
            if not self.bucket.object_exists(object_key):
                print(f"❌ 知识块不存在: {chunk_id}")
                return False
            
            # 获取现有数据
            content = self.bucket.get_object(object_key).read()
            chunk_data = json.loads(content.decode('utf-8'))
            
            # 更新数据
            chunk_data["text_content"] = new_content
            chunk_data["updated_time"] = datetime.now().isoformat()
            
            if new_metadata:
                chunk_data["metadata"].update(new_metadata)
            
            # 重新上传
            json_data = json.dumps(chunk_data, ensure_ascii=False, indent=2)
            result = self.bucket.put_object(
                object_key,
                json_data,
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            
            if result.status == 200:
                print(f"✅ 成功更新: {chunk_id}")
                return True
            else:
                print(f"❌ 更新失败: {chunk_id} - Status: {result.status}")
                return False
                
        except Exception as e:
            print(f"❌ 更新异常: {str(e)}")
            return False

    def get_chunk_by_id(self, chunk_id: str) -> Dict:
        """根据ID获取完整的知识块数据"""
        print(f"[OSSProvider] 获取知识块: {chunk_id}")
        
        try:
            object_key = f"{self.prefix}{chunk_id}.json"
            
            if not self.bucket.object_exists(object_key):
                print(f"❌ 知识块不存在: {chunk_id}")
                return {}
            
            content = self.bucket.get_object(object_key).read()
            chunk_data = json.loads(content.decode('utf-8'))
            
            print(f"✅ 成功获取: {chunk_id}")
            return chunk_data
            
        except Exception as e:
            print(f"❌ 获取异常: {str(e)}")
            return {}

    def batch_delete_chunks(self, chunk_ids: List[str]) -> Dict[str, bool]:
        """批量删除知识块"""
        print(f"[OSSProvider] 批量删除 {len(chunk_ids)} 个知识块...")
        
        results = {}
        
        for chunk_id in chunk_ids:
            results[chunk_id] = self.delete_chunk(chunk_id)
        
        success_count = sum(1 for success in results.values() if success)
        print(f"[OSSProvider] 批量删除完成: {success_count}/{len(chunk_ids)} 成功")
        
        return results

    def get_storage_stats(self) -> Dict:
        """获取存储统计信息"""
        print("[OSSProvider] 获取存储统计信息...")
        
        try:
            total_chunks = 0
            total_size = 0
            
            for obj in oss2.ObjectIterator(self.bucket, prefix=self.prefix):
                if obj.key.endswith('.json'):
                    total_chunks += 1
                    total_size += obj.size
            
            stats = {
                "total_chunks": total_chunks,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "bucket_name": self.bucket_name,
                "prefix": self.prefix
            }
            
            print(f"[OSSProvider] 统计信息: {stats}")
            return stats
            
        except Exception as e:
            print(f"❌ 获取统计信息异常: {str(e)}")
            return {}
