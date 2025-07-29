#!/usr/bin/env python3
"""
最小化测试应用 - 用于验证Render部署
只包含基本功能，避免复杂的依赖问题
"""

from flask import Flask, render_template_string, jsonify
import os

app = Flask(__name__)

# 简单的HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OCCW报价系统 - 测试版</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 20px; background: #f0f8ff; border-radius: 5px; margin: 20px 0; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>OCCW报价系统 - 部署测试</h1>
        
        <div class="status success">
            <h3>✅ 部署成功！</h3>
            <p>应用已成功部署到Render</p>
            <p>Python版本: {{ python_version }}</p>
            <p>Flask版本: {{ flask_version }}</p>
        </div>
        
        <div class="status">
            <h3>📋 功能状态</h3>
            <ul>
                <li>✅ 基础Web服务: 正常</li>
                <li>✅ Flask框架: 正常</li>
                <li>⏳ 数据处理: 待测试</li>
                <li>⏳ PDF处理: 待测试</li>
                <li>⏳ Excel处理: 待测试</li>
            </ul>
        </div>
        
        <div class="status">
            <h3>🔧 下一步</h3>
            <p>基础部署成功后，可以逐步添加完整功能：</p>
            <ol>
                <li>添加pandas和numpy支持</li>
                <li>添加PDF处理功能</li>
                <li>添加Excel处理功能</li>
                <li>部署完整应用</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    import sys
    import flask
    
    return render_template_string(HTML_TEMPLATE, 
                                python_version=sys.version,
                                flask_version=flask.__version__)

@app.route('/api/status')
def status():
    """状态API"""
    import sys
    import flask
    return jsonify({
        'status': 'success',
        'message': 'OCCW报价系统基础部署成功',
        'python_version': sys.version,
        'flask_version': flask.__version__
    })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 