#!/bin/bash
# 统一知识库系统发布脚本

# 确保脚本在错误时退出
set -e

# 显示帮助信息
show_help() {
  echo "统一知识库系统发布脚本"
  echo ""
  echo "用法: $0 [选项]"
  echo ""
  echo "选项:"
  echo "  -v, --version VERSION   指定版本号 (例如: 1.0.1)"
  echo "  -n, --no-tag            不创建Git标签"
  echo "  -b, --no-build          不构建分发包"
  echo "  -h, --help              显示此帮助信息"
  echo ""
  echo "示例:"
  echo "  $0 --version 1.0.1"
  echo "  $0 --no-tag"
}

# 解析命令行参数
ARGS=""
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--version)
      ARGS="$ARGS --version $2"
      shift 2
      ;;
    -n|--no-tag)
      ARGS="$ARGS --no-tag"
      shift
      ;;
    -b|--no-build)
      ARGS="$ARGS --no-build"
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "未知选项: $1"
      show_help
      exit 1
      ;;
  esac
done

# 检查是否有未提交的更改
if [[ -n $(git status --porcelain) ]]; then
  echo "警告: 存在未提交的更改。建议在发布前提交所有更改。"
  read -p "是否继续? (y/n): " CONTINUE
  if [[ $CONTINUE != "y" ]]; then
    echo "操作已取消"
    exit 0
  fi
fi

# 运行Python发布脚本
echo "执行发布流程..."
python scripts/create_release.py $ARGS

# 如果成功，提示用户推送标签
if [[ $? -eq 0 && "$ARGS" != *"--no-tag"* ]]; then
  echo ""
  echo "提示: 别忘了推送标签到远程仓库:"
  echo "  git push origin --tags"
fi