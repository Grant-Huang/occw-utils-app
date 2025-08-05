#!/bin/bash

# 脚本必须以 root 或支持 sudo 权限执行

APP_DIR="/opt/occw-utils-app"
VENV_DIR="$APP_DIR/venv"
PYTHON_BIN="/usr/bin/python3.11"  # 你可以根据实际安装路径调整

echo "📦 部署 OCCW-utils 应用"

# Step 1: 切换到项目目录
cd "$APP_DIR" || { echo "❌ 无法进入目录 $APP_DIR"; exit 1; }

# Step 2: 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️ 创建 Python 3.11 虚拟环境..."
    $PYTHON_BIN -m venv venv || { echo "❌ 虚拟环境创建失败"; exit 1; }
else
    echo "✅ 虚拟环境已存在"
fi

# Step 3: 激活虚拟环境
source "$VENV_DIR/bin/activate" || { echo "❌ 虚拟环境激活失败"; exit 1; }

# Step 4: 安装依赖
if [ -f "requirements.txt" ]; then
    echo "📚 正在安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt || { echo "❌ 安装依赖失败"; exit 1; }
else
    echo "⚠️ 没有找到 requirements.txt，跳过依赖安装"
fi

# Step 5: 设置环境变量并启动应用
echo "🚀 正在启动应用..."

export PORT=999
export FLASK_ENV=production

# 使用 exec 启动，便于进程管理（尤其是结合 systemd）
exec python app.py
