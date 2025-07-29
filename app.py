#!/usr/bin/env python3
"""
OCCW报价系统 - 主应用
临时重定向到数据处理测试应用
"""

import sys
import os

# 临时重定向到数据处理测试应用
if __name__ == '__main__':
    print("重定向到数据处理测试应用...")
    os.system('python test-data-processing.py')
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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices
    
    # 获取过滤参数
    search_sku = request.args.get('search_sku', '').strip()
    door_variant = request.args.get('door_variant', '').strip()
    box_variant = request.args.get('box_variant', '').strip()
    category = request.args.get('category', '').strip()
    
    # 过滤数据
    filtered_data = occw_prices.copy()
    
    if search_sku:
        filtered_data = [item for item in filtered_data if search_sku.lower() in item.get('internal_ref', '').lower()]
    
    if door_variant:
        filtered_data = [item for item in filtered_data if door_variant.upper() in item.get('door_variant', '').upper()]
    
    if box_variant:
        filtered_data = [item for item in filtered_data if box_variant.upper() in item.get('box_variant', '').upper()]
    
    if category:
        filtered_data = [item for item in filtered_data if category.upper() in item.get('category', '').upper()]
    
    return jsonify(filtered_data)

@app.route('/get_price_filter_options')
def get_price_filter_options():
    global occw_prices
    
    door_variants = list(set([item.get('door_variant', '') for item in occw_prices if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in occw_prices if item.get('box_variant')]))
    categories = list(set([item.get('category', '') for item in occw_prices if item.get('category')]))
    
    return jsonify({
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants),
        'categories': sorted(categories)
    })

@app.route('/get_products_by_category')
def get_products_by_category():
    global occw_prices
    
    category = request.args.get('category', '').strip().upper()
    
    if not category:
        return jsonify({'products': [], 'door_variants': [], 'box_variants': []})
    
    # 从价格数据中提取产品信息
    category_data = [item for item in occw_prices if item.get('category', '').upper() == category]
    
    products = list(set([item.get('name', '') for item in category_data if item.get('name')]))
    door_variants = list(set([item.get('door_variant', '') for item in category_data if item.get('door_variant')]))
    box_variants = list(set([item.get('box_variant', '') for item in category_data if item.get('box_variant')]))
    
    # 如果没有找到数据，提供默认选项
    if not products and not door_variants and not box_variants:
        # 为某些类别提供默认产品选项
        if category == "ENDING PANEL":
            products = ['PANEL-24', 'PANEL-36', 'PANEL-48']
        elif category == "MOLDING":
            products = ['CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M']
        elif category == "TOE KICK":
            products = ['TOE-4.5', 'TOE-6', 'TOE-8']
        elif category == "FILLER":
            products = ['FILLER-3', 'FILLER-6', 'FILLER-9']
    
    return jsonify({
        'products': sorted(products),
        'door_variants': sorted(door_variants),
        'box_variants': sorted(box_variants)
    })

def generate_door_sku(product_name, door_variant):
    """生成门板SKU"""
    if not product_name or not door_variant:
        return ''
    
    return f"{door_variant}-{product_name}-Door"

def generate_box_sku(product_name, box_variant, door_variant):
    """生成柜体SKU"""
    if not product_name:
        return ''
    
    # 检查是否为开放柜体
    if 'OPEN' in product_name.upper():
        # 开放柜体：门板变体-产品名称
        if door_variant:
            # 如果产品名称已经包含-OPEN，不再添加
            if product_name.upper().endswith('-OPEN'):
                return f"{door_variant}-{product_name}"
            else:
                return f"{door_variant}-{product_name}-OPEN"
        else:
            return product_name
    else:
        # 标准柜体：柜身变体-产品名称-BOX
        if box_variant:
            return f"{box_variant}-{product_name}-BOX"
        else:
            return f"{product_name}-BOX"

