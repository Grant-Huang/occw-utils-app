#!/usr/bin/env python3
"""
最简单的测试应用 - 只包含Flask基础功能
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    """主页"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCCW报价系统 - 部署测试</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #155724; background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 OCCW报价系统 - 部署成功！</h1>
            
            <div class="success">
                <h3>✅ 基础部署验证通过</h3>
                <p>Flask应用已成功部署到Render</p>
            </div>
            
            <div class="info">
                <h3>📋 系统信息</h3>
                <p><strong>Python版本:</strong> {sys.version}</p>
                <p><strong>Flask版本:</strong> {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}</p>
                <p><strong>端口:</strong> {os.environ.get('PORT', '5000')}</p>
            </div>
            
            <div class="info">
                <h3>🔗 测试链接</h3>
                <ul>
                    <li><a href="/api/status">API状态</a></li>
                    <li><a href="/health">健康检查</a></li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🚀 下一步</h3>
                <p>基础功能验证成功后，可以逐步添加完整功能：</p>
                <ol>
                    <li>添加数据处理功能 (pandas, numpy)</li>
                    <li>添加PDF处理功能 (PyPDF2)</li>
                    <li>添加Excel处理功能 (openpyxl)</li>
                    <li>部署完整OCCW报价系统</li>
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
        'message': 'OCCW报价系统基础部署成功',
        'python_version': sys.version,
        'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3',
        'port': os.environ.get('PORT', '5000')
    })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'OCCW Quote System',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"启动简单测试应用，端口: {port}")
    print(f"Python版本: {sys.version}")
    print(f"Flask版本: {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}")
    app.run(host='0.0.0.0', port=port, debug=False) 