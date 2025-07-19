#!/bin/bash
# 开发环境安装脚本

# 确保脚本在错误时退出
set -e

echo "安装统一知识库系统（开发模式）..."

# 安装额外的依赖
echo "安装额外的依赖..."
pip install psutil

# 使用 Poetry 安装项目（开发模式）
if command -v poetry &> /dev/null; then
    echo "使用 Poetry 安装..."
    poetry install
    
    # 确保安装了所有必要的依赖
    poetry add psutil
else
    # 如果没有 Poetry，使用 pip
    echo "使用 pip 安装..."
    pip install -e .
fi

echo "安装完成！"
echo ""
echo "现在你可以运行示例："
echo "  python examples/api_server.py"
echo "  python examples/knowledge_base_example.py"