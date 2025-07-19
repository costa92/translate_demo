# 统一知识库系统发布流程

本文档描述了统一知识库系统的发布流程，包括版本标记、生成发布说明和创建分发包。

## 发布前准备

1. 确保所有功能开发和修复已完成
2. 确保所有测试通过
3. 更新文档（如有必要）
4. 提交所有更改到版本控制系统

## 发布流程

### 方法1：使用发布脚本（推荐）

我们提供了一个简单的发布脚本，可以自动执行整个发布流程：

```bash
# 基本用法
./scripts/release.sh

# 指定版本号
./scripts/release.sh --version 1.0.1

# 不创建Git标签
./scripts/release.sh --no-tag

# 不构建分发包
./scripts/release.sh --no-build

# 显示帮助信息
./scripts/release.sh --help
```

### 方法2：使用Python脚本

如果你需要更多控制，可以直接使用Python发布脚本：

```bash
# 基本用法
python scripts/create_release.py

# 指定版本号和变更信息
python scripts/create_release.py --version 1.0.1 \
  --added "新功能1" "新功能2" \
  --changed "更改1" "更改2" \
  --fixed "修复1" "修复2" \
  --removed "移除1" "移除2"

# 不创建Git标签
python scripts/create_release.py --no-tag

# 不构建分发包
python scripts/create_release.py --no-build
```

## 发布后操作

1. 推送标签到远程仓库：
   ```bash
   git push origin --tags
   ```

2. 上传分发包到PyPI：
   ```bash
   poetry publish
   ```

3. 在GitHub上创建发布：
   - 访问项目的GitHub页面
   - 点击"Releases"
   - 点击"Draft a new release"
   - 选择刚创建的标签
   - 填写发布标题和描述（可以使用生成的发布说明）
   - 上传分发包
   - 点击"Publish release"

## 生成API文档

我们提供了一个脚本来生成API文档：

```bash
python scripts/generate_api_docs.py
```

生成的文档将保存在`docs/api/`目录中。

## 清理多余代码

我们提供了一个脚本来清理多余的代码：

```bash
python scripts/cleanup_code.py
```

此脚本将删除重复实现、临时文件和其他不需要的代码。