def generate_sku_by_rules(category, product, box_variant, door_variant):
    """根据配置的规则生成SKU列表"""
    global sku_rules
    possible_skus = []
    
    # 使用配置的手动创建规则
    if 'manual_quote_rules' in sku_rules and 'rules' in sku_rules['manual_quote_rules']:
        for rule in sku_rules['manual_quote_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            rule_category = rule.get('category', '')
            condition = rule.get('condition', '')
            
            # 检查类别匹配
            if rule_category == category:
                # 检查条件
                if evaluate_sku_condition(condition, product, box_variant, door_variant):
                    sku_format = rule.get('sku_format', '')
                    special_handling = rule.get('special_handling', '')
                    
                    # 生成SKU
                    sku = apply_sku_format(sku_format, product, box_variant, door_variant, special_handling)
                    if sku:
                        possible_skus.append(sku)
                        
                    # 检查是否有备用格式
                    fallback = rule.get('fallback', '')
                    if fallback and not sku:
                        fallback_sku = apply_sku_format(fallback, product, box_variant, door_variant, special_handling)
                        if fallback_sku:
                            possible_skus.append(fallback_sku)
    
    # 回退到硬编码规则
    if category == 'Assm':
        sku = f"{product}-{box_variant}-{door_variant}"
        if sku != f"{product}--":
            possible_skus.append(sku)
    elif category == 'Door':
        sku = generate_door_sku(product, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'BOX':
        sku = generate_box_sku(product, box_variant, door_variant)
        if sku:
            possible_skus.append(sku)
    elif category == 'HARDWARE':
        possible_skus.append(product)
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU条件"""
    if condition == 'True':
        return True
    
    # 可以添加更复杂的条件评估逻辑
    return True

def apply_sku_format(sku_format, product, box_variant, door_variant, special_handling):
    """应用SKU格式"""
    if not sku_format:
        return ''
    
    sku = sku_format.replace('{product_name}', product or '')
    sku = sku.replace('{box_variant}', box_variant or '')
    sku = sku.replace('{door_variant}', door_variant or '')
    
    # 处理特殊逻辑
    if special_handling == 'remove_empty_parts':
        sku = sku.replace('--', '-').strip('-')
    
    return sku

@app.route('/search_sku_price')
def search_sku_price():
    global occw_prices
    
    sku = request.args.get('sku', '').strip()
    if not sku:
        return jsonify({'error': 'SKU不能为空'})
    
    # 使用规则生成可能的SKU
    possible_skus = generate_sku_by_rules('', '', '', '')
    
    # 在价格数据中搜索
    for item in occw_prices:
        if sku.lower() in item.get('internal_ref', '').lower():
            return jsonify({
                'found': True,
                'price': item.get('price', 0),
                'sku': item.get('internal_ref', ''),
                'name': item.get('name', ''),
                'category': item.get('category', '')
            })
    
    return jsonify({'found': False, 'message': '未找到匹配的SKU'})

@app.route('/rules')
def rules_page():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('rules.html')

@app.route('/get_sku_rules')
def get_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
def save_sku_rules_api():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        global sku_rules
        sku_rules = request.json
        save_sku_rules()
        return jsonify({'success': True, 'message': '规则保存成功'})
    except Exception as e:
        return jsonify({'error': f'保存失败: {str(e)}'})

@app.route('/reset_sku_rules', methods=['POST'])
def reset_sku_rules():
    if not session.get('admin'):
        return jsonify({'error': '未授权'})
    
    try:
        load_sku_rules()
        return jsonify({'success': True, 'message': '规则重置成功'})
    except Exception as e:
        return jsonify({'error': f'重置失败: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
"""

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
                            "condition": "name starts with letter or number",
                            "action": "keep",
                            "enabled": True
                        }
                    ]
                },
                "manual_quote_rules": {
                    "rules": [
                        {
                            "id": "assm_manual",
                            "category": "Assm",
                            "condition": "True",
                            "sku_format": "{product_name}-{box_variant}-{door_variant}",
                            "enabled": True
                        },
                        {
                            "id": "door_manual",
                            "category": "Door", 
                            "condition": "True",
                            "sku_format": "{door_variant}-{product_name}-Door",
                            "enabled": True
                        },
                        {
                            "id": "box_manual",
                            "category": "BOX",
                            "condition": "True",
                            "sku_format": "{box_variant}-{product_name}-BOX",
                            "enabled": True
                        },
                        {
                            "id": "hardware_manual",
                            "category": "HARDWARE",
                            "condition": "True", 
                            "sku_format": "{product_name}",
                            "enabled": True
                        }
                    ]
                },
                "common_variants": {
                    "door_variants": ["PB", "GSS", "BSS", "WSS", "SSW"],
                    "box_variants": ["PLY", "MDF", "PB", "GSS", "BSS", "WSS", "SSW"]
                }
            }
            save_sku_rules()
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        # 使用默认规则
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

# 初始化数据
load_occw_prices()
load_sku_mappings()

