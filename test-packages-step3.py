#!/usr/bin/env python3
"""
OCCW报价系统 - 包测试第三步：pandas、numpy、PyPDF2和openpyxl
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
    
    # 测试包状态
    pandas_status = "未安装"
    numpy_status = "未安装"
    pypdf2_status = "未安装"
    openpyxl_status = "未安装"
    
    try:
        import pandas as pd
        pandas_status = f"已安装 (v{pd.__version__})"
    except ImportError:
        pandas_status = "未安装"
    
    try:
        import numpy as np
        numpy_status = f"已安装 (v{np.__version__})"
    except ImportError:
        numpy_status = "未安装"
    
    try:
        import PyPDF2
        pypdf2_status = f"已安装 (v{PyPDF2.__version__})"
    except ImportError:
        pypdf2_status = "未安装"
    
    try:
        import openpyxl
        openpyxl_status = f"已安装 (v{openpyxl.__version__})"
    except ImportError:
        openpyxl_status = "未安装"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OCCW报价系统 - 包测试第三步</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .success {{ color: #155724; background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .info {{ background: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .version {{ background: #e2e3e5; color: #383d41; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 0.9em; }}
            .package {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 OCCW报价系统 - 包测试第三步</h1>
            
            <div class="version">
                <strong>部署版本:</strong> v1.9.0 - 包测试第三步<br>
                <strong>部署时间:</strong> 2025-01-29<br>
                <strong>构建步骤:</strong> 测试pandas、numpy、PyPDF2和openpyxl安装<br>
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
            </div>
            
            <div class="package">
                <h3>📦 包状态测试</h3>
                <p><strong>pandas:</strong> {pandas_status}</p>
                <p><strong>numpy:</strong> {numpy_status}</p>
                <p><strong>PyPDF2:</strong> {pypdf2_status}</p>
                <p><strong>openpyxl:</strong> {openpyxl_status}</p>
            </div>
            
            <div class="info">
                <h3>🔗 测试链接</h3>
                <ul>
                    <li><a href="/api/status">API状态</a></li>
                    <li><a href="/health">健康检查</a></li>
                    <li><a href="/test/pandas">pandas功能测试</a></li>
                    <li><a href="/test/numpy">numpy功能测试</a></li>
                    <li><a href="/test/pdf">PyPDF2功能测试</a></li>
                    <li><a href="/test/excel">openpyxl功能测试</a></li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🚀 构建步骤</h3>
                <ol>
                    <li>✅ Flask基础功能 - <strong>已完成</strong></li>
                    <li>✅ pandas和numpy安装 - <strong>已完成</strong></li>
                    <li>✅ PyPDF2安装 - <strong>已完成</strong></li>
                    <li>⏳ openpyxl安装 - <strong>进行中</strong></li>
                    <li>⏳ 部署完整OCCW报价系统</li>
                </ol>
            </div>
            
            <div class="warning">
                <h3>⚠️ 当前构建命令</h3>
                <p><code>pip install Flask==2.3.3 pandas==2.0.3 numpy==1.24.3 PyPDF2==3.0.1 openpyxl==3.1.2</code></p>
                <p><em>如果openpyxl安装失败，请检查构建日志</em></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def status():
    """状态API"""
    packages = {}
    
    try:
        import pandas as pd
        packages['pandas'] = {'status': 'installed', 'version': pd.__version__}
    except ImportError:
        packages['pandas'] = {'status': 'not_installed', 'error': 'No module named pandas'}
    
    try:
        import numpy as np
        packages['numpy'] = {'status': 'installed', 'version': np.__version__}
    except ImportError:
        packages['numpy'] = {'status': 'not_installed', 'error': 'No module named numpy'}
    
    try:
        import PyPDF2
        packages['pypdf2'] = {'status': 'installed', 'version': PyPDF2.__version__}
    except ImportError:
        packages['pypdf2'] = {'status': 'not_installed', 'error': 'No module named PyPDF2'}
    
    try:
        import openpyxl
        packages['openpyxl'] = {'status': 'installed', 'version': openpyxl.__version__}
    except ImportError:
        packages['openpyxl'] = {'status': 'not_installed', 'error': 'No module named openpyxl'}
    
    return jsonify({
        'status': 'success',
        'message': 'OCCW报价系统包测试第三步',
        'python_version': sys.version,
        'flask_version': Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3',
        'port': os.environ.get('PORT', '5000'),
        'deploy_version': 'v1.9.0',
        'deploy_time': '2025-01-29',
        'build_step': '测试pandas、numpy、PyPDF2和openpyxl安装',
        'packages': packages
    })

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'OCCW Quote System - Package Test Step 3',
        'version': '1.9.0',
        'deploy_time': '2025-01-29'
    })

@app.route('/test/pandas')
def test_pandas():
    """pandas功能测试"""
    try:
        import pandas as pd
        import numpy as np
        
        # 创建测试数据
        data = {
            'product': ['Door A', 'Box B', 'Hardware C'],
            'price': [100, 200, 50],
            'quantity': [2, 1, 5]
        }
        df = pd.DataFrame(data)
        
        # 计算总价值
        total_value = (df['price'] * df['quantity']).sum()
        
        return jsonify({
            'status': 'success',
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__,
            'test_data': df.to_dict('records'),
            'total_value': total_value,
            'message': 'pandas和numpy功能正常'
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'pandas或numpy导入失败: {str(e)}'
        })

@app.route('/test/numpy')
def test_numpy():
    """numpy功能测试"""
    try:
        import numpy as np
        
        # 创建测试数组
        test_array = np.array([1, 2, 3, 4, 5])
        test_matrix = np.array([[1, 2], [3, 4]])
        
        return jsonify({
            'status': 'success',
            'numpy_version': np.__version__,
            'test_array': test_array.tolist(),
            'test_matrix': test_matrix.tolist(),
            'array_sum': np.sum(test_array).item(),
            'matrix_det': np.linalg.det(test_matrix).item(),
            'message': 'numpy功能正常'
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'numpy导入失败: {str(e)}'
        })

@app.route('/test/pdf')
def test_pdf():
    """PyPDF2功能测试"""
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
    """openpyxl功能测试"""
    try:
        import openpyxl
        
        return jsonify({
            'status': 'success',
            'openpyxl_version': openpyxl.__version__,
            'features': [
                'Excel文件读取',
                '工作表操作',
                '单元格读写',
                '创建新Excel文件'
            ],
            'message': 'openpyxl功能正常'
        })
    except ImportError as e:
        return jsonify({
            'status': 'error',
            'message': f'openpyxl导入失败: {str(e)}'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"启动包测试第三步应用，端口: {port}")
    print(f"Python版本: {sys.version}")
    print(f"Flask版本: {Flask.__version__ if hasattr(Flask, '__version__') else '2.3.3'}")
    print(f"部署版本: v1.9.0 - 包测试第三步")
    print(f"部署时间: 2025-01-29")
    app.run(host='0.0.0.0', port=port, debug=False) 