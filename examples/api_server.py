#!/usr/bin/env python
"""
API server example for the Unified Knowledge Base System.

This example demonstrates how to start the API server with a custom configuration.
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # 尝试从 src 导入
    from src.knowledge_base.api.server import run_app
    from src.knowledge_base.core.config import Config
    print("成功从 src.knowledge_base 导入模块")
except ImportError:
    try:
        # 尝试直接导入
        from knowledge_base.api.server import run_app
        from knowledge_base.core.config import Config
        print("成功从 knowledge_base 导入模块")
    except ImportError:
        print("错误: 无法导入必要的模块。请确保项目已正确安装。")
        print("尝试运行: pip install -e .")
        print("或者使用最小化 API 服务器: python examples/minimal_api_server.py")
        sys.exit(1)


def main():
    """Run the API server example."""
    # Create a custom configuration
    config = Config()
    
    # Customize API settings
    config.api.host = "0.0.0.0"
    config.api.port = 8000
    config.api.docs_enabled = True
    config.api.cors_origins = ["*"]
    
    # Customize storage settings
    config.storage.provider = "memory"
    
    # Customize embedding settings
    config.embedding.provider = "sentence_transformers"
    config.embedding.model = "all-MiniLM-L6-v2"
    
    # Customize generation settings
    config.generation.provider = "openai"
    config.generation.model = "gpt-3.5-turbo"
    
    # Start the API server
    print("Starting API server...")
    print(f"API documentation will be available at http://{config.api.host}:{config.api.port}/docs")
    try:
        run_app(config)
    except Exception as e:
        print(f"启动 API 服务器时出错: {e}")
        print("请尝试使用最小化 API 服务器: python examples/minimal_api_server.py")
        sys.exit(1)


if __name__ == "__main__":
    main()