#!/usr/bin/env python
"""
生成统一知识库系统API文档
"""
import sys
import os
import inspect
import importlib
import re
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_module_docs(module_name, output_file):
    """为指定模块生成API文档"""
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        print(f"无法导入模块 {module_name}")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {module_name} API 文档\n\n")
        
        # 获取模块中的所有类
        classes = inspect.getmembers(module, inspect.isclass)
        for name, cls in classes:
            if cls.__module__ == module_name:
                f.write(f"## {name}\n\n")
                
                # 类文档
                if cls.__doc__:
                    f.write(f"{cls.__doc__.strip()}\n\n")
                
                # 获取类的方法
                methods = inspect.getmembers(cls, inspect.isfunction)
                for method_name, method in methods:
                    if not method_name.startswith('_') or method_name == '__init__':
                        f.write(f"### {method_name}\n\n")
                        
                        # 方法文档
                        if method.__doc__:
                            f.write(f"{method.__doc__.strip()}\n\n")
                        
                        # 方法签名
                        sig = inspect.signature(method)
                        params = []
                        for param_name, param in sig.parameters.items():
                            if param_name != 'self':
                                param_str = param_name
                                if param.default != inspect.Parameter.empty:
                                    param_str += f"={param.default}"
                                params.append(param_str)
                        
                        f.write(f"```python\n{method_name}({', '.join(params)})\n```\n\n")
                
                f.write("\n")

def generate_api_index(modules, output_file):
    """生成API文档索引"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 统一知识库系统 API 文档\n\n")
        f.write("## 模块\n\n")
        
        for module in modules:
            module_name = module.replace('/', '.')
            doc_path = f"api/{module.replace('/', '_')}.md"
            f.write(f"- [{module_name}]({doc_path})\n")

def main():
    """主函数"""
    # 创建API文档目录
    api_dir = Path('docs/api')
    api_dir.mkdir(exist_ok=True, parents=True)
    
    # 要生成文档的模块列表
    modules = [
        'knowledge_base',
        'knowledge_base.core',
        'knowledge_base.storage',
        'knowledge_base.processing',
        'knowledge_base.retrieval',
        'knowledge_base.generation',
        'knowledge_base.agents',
        'knowledge_base.api'
    ]
    
    # 生成每个模块的文档
    for module in modules:
        output_file = api_dir / f"{module.replace('.', '_')}.md"
        print(f"生成 {module} 的文档...")
        generate_module_docs(module, output_file)
    
    # 生成索引
    generate_api_index(modules, api_dir / 'index.md')
    print("API文档生成完成！")

if __name__ == "__main__":
    main()