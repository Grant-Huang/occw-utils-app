#!/bin/bash

APP_DIR="/opt/occw-utils-app"
PID_FILE="$APP_DIR/gunicorn.pid"

echo "📊 OCCW-utils 应用状态检查"

# 进入应用目录
cd "$APP_DIR" || { echo "❌ 无法进入目录 $APP_DIR"; exit 1; }

# 检查 PID 文件
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "📄 PID 文件存在: $PID_FILE (PID: $PID)"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 进程正在运行 (PID: $PID)"
        echo "📋 进程详情:"
        ps -p $PID -o pid,ppid,cmd,etime
    else
        echo "⚠️ PID 文件存在但进程不存在"
    fi
else
    echo "📄 PID 文件不存在: $PID_FILE"
fi

# 通过进程名查找
echo ""
echo "🔍 通过进程名查找 gunicorn 进程:"
GUNICORN_PROCESSES=$(pgrep -f "gunicorn.*app:app" 2>/dev/null)
if [ -n "$GUNICORN_PROCESSES" ]; then
    echo "✅ 找到 gunicorn 进程:"
    for PID in $GUNICORN_PROCESSES; do
        echo "  PID: $PID"
        ps -p $PID -o pid,ppid,cmd,etime 2>/dev/null
    done
else
    echo "ℹ️ 未找到运行中的 gunicorn 进程"
fi

# 检查端口占用
echo ""
echo "🌐 检查端口 999 占用情况:"
if netstat -tlnp 2>/dev/null | grep ":999 " > /dev/null; then
    echo "✅ 端口 999 正在被使用:"
    netstat -tlnp 2>/dev/null | grep ":999 "
elif ss -tlnp 2>/dev/null | grep ":999 " > /dev/null; then
    echo "✅ 端口 999 正在被使用:"
    ss -tlnp 2>/dev/null | grep ":999 "
else
    echo "ℹ️ 端口 999 未被占用"
fi

# 检查日志文件
echo ""
echo "📝 日志文件检查:"
if [ -f "gunicorn.log" ]; then
    echo "✅ gunicorn.log 存在"
    echo "📄 最后 5 行日志:"
    tail -5 gunicorn.log
else
    echo "ℹ️ gunicorn.log 不存在"
fi

if [ -f "nohup.out" ]; then
    echo "✅ nohup.out 存在"
    echo "📄 最后 5 行输出:"
    tail -5 nohup.out
fi 