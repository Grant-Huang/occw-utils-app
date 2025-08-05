#!/bin/bash

APP_DIR="/opt/occw-utils-app"
PID_FILE="$APP_DIR/gunicorn.pid"

echo "🛑 停止 OCCW-utils 应用"

# 进入应用目录
cd "$APP_DIR" || { echo "❌ 无法进入目录 $APP_DIR"; exit 1; }

# 方法1: 通过 PID 文件停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚙️ 正在终止进程 PID=$PID"
        kill $PID
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ 进程仍在运行，强制终止..."
            kill -9 $PID
        fi
        echo "✅ 应用已停止"
    else
        echo "⚠️ 找到 PID 文件但进程不存在，可能已经停止"
    fi
    rm -f "$PID_FILE"
else
    echo "ℹ️ 未找到 gunicorn.pid，尝试通过进程名查找..."
fi

# 方法2: 通过进程名查找并停止
GUNICORN_PROCESSES=$(pgrep -f "gunicorn.*app:app" 2>/dev/null)
if [ -n "$GUNICORN_PROCESSES" ]; then
    echo "🔍 找到 gunicorn 进程: $GUNICORN_PROCESSES"
    for PID in $GUNICORN_PROCESSES; do
        echo "⚙️ 正在终止进程 PID=$PID"
        kill $PID
    done
    sleep 2
    
    # 检查是否还有进程在运行
    REMAINING_PROCESSES=$(pgrep -f "gunicorn.*app:app" 2>/dev/null)
    if [ -n "$REMAINING_PROCESSES" ]; then
        echo "⚠️ 仍有进程在运行，强制终止..."
        for PID in $REMAINING_PROCESSES; do
            kill -9 $PID
        done
    fi
    echo "✅ 所有 gunicorn 进程已停止"
else
    echo "ℹ️ 未找到运行中的 gunicorn 进程"
fi

# 清理可能的残留文件
rm -f "$PID_FILE"
rm -f nohup.out
