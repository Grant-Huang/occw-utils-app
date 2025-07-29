#!/usr/bin/env python3
"""
OCCW报价系统 - 主应用
临时重定向到数据处理测试应用
"""

import sys
import os

# 临时重定向到数据处理测试应用
if __name__ == '__main__':
    print("重定向到版本测试应用...")
    os.system('python test-simple-with-version.py')
    sys.exit(0)

# 原始应用代码（暂时注释掉）
"""
import PyPDF2
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import os
import json
import re
from datetime import datetime
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 确保必要的目录存在
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

# 全局变量
occw_prices = []
sku_mappings = {}
sku_rules = {}

# 加载SKU规则
def load_sku_rules():
    global sku_rules
    try:
        # 首先尝试从data目录加载
        if os.path.exists('data/sku_rules.json'):
            with open('data/sku_rules.json', 'r', encoding='utf-8') as f:
                sku_rules = json.load(f)
        # 如果不存在，尝试从根目录加载
        elif os.path.exists('sku_rules.json'):
            with open('sku_rules.json', 'r', encoding='utf-8') as f:
                sku_rules = json.load(f)
        else:
            # 创建默认规则
            sku_rules = {
                "pdf_parsing_rules": {
                    "rules": [
                        {
                            "id": "assm_rule",
                            "condition": "category == 'Assm'",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_rule", 
                            "condition": "category == 'Door'",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_rule",
                            "condition": "category == 'BOX' and 'OPEN' in product_name",
                            "sku_format": "{door_variant}-{product_name}",
                            "enabled": True
                        },
                        {
                            "id": "box_standard_rule",
                            "condition": "category == 'BOX' and 'OPEN' not in product_name",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_rule",
                            "condition": "category == 'HARDWARE'",
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "occw_import_rules": {
                    "rules": [
                        {
                            "id": "name_filter",
                            "condition": "name starts with English letter or number",
                            "action": "include",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "door_sku_rule",
                            "condition": "category == 'Door'",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_standard_sku_rule",
                            "condition": "category == 'BOX' and box_variant is not empty",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "box_open_sku_rule",
                            "condition": "category == 'BOX' and door_variant is not empty and box_variant is empty",
                            "sku_format": "{door_variant}-{product_name}-OPEN",
                            "enabled": True
                        },
                        {
                            "id": "hardware_sku_rule",
                            "condition": "category == 'HARDWARE'",
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                }
            }
            # 保存默认规则
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        sku_rules = {}

def save_sku_rules():
    """保存SKU规则到文件"""
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/sku_rules.json', 'w', encoding='utf-8') as f:
            json.dump(sku_rules, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存SKU规则失败: {e}")

# 初始化时加载规则
load_sku_rules()

# 加载价格数据
def load_occw_prices():
    global occw_prices
    try:
        if os.path.exists('data/occw_prices.json'):
            with open('data/occw_prices.json', 'r', encoding='utf-8') as f:
                occw_prices = json.load(f)
    except Exception as e:
        print(f"加载价格数据失败: {e}")
        occw_prices = []

# 保存价格数据
def save_occw_prices():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/occw_prices.json', 'w', encoding='utf-8') as f:
            json.dump(occw_prices, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存价格数据失败: {e}")

# 加载SKU映射
def load_sku_mappings():
    global sku_mappings
    try:
        if os.path.exists('data/sku_mappings.json'):
            with open('data/sku_mappings.json', 'r', encoding='utf-8') as f:
                sku_mappings = json.load(f)
    except Exception as e:
        print(f"加载SKU映射失败: {e}")
        sku_mappings = {}

# 保存SKU映射
def save_sku_mappings():
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/sku_mappings.json', 'w', encoding='utf-8') as f:
            json.dump(sku_mappings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存SKU映射失败: {e}")

# 初始化时加载数据
load_occw_prices()
load_sku_mappings()

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prices')
def prices():
    return render_template('prices.html')

@app.route('/sku_mappings')
def sku_mappings_page():
    return render_template('sku_mappings.html')

@app.route('/config')
def config():
    return render_template('config.html')

@app.route('/help')
def help():
    return render_template('help.html')

# API路由
@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 解析PDF内容
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text()
            
            # 保存PDF内容到文件
            with open('pdf_content.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return jsonify({
                'success': True,
                'message': 'PDF上传成功',
                'content': text_content[:1000] + '...' if len(text_content) > 1000 else text_content
            })
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
        finally:
            # 清理上传的文件
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({'error': '请上传PDF文件'})

@app.route('/api/parse_pdf', methods=['POST'])
def parse_pdf():
    try:
        with open('pdf_content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析PDF内容
        lines = content.split('\n')
        products = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析产品信息
            parts = line.split()
            if len(parts) >= 3:
                try:
                    # 尝试解析价格
                    price = float(parts[-1])
                    product_name = ' '.join(parts[:-1])
                    
                    products.append({
                        'name': product_name,
                        'price': price
                    })
                except ValueError:
                    continue
        
        return jsonify({
            'success': True,
            'products': products
        })
    except Exception as e:
        return jsonify({'error': f'解析失败: {str(e)}'})

@app.route('/api/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'excel_file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 读取Excel文件
            df = pd.read_excel(filepath)
            
            # 处理数据
            processed_data = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 检查产品名称是否以英文字母或数字开头
                    name = str(row.get('名称', '')).strip()
                    if not name or not re.match(r'^[a-zA-Z0-9]', name):
                        continue
                    
                    # 提取产品信息
                    product_info = {
                        'internal_ref': str(row.get('内部参考号', '')).strip(),
                        'name': name,
                        'category': str(row.get('产品类别/名称', '')).strip(),
                        'variant': str(row.get('变体', '')).strip(),
                        'price': float(row.get('价格', 0))
                    }
                    
                    # 生成SKU
                    sku = generate_sku(product_info)
                    product_info['sku'] = sku
                    
                    processed_data.append(product_info)
                    
                except Exception as e:
                    errors.append(f"第{index+1}行处理失败: {str(e)}")
                    continue
            
            # 更新全局数据
            global occw_prices
            occw_prices = processed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入{len(processed_data)}个产品',
                'errors': errors,
                'data': processed_data[:10]  # 返回前10个产品作为预览
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
        finally:
            # 清理上传的文件
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({'error': '请上传Excel文件'})

def generate_sku(product_info):
    """根据产品信息生成SKU"""
    name = product_info['name']
    category = product_info['category']
    variant = product_info['variant']
    
    # 应用SKU规则
    if category == 'Door':
        return f"{variant}-{name}-Door"
    elif category == 'BOX':
        if 'OPEN' in name:
            return f"{variant}-{name}"
        else:
            return f"{variant}-{name}-BOX"
    elif category == 'HARDWARE':
        return name
    else:
        return name

@app.route('/api/get_occw_price_table')
def get_occw_price_table():
    return jsonify({
        'data': occw_prices
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
""" 