#!/usr/bin/env python3
"""
OCCW报价系统 - 基础版本
"""

from flask import Flask, render_template, request, jsonify
import os
import sys
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 确保必要的目录存在
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

@app.route('/')
def index():
    """主页"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCCW报价系统 - 基础版本</title>
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
            <h1>🎉 OCCW报价系统 - 基础版本</h1>
            
            <div class="version">
                <strong>部署版本:</strong> v2.2.0 - 基础版本<br>
                <strong>部署时间:</strong> 2025-01-29<br>
                <strong>构建步骤:</strong> 基础版本部署<br>
                <strong>当前时间:</strong> {current_time}
            </div>
            
            <div class="success">
                <h3>✅ 系统部署成功</h3>
                <p>OCCW报价系统基础版本已成功部署到Render</p>
            </div>
            
            <div class="info">
                <h3>📋 系统信息</h3>
                <p><strong>Python版本:</strong> {sys.version}</p>
                <p><strong>Flask版本:</strong> {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}</p>
                <p><strong>端口:</strong> {os.environ.get('PORT', '5000')}</p>
                <p><strong>环境:</strong> {os.environ.get('FLASK_ENV', 'production')}</p>
            </div>
            
            <div class="info">
                <h3>🔗 功能链接</h3>
                <ul>
                    <li><a href="/api/status">API状态</a></li>
                    <li><a href="/health">健康检查</a></li>
                    <li><a href="/test/packages">包状态测试</a></li>
                    <li><a href="/test/pdf">PDF功能测试</a></li>
                    <li><a href="/test/excel">Excel功能测试</a></li>
                </ul>
            </div>
            
            <div class="warning">
                <h3>⚠️ 当前功能</h3>
                <p>基础版本包含以下功能：</p>
                <ul>
                    <li>✅ Flask Web框架</li>
                    <li>✅ pandas数据处理</li>
                    <li>✅ numpy数值计算</li>
                    <li>✅ PyPDF2 PDF处理</li>
                    <li>✅ openpyxl Excel处理</li>
                    <li>⏳ 完整OCCW报价系统功能（待添加）</li>
                </ul>
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
        'message': 'OCCW报价系统基础版本运行正常',
        'python_version': sys.version,
        'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3',
        'port': os.environ.get('PORT', '5000'),
        'deploy_version': 'v2.2.0',
        'deploy_time': '2025-01-29',
        'build_step': '基础版本部署'
    })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'OCCW Quote System - Basic Version',
        'version': '2.2.0',
        'deploy_time': '2025-01-29'
    })

@app.route('/test/packages')
def test_packages():
    """包状态测试"""
    packages = {}
    
    # 测试Flask
    try:
        packages['flask'] = {'status': 'installed', 'version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}
    except ImportError:
        packages['flask'] = {'status': 'not_installed', 'error': 'Flask not available'}
    
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

@app.route('/test/pdf')
def test_pdf():
    """PDF功能测试"""
    try:
        import PyPDF2
        return jsonify({
            'status': 'success',
            'pypdf2_version': PyPDF2.__version__,
            'features': [
                'PDF文件读取',
                '文本内容提取',
                '页面信息获取',
                '元数据读取'
            ],
            'message': 'PyPDF2功能正常'
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'PyPDF2导入失败: {str(e)}'
        })

@app.route('/test/excel')
def test_excel():
    """Excel功能测试"""
    try:
        import openpyxl
        import pandas as pd
        return jsonify({
            'status': 'success',
            'openpyxl_version': openpyxl.__version__,
            'pandas_version': pd.__version__,
            'features': [
                'Excel文件读取',
                '工作表操作',
                '单元格读写',
                'DataFrame处理'
            ],
            'message': 'Excel处理功能正常'
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'Excel处理功能导入失败: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"启动基础OCCW报价系统，端口: {port}")
    print(f"Python版本: {sys.version}")
    print(f"Flask版本: {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}")
    print(f"部署版本: v2.2.0 - 基础版本")
    print(f"部署时间: 2025-01-29")
    app.run(host='0.0.0.0', port=port, debug=False) 