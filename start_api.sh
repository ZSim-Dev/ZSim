#!/bin/bash
# ZSim API 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置环境变量
export ZSIM_DISABLE_ROUTES="0"
export ZSIM_IPC_MODE="auto"

# 启动API
echo "启动 ZSim API..."
echo "IPC模式: $ZSIM_IPC_MODE"
echo "工作目录: $SCRIPT_DIR"

# 检查可执行文件是否存在
if [ -f "./zsim_api/zsim_api" ]; then
    ./zsim_api/zsim_api
elif [ -f "./zsim_api" ]; then
    ./zsim_api
else
    echo "错误：找不到可执行文件"
    echo "请确保在正确的目录中运行此脚本"
    ls -la
    exit 1
fi