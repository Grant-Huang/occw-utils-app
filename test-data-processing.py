#!/usr/bin/env python3
"""
测试数据处理功能 - 包含pandas和numpy
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    """主页"""
    try:
        import pandas as pd
        import numpy as np
        
        # 测试数据处理功能
        test_data = {
            'name': ['Product A', 'Product B', 'Product C'],
            'price': [100, 200, 150],
            'quantity': [10, 5, 8]
        }
        df = pd.DataFrame(test_data)
        total_value = np.sum(df['price'] * df['quantity'])
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OCCW报价系统 - 数据处理测试</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .success {{ color: #155724; background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .data {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 OCCW报价系统 - 数据处理测试</h1>
                
                <div class="success">
                    <h3>✅ 数据处理功能验证通过</h3>
                    <p>pandas和numpy已成功安装并正常工作</p>
                </div>
                
                <div class="info">
                    <h3>📋 系统信息</h3>
                    <p><strong>Python版本:</strong> {sys.version}</p>
                    <p><strong>Flask版本:</strong> {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}</p>
                    <p><strong>pandas版本:</strong> {pd.__version__}</p>
                    <p><strong>numpy版本:</strong> {np.__version__}</p>
                    <p><strong>端口:</strong> {os.environ.get('PORT', '5000')}</p>
                </div>
                
                <div class="data">
                    <h3>📊 数据处理测试</h3>
                    <p><strong>测试数据:</strong></p>
                    <pre>{df.to_string()}</pre>
                    <p><strong>总价值计算:</strong> ${total_value}</p>
                    <p><strong>pandas功能:</strong> ✅ DataFrame创建和操作</p>
                    <p><strong>numpy功能:</strong> ✅ 数值计算</p>
                </div>
                
                <div class="info">
                    <h3>🔗 测试链接</h3>
                    <ul>
                        <li><a href="/api/status">API状态</a></li>
                        <li><a href="/health">健康检查</a></li>
                        <li><a href="/test/pandas">pandas测试</a></li>
                        <li><a href="/test/numpy">numpy测试</a></li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>🚀 下一步</h3>
                    <p>数据处理功能验证成功后，可以继续添加：</p>
                    <ol>
                        <li>✅ 数据处理功能 (pandas, numpy) - <strong>已完成</strong></li>
                        <li>⏳ PDF处理功能 (PyPDF2)</li>
                        <li>⏳ Excel处理功能 (openpyxl)</li>
                        <li>⏳ 部署完整OCCW报价系统</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
    except ImportError as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OCCW报价系统 - 数据处理测试</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error {{ color: #721c24; background: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ 数据处理功能测试失败</h1>
                <div class="error">
                    <h3>导入错误</h3>
                    <p>无法导入pandas或numpy: {str(e)}</p>
                    <p>请检查requirements.txt和构建命令</p>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/api/status')
def status():
    """状态API"""
    try:
        import pandas as pd
        import numpy as np
        return jsonify({
            'status': 'success',
            'message': 'OCCW报价系统数据处理功能正常',
            'python_version': sys.version,
            'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3',
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__,
            'port': os.environ.get('PORT', '5000')
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'数据处理功能导入失败: {str(e)}',
            'python_version': sys.version,
            'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'
        })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'OCCW Quote System - Data Processing',
        'version': '1.1.0'
    })

@app.route('/test/pandas')
def test_pandas():
    """pandas测试"""
    try:
        import pandas as pd
        test_data = {'test': [1, 2, 3]}
        df = pd.DataFrame(test_data)
        return jsonify({
            'status': 'success',
            'pandas_version': pd.__version__,
            'test_data': df.to_dict('records')
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'pandas导入失败: {str(e)}'
        })

@app.route('/test/numpy')
def test_numpy():
    """numpy测试"""
    try:
        import numpy as np
        test_array = np.array([1, 2, 3, 4, 5])
        return jsonify({
            'status': 'success',
            'numpy_version': np.__version__,
            'test_array': test_array.tolist(),
            'sum': np.sum(test_array).item()
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'numpy导入失败: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"启动数据处理测试应用，端口: {port}")
    print(f"Python版本: {sys.version}")
    print(f"Flask版本: {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}")
    app.run(host='0.0.0.0', port=port, debug=False) 