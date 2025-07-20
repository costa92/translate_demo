#!/bin/bash
# 知识库 API 启动脚本

# 设置环境变量
export KB_API_HOST=${KB_API_HOST:-0.0.0.0}
export KB_API_PORT=${KB_API_PORT:-8000}
export KB_API_DEBUG=${KB_API_DEBUG:-false}
export KB_SYSTEM_LOG_LEVEL=${KB_SYSTEM_LOG_LEVEL:-INFO}
export KB_CONFIG_PATH=${KB_CONFIG_PATH:-config.yaml}

# 检查配置文件
if [ ! -f "$KB_CONFIG_PATH" ]; then
    echo "警告: 配置文件 $KB_CONFIG_PATH 不存在，将使用默认配置"
fi

# 启动 API 服务
echo "启动知识库 API 服务..."
echo "主机: $KB_API_HOST"
echo "端口: $KB_API_PORT"
echo "调试模式: $KB_API_DEBUG"
echo "日志级别: $KB_SYSTEM_LOG_LEVEL"
echo "配置文件: $KB_CONFIG_PATH"

# 运行 API
python run_api.py --host $KB_API_HOST --port $KB_API_PORT --log-level $KB_SYSTEM_LOG_LEVEL $([ "$KB_API_DEBUG" = "true" ] && echo "--debug") --config $KB_CONFIG_PATH