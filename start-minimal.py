#!/usr/bin/env python3
"""
启动脚本 - 明确启动最小化测试应用
"""

import os
import sys

# 确保使用正确的应用
if __name__ == '__main__':
    # 设置端口
    port = int(os.environ.get('PORT', 5000))
    
    # 导入并启动最小化应用
    from test_minimal import app
    
    print(f"启动最小化测试应用，端口: {port}")
    print("Python版本:", sys.version)
    
    app.run(host='0.0.0.0', port=port, debug=False) 