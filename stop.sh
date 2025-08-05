#!/bin/bash

APP_DIR="/opt/occw-utils-app"
PID_FILE="$APP_DIR/gunicorn.pid"

echo "🛑 停止 OCCW-utils 应用"

# 进入应用目录
cd "$APP_DIR" || { echo "❌ 无法进入目录 $APP_DIR"; exit 1; }

# 检查 PID 文件是否存在
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "⚙️ 正在终止进程 PID=$PID"
        kill $PID && echo "✅ 应用已停止"
    else
        echo "⚠️ 找到 PID 文件但进程不存在，可能已经停止"
    fi
    rm -f "$PID_FILE"
else
    echo "ℹ️ 未找到 gunicorn.pid，应用可能未运行"
fi
