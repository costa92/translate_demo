# Unified Knowledge Base System Examples

This directory contains examples demonstrating how to use the Unified Knowledge Base System.

## Quick Start Examples

### 1. Basic Usage

Run the quick start example to see how to initialize the knowledge base, add documents, and query the knowledge base:

```bash
python quick_start.py
```

### 2. API Server Examples

#### Minimal API Server (Recommended)

Run the minimal API server for a lightweight implementation:

```bash
python minimal_api_server.py
```

This server uses the simplified KnowledgeBase implementation and doesn't depend on the agent system.

#### Standalone API Server

Run the standalone API server to interact with the knowledge base through a REST API:

```bash
python standalone_api.py
```

Then open `standalone_api.html` in your web browser to interact with the API through a simple web interface.

#### Simple API Server

Run the simple API server (which uses the minimal implementation):

```bash
python simple_api_server.py
```

## Advanced Examples

### 1. Full API Server

Run the full API server with all features enabled:

```bash
python api_server_example.py
```

### 2. Model Provider Examples

#### DeepSeek

Run the DeepSeek query demo:

```bash
python deepseek_query_demo.py
```

Advanced usage:

```bash
# 显示模型信息
python deepseek_query_demo.py --info

# 使用特定模型
python deepseek_query_demo.py --model deepseek-coder

# 跳过添加示例文档
python deepseek_query_demo.py --skip-docs
```

#### SiliconFlow

Run the SiliconFlow query demo:

```bash
python siliconflow_query_demo.py
```

Advanced usage:

```bash
# 显示模型信息
python siliconflow_query_demo.py --info

# 运行性能基准测试
python siliconflow_query_demo.py --benchmark

# 使用特定设备和精度
python siliconflow_query_demo.py --device cuda --precision float16
```

### 3. Storage Provider Examples

#### Google Cloud Storage (GCS)

Run the simple GCS demo:

```bash
python simple_gcs_demo.py
```

### 2. Core Demos

For a more guided experience, run the core demos:

```bash
python core_demos/run_all_demos.py
```

This will present a menu of different demos you can run.

## Example Files

- `quick_start.py`: Basic usage of the knowledge base
- `standalone_api.py`: Simple API server implementation
- `standalone_api.html`: Web interface for the standalone API server
- `minimal_api_server.py`: Minimal API server implementation
- `api_server_example.py`: Full API server implementation
- `core_demos/`: Directory containing core demos
  - `run_all_demos.py`: Script to run all core demos
  - `standalone_example.py`: Standalone example without dependencies
  - `minimal_api_server.py`: Minimal API server implementation
  - `run_demo.py`: Script to run the demo
  - `api_demo.html`: Web interface for the API demo