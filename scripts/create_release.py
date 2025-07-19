#!/usr/bin/env python
"""
统一知识库系统发布脚本

此脚本用于:
1. 标记发布版本
2. 生成发布说明
3. 创建分发包
"""
import os
import sys
import re
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

def get_current_version():
    """从pyproject.toml获取当前版本"""
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return None

def update_version(new_version):
    """更新pyproject.toml中的版本号"""
    with open('pyproject.toml', 'r') as f:
        content = f.read()
    
    updated_content = re.sub(
        r'(version\s*=\s*)"([^"]+)"', 
        r'\1"' + new_version + '"', 
        content
    )
    
    with open('pyproject.toml', 'w') as f:
        f.write(updated_content)
    
    print(f"版本已更新为 {new_version}")

def update_changelog(version, changes):
    """更新CHANGELOG.md文件"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    with open('CHANGELOG.md', 'r') as f:
        content = f.readlines()
    
    # 查找插入位置（第一个版本条目之前）
    insert_pos = 0
    for i, line in enumerate(content):
        if re.match(r'^## \[\d+\.\d+\.\d+\]', line):
            insert_pos = i
            break
    
    # 准备新版本条目
    new_entry = [
        f"## [{version}] - {today}\n",
        "\n",
        "### Added\n",
    ]
    
    for change in changes.get('added', []):
        new_entry.append(f"- {change}\n")
    
    if changes.get('changed'):
        new_entry.append("\n")
        new_entry.append("### Changed\n")
        for change in changes.get('changed', []):
            new_entry.append(f"- {change}\n")
    
    if changes.get('fixed'):
        new_entry.append("\n")
        new_entry.append("### Fixed\n")
        for change in changes.get('fixed', []):
            new_entry.append(f"- {change}\n")
    
    if changes.get('removed'):
        new_entry.append("\n")
        new_entry.append("### Removed\n")
        for change in changes.get('removed', []):
            new_entry.append(f"- {change}\n")
    
    new_entry.append("\n")
    
    # 插入新版本条目
    updated_content = content[:insert_pos] + new_entry + content[insert_pos:]
    
    with open('CHANGELOG.md', 'w') as f:
        f.writelines(updated_content)
    
    print(f"CHANGELOG.md 已更新")

def tag_version(version):
    """创建Git标签"""
    try:
        subprocess.run(['git', 'tag', '-a', f'v{version}', '-m', f'Version {version}'], check=True)
        print(f"已创建标签 v{version}")
    except subprocess.CalledProcessError as e:
        print(f"创建标签失败: {e}")
        return False
    return True

def generate_release_notes(version):
    """生成发布说明"""
    # 从CHANGELOG中提取该版本的发布说明
    with open('CHANGELOG.md', 'r') as f:
        content = f.read()
    
    pattern = rf"## \[{version}\].*?(?=## \[\d+\.\d+\.\d+\]|$)"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        release_notes = match.group(0).strip()
        
        # 写入发布说明文件
        release_dir = Path('dist')
        release_dir.mkdir(exist_ok=True)
        
        with open(release_dir / f'release-notes-{version}.md', 'w') as f:
            f.write(release_notes)
        
        print(f"发布说明已生成: dist/release-notes-{version}.md")
        return True
    else:
        print("无法从CHANGELOG中提取发布说明")
        return False

def create_distribution_packages():
    """创建分发包"""
    try:
        # 清理旧的构建文件
        subprocess.run(['rm', '-rf', 'dist', 'build', '*.egg-info'], shell=True, check=True)
        
        # 使用Poetry构建包
        subprocess.run(['poetry', 'build'], check=True)
        
        print("分发包已创建:")
        for item in os.listdir('dist'):
            print(f"  - dist/{item}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"创建分发包失败: {e}")
        return False

def cleanup_code():
    """清理代码"""
    try:
        # 清理无用的示例代码
        print("清理无用的示例代码...")
        subprocess.run(['python', 'scripts/cleanup_examples.py'], check=True)
        
        # 清理其他无用代码
        print("清理其他无用代码...")
        subprocess.run(['python', 'scripts/cleanup_code.py'], check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"清理代码失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='统一知识库系统发布脚本')
    parser.add_argument('--version', help='新版本号 (例如: 1.0.1)')
    parser.add_argument('--added', nargs='+', help='添加的功能列表')
    parser.add_argument('--changed', nargs='+', help='更改的功能列表')
    parser.add_argument('--fixed', nargs='+', help='修复的问题列表')
    parser.add_argument('--removed', nargs='+', help='移除的功能列表')
    parser.add_argument('--no-tag', action='store_true', help='不创建Git标签')
    parser.add_argument('--no-build', action='store_true', help='不构建分发包')
    parser.add_argument('--no-cleanup', action='store_true', help='不清理代码')
    
    args = parser.parse_args()
    
    # 获取当前版本
    current_version = get_current_version()
    if not current_version:
        print("错误: 无法从pyproject.toml获取当前版本")
        return 1
    
    print(f"当前版本: {current_version}")
    
    # 确定新版本
    new_version = args.version
    if not new_version:
        # 提示用户输入新版本
        new_version = input(f"请输入新版本号 (当前: {current_version}): ")
        if not new_version:
            print("未指定新版本，使用当前版本")
            new_version = current_version
    
    # 验证版本格式
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("错误: 版本号格式无效，应为 X.Y.Z")
        return 1
    
    # 收集变更信息
    changes = {}
    
    if args.added:
        changes['added'] = args.added
    if args.changed:
        changes['changed'] = args.changed
    if args.fixed:
        changes['fixed'] = args.fixed
    if args.removed:
        changes['removed'] = args.removed
    
    # 如果没有提供变更信息，提示用户输入
    if not changes:
        print("请输入变更信息 (每行一项，空行结束):")
        
        print("添加的功能:")
        added = []
        while True:
            item = input("> ")
            if not item:
                break
            added.append(item)
        if added:
            changes['added'] = added
        
        print("更改的功能:")
        changed = []
        while True:
            item = input("> ")
            if not item:
                break
            changed.append(item)
        if changed:
            changes['changed'] = changed
        
        print("修复的问题:")
        fixed = []
        while True:
            item = input("> ")
            if not item:
                break
            fixed.append(item)
        if fixed:
            changes['fixed'] = fixed
        
        print("移除的功能:")
        removed = []
        while True:
            item = input("> ")
            if not item:
                break
            removed.append(item)
        if removed:
            changes['removed'] = removed
    
    # 确认操作
    print("\n准备执行以下操作:")
    print(f"1. 更新版本: {current_version} -> {new_version}")
    print("2. 更新CHANGELOG.md")
    if not args.no_cleanup:
        print("3. 清理无用代码")
    if not args.no_tag:
        print(f"4. 创建Git标签: v{new_version}")
    if not args.no_build:
        print("5. 生成发布说明")
        print("6. 创建分发包")
    
    confirm = input("\n确认执行? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return 0
    
    # 执行操作
    if current_version != new_version:
        update_version(new_version)
    
    update_changelog(new_version, changes)
    
    if not args.no_cleanup:
        if not cleanup_code():
            print("警告: 代码清理失败，但将继续执行其他操作")
    
    if not args.no_tag:
        if not tag_version(new_version):
            return 1
    
    if not args.no_build:
        if not generate_release_notes(new_version):
            return 1
        
        if not create_distribution_packages():
            return 1
    
    print(f"\n统一知识库系统 v{new_version} 发布完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())