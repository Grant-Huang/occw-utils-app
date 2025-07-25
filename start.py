#!/usr/bin/env python3
"""
Render部署启动脚本
确保必要的目录存在，然后启动Flask应用
"""
import os
import subprocess
import sys

def ensure_directories():
    """确保必要的目录存在"""
    directories = ['uploads', 'data']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")

def main():
    """主启动函数"""
    print("🚀 启动2020软件报价单转换系统...")
    
    # 确保目录存在
    ensure_directories()
    
    # 启动Flask应用
    print("📝 启动Flask应用...")
    from app import app
    
    # 从环境变量获取端口，Render默认提供PORT环境变量
    port = int(os.environ.get('PORT', 5000))
    
    # 在生产环境中运行
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main() 