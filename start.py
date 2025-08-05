#!/usr/bin/env python3
"""
OCCW报价系统启动脚本
确保必要的目录存在，然后启动Flask应用
"""
import os
import sys

def ensure_directories():
    """确保必要的目录存在"""
    directories = ['uploads', 'data', 'upload']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ 创建目录: {directory}")

def check_dependencies():
    """检查必要的依赖"""
    try:
        import flask
        import pandas
        import PyPDF2
        import openpyxl
        import reportlab
        import gunicorn
        print("✅ 所有依赖包已正确安装")
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        sys.exit(1)

def main():
    """主启动函数"""
    print("🚀 启动OCCW报价系统...")
    
    # 检查依赖
    check_dependencies()
    
    # 确保目录存在
    ensure_directories()
    
    # 启动Flask应用
    print("📝 启动Flask应用...")
    from app import app
    
    # 从环境变量获取端口，Render默认提供PORT环境变量
    port = int(os.environ.get('PORT', 999))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🌐 服务器将在端口 {port} 上启动")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    # 在生产环境中运行
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main() 