class OCCWPriceTransformer:
    def __init__(self):
        self.errors = []
        self.success_count = 0
        
    def transform_excel_file(self, file_path):
        """转换Excel文件为结构化数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            
            transformed_data = []
            self.errors = []
            self.success_count = 0
            
            # 逐行处理数据
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号从2开始（第1行是标题）
                transformed_row = self.transform_single_row(row, row_number)
                if transformed_row:
                    transformed_data.append(transformed_row)
                    self.success_count += 1
            
            return transformed_data
            
        except Exception as e:
            self.errors.append(f"文件处理失败: {str(e)}")
            return []
    
    def transform_single_row(self, row, row_number):
        """转换单行数据"""
        try:
            # 获取基础字段
            internal_ref = str(row.get('内部参考号', '')).strip()
            name = str(row.get('名称', '')).strip()
            category = str(row.get('产品类别/名称', '')).strip()
            variant = str(row.get('变体', '')).strip()
            price = str(row.get('价格', '')).strip()
            
            # 处理NaN值
            if internal_ref == 'nan': internal_ref = ''
            if name == 'nan': name = ''
            if category == 'nan': category = ''
            if variant == 'nan': variant = ''
            if price == 'nan': price = ''
            
            # 验证必需字段
            if not internal_ref:
                self.errors.append(f"第{row_number}行：内部参考号不能为空")
                return None
                
            if not name:
                self.errors.append(f"第{row_number}行：名称不能为空")
                return None
            
            # 验证名称格式：必须以英文字母或数字开头
            if not re.match(r'^[A-Za-z0-9]', name):
                self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
                return None
            
            # 标准化类别
            category = category.upper().strip()
            
            # 提取变体信息
            door_variant = ''
            box_variant = ''
            
            if category == 'ASSM' or category == '组合件':
                # 组合件：从名称中提取柜身变体
                door_variant, box_variant = self._extract_assm_variants(name, variant)
            elif category == 'DOOR' or category == '门板':
                door_variant = self._extract_door_variant(variant)
            elif category == 'BOX':
                # 检查是否为开放柜体
                if 'OPEN' in name.upper():
                    # 开放柜体：门板变体来自变体字段，柜身变体为空
                    door_variant = self._extract_door_variant(variant)
                    box_variant = ''
                else:
                    # 标准柜体：柜身变体来自变体字段
                    box_variant = self._extract_box_variant(variant)
            else:
                # 其他类别：尝试从变体字段提取
                door_variant = self._extract_door_variant(variant)
                box_variant = self._extract_box_variant(variant)
            
            # 处理价格
            try:
                price_value = float(price) if price else 0.0
            except ValueError:
                price_value = 0.0
                self.errors.append(f"第{row_number}行：价格格式错误 '{price}'")
            
            # 构建转换后的数据
            transformed_row = {
                'internal_ref': internal_ref,
                'name': name,
                'category': category,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'price': price_value,
                'original_variant': variant
            }
            
            return transformed_row
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：处理失败 - {str(e)}")
            return None
    
    def _extract_door_variant(self, variant):
        """从变体字段提取门板变体"""
        if not variant:
            return ''
        
        # 常见的门板变体
        door_variants = ['PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for door_var in door_variants:
            if door_var in variant.upper():
                return door_var
        
        return ''
    
    def _extract_box_variant(self, variant):
        """从变体字段提取柜身变体"""
        if not variant:
            return ''
        
        # 常见的柜身变体
        box_variants = ['PLY', 'MDF', 'PB', 'GSS', 'BSS', 'WSS', 'SSW']
        
        for box_var in box_variants:
            if box_var in variant.upper():
                return box_var
        
        return ''
    
    def _extract_assm_variants(self, name, variant):
        """从组合件名称和变体中提取门板和柜身变体"""
        door_variant = ''
        box_variant = ''
        
        # 从名称中提取柜身变体（名称中"-"前面的部分）
        if '-' in name:
            box_variant = name.split('-')[0].strip()
        
        # 从变体字段提取门板变体
        door_variant = self._extract_door_variant(variant)
        
        return door_variant, box_variant

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
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
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
            
            # 生成SKU
            sku_list = generate_sku(content)
            
            return jsonify({
                'success': True,
                'sku_list': sku_list,
                'content': content[:1000] + '...' if len(content) > 1000 else content
            })
            
        except Exception as e:
            return jsonify({'error': f'PDF处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

def generate_sku(content):
    """根据PDF内容生成SKU列表"""
    global sku_rules
    
    sku_list = []
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            # 这里可以根据规则和内容生成SKU
            # 简化版本：基于关键词匹配
            condition = rule.get('condition', '')
            sku_format = rule.get('sku_format', '')
            
            if 'Door' in condition and 'Door' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleDoor').replace('{door_variant}', 'PB'))
            elif 'BOX' in condition and 'BOX' in content:
                sku_list.append(sku_format.replace('{product_name}', 'SampleBox').replace('{box_variant}', 'PLY'))
    
    return sku_list

@app.route('/upload_occw_prices', methods=['POST'])
def upload_occw_prices():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file and file.filename.endswith('.xlsx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)
        
        try:
            # 转换Excel数据
            transformer = OCCWPriceTransformer()
            transformed_data = transformer.transform_excel_file(filepath)
            
            # 更新全局数据
            global occw_prices
            occw_prices = transformed_data
            save_occw_prices()
            
            return jsonify({
                'success': True,
                'message': f'成功导入 {transformer.success_count} 条记录',
                'errors': transformer.errors,
                'data_count': len(transformed_data)
            })
            
        except Exception as e:
            return jsonify({'error': f'Excel处理失败: {str(e)}'})
    
    return jsonify({'error': '不支持的文件格式'})

@app.route('/get_occw_price_table')
def get_occw_price_table():
    global occw_prices