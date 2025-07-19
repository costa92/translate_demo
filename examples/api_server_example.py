#!/usr/bin/env python
"""
启动案例：统一知识库系统API服务器
"""
import sys
import os

# 导入知识库API服务器
from knowledge_base.api.server import run_app

if __name__ == "__main__":
    # 启动API服务器
    run_app(host="0.0.0.0", port=8000)
    
    print("API服务器已启动，访问 http://localhost:8000/docs 查看API文档")