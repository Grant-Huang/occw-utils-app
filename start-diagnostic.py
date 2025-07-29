#!/usr/bin/env python3
"""
OCCW报价系统 - 诊断启动脚本
"""

from flask import Flask, jsonify
import os
import sys
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """主页"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCCW报价系统 - 诊断应用</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #155724; background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .version {{ background: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 OCCW报价系统 - 诊断应用</h1>
            
            <div class="version">
                <strong>部署版本:</strong> v1.6.0 - 专用启动脚本<br>
                <strong>部署时间:</strong> 2025-01-29<br>
                <strong>构建步骤:</strong> 专用启动脚本<br>
                <strong>当前时间:</strong> {current_time}
            </div>
            
            <div class="success">
                <h3>✅ Flask基础功能正常</h3>
                <p>Flask应用已成功部署到Render</p>
            </div>
            
            <div class="info">
                <h3>📋 系统信息</h3>
                <p><strong>Python版本:</strong> {sys.version}</p>
                <p><strong>Flask版本:</strong> {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}</p>
                <p><strong>端口:</strong> {os.environ.get('PORT', '5000')}</p>
                <p><strong>环境:</strong> {os.environ.get('FLASK_ENV', 'production')}</p>
                <p><strong>启动脚本:</strong> start-diagnostic.py</p>
            </div>
            
            <div class="warning">
                <h3>⚠️ 依赖包状态</h3>
                <p><strong>pandas:</strong> 未安装或未导入</p>
                <p><strong>numpy:</strong> 未安装或未导入</p>
                <p><strong>PyPDF2:</strong> 未安装或未导入</p>
                <p><strong>openpyxl:</strong> 未安装或未导入</p>
                <p><em>这可能是因为Render没有执行构建命令，或者包安装失败</em></p>
            </div>
            
            <div class="info">
                <h3>🔗 测试链接</h3>
                <ul>
                    <li><a href="/api/status">API状态</a></li>
                    <li><a href="/health">健康检查</a></li>
                    <li><a href="/test/packages">包状态测试</a></li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🚀 下一步</h3>
                <p>需要解决依赖包安装问题：</p>
                <ol>
                    <li>✅ Flask基础功能 - <strong>已完成</strong></li>
                    <li>⏳ 检查构建日志 - <strong>进行中</strong></li>
                    <li>⏳ 修复包安装问题</li>
                    <li>⏳ 逐步添加功能</li>
                    <li>⏳ 部署完整OCCW报价系统</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def status():
    """状态API"""
    return jsonify({
        'status': 'success',
        'message': 'OCCW报价系统基础功能正常',
        'python_version': sys.version,
        'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3',
        'port': os.environ.get('PORT', '5000'),
        'deploy_version': 'v1.6.0',
        'deploy_time': '2025-01-29',
        'build_step': '专用启动脚本',
        'packages_status': {
            'flask': 'installed',
            'pandas': 'unknown',
            'numpy': 'unknown',
            'pypdf2': 'unknown',
            'openpyxl': 'unknown'
        }
    })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'OCCW Quote System - Diagnostic Script',
        'version': '1.6.0',
        'deploy_time': '2025-01-29'
    })

@app.route('/test/packages')
def test_packages():
    """包状态测试"""
    packages = {}
    
    # 测试pandas
    try:
        import pandas as pd
        packages['pandas'] = {'status': 'installed', 'version': pd.__version__}
    except ImportError:
        packages['pandas'] = {'status': 'not_installed', 'error': 'No module named pandas'}
    
    # 测试numpy
    try:
        import numpy as np
        packages['numpy'] = {'status': 'installed', 'version': np.__version__}
    except ImportError:
        packages['numpy'] = {'status': 'not_installed', 'error': 'No module named numpy'}
    
    # 测试PyPDF2
    try:
        import PyPDF2
        packages['pypdf2'] = {'status': 'installed', 'version': PyPDF2.__version__}
    except ImportError:
        packages['pypdf2'] = {'status': 'not_installed', 'error': 'No module named PyPDF2'}
    
    # 测试openpyxl
    try:
        import openpyxl
        packages['openpyxl'] = {'status': 'installed', 'version': openpyxl.__version__}
    except ImportError:
        packages['openpyxl'] = {'status': 'not_installed', 'error': 'No module named openpyxl'}
    
    return jsonify({
        'status': 'success',
        'packages': packages,
        'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"启动专用诊断脚本，端口: {port}")
    print(f"Python版本: {sys.version}")
    print(f"Flask版本: {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}")
    print(f"部署版本: v1.6.0 - 专用启动脚本")
    print(f"部署时间: 2025-01-29")
    app.run(host='0.0.0.0', port=port, debug=False) 