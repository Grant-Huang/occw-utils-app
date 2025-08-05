#!/bin/bash

# 脚本必须以 root 或支持 sudo 权限执行
APP_DIR="/opt/occw-utils-app"
VENV_DIR="$APP_DIR/venv"
PYTHON_BIN="/usr/bin/python3.11"  # 根据实际路径修改
GUNICORN_PORT=999

echo "📦 部署 OCCW-utils 应用 (使用 Gunicorn)"

# Step 1: 进入项目目录
cd "$APP_DIR" || { echo "❌ 无法进入目录 $APP_DIR"; exit 1; }

# Step 2: 创建虚拟环境（如果尚未存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️ 创建 Python 虚拟环境..."
    $PYTHON_BIN -m venv venv || { echo "❌ 创建虚拟环境失败"; exit 1; }
else
    echo "✅ 虚拟环境已存在"
fi

# Step 3: 激活虚拟环境
source "$VENV_DIR/bin/activate" || { echo "❌ 激活虚拟环境失败"; exit 1; }

# Step 4: 安装依赖
if [ -f "requirements.txt" ]; then
    echo "📚 安装依赖中..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️ 未找到 requirements.txt，跳过依赖安装"
fi

# Step 5: 安装 gunicorn（如果未安装）
if ! pip show gunicorn >/dev/null 2>&1; then
    echo "🔧 安装 Gunicorn..."
    pip install gunicorn
fi

# Step 6: 启动 Flask 应用（通过 Gunicorn）
echo "🚀 正在通过 Gunicorn 启动 Flask 应用..."
#gunicorn -w 4 -b 0.0.0.0:$GUNICORN_PORT app:app
nohup gunicorn -w 1 -b 0.0.0.0:999 app:app > gunicorn.log 2>&1 &
