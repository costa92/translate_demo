#!/usr/bin/env python3
"""
知识库API服务启动脚本
支持多种配置方式和部署模式
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging(level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('knowledge_base_api.log')
        ]
    )

def load_environment_config():
    """加载环境变量配置"""
    # 设置默认环境变量
    env_defaults = {
        "KB_API_HOST": "0.0.0.0",
        "KB_API_PORT": "8000",
        "KB_API_DEBUG": "false",
        "KB_SYSTEM_LOG_LEVEL": "INFO",
        "KB_STORAGE_PROVIDER": "memory",
        "KB_EMBEDDING_PROVIDER": "sentence_transformers",
        "KB_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
        "KB_GENERATION_PROVIDER": "simple",
        "KB_API_DOCS_ENABLED": "true"
    }
    
    for key, default_value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知识库REST API服务器")
    parser.add_argument("--host", default=None, help="服务器主机地址")
    parser.add_argument("--port", type=int, default=None, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="日志级别")
    parser.add_argument("--simple", action="store_true", help="使用简单模式（仅基础功能）")
    parser.add_argument("--reload", action="store_true", help="启用自动重载（开发模式）")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 加载环境变量配置
    load_environment_config()
    
    # 覆盖命令行参数
    if args.host:
        os.environ["KB_API_HOST"] = args.host
    if args.port:
        os.environ["KB_API_PORT"] = str(args.port)
    if args.debug:
        os.environ["KB_API_DEBUG"] = "true"
        os.environ["KB_SYSTEM_LOG_LEVEL"] = "DEBUG"
    
    # 设置配置文件路径
    if args.config:
        os.environ["KB_CONFIG_PATH"] = args.config
    
    logger.info("启动知识库API服务器...")
    logger.info(f"主机: {os.environ['KB_API_HOST']}")
    logger.info(f"端口: {os.environ['KB_API_PORT']}")
    logger.info(f"调试模式: {os.environ['KB_API_DEBUG']}")
    logger.info(f"简单模式: {args.simple}")
    
    try:
        if args.simple:
            # 简单模式：只使用基础功能
            from knowledge_base_simple_api import main as simple_main
            simple_main()
        else:
            # 完整模式：使用所有功能
            try:
                # 尝试使用新的REST API实现
                from src.knowledge_base_rest_api import main as rest_api_main
                logger.info("使用REST API实现")
                rest_api_main()
            except ImportError:
                # 回退到旧的API实现
                from knowledge_base_api import main as full_main
                logger.info("使用标准API实现")
                full_main()
            
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()