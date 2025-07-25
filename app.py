import os
import re
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
import PyPDF2
import pandas as pd
from datetime import datetime
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from functools import wraps
from version import VERSION, VERSION_NAME, COMPANY_NAME_ZH, COMPANY_NAME_EN, SYSTEM_NAME_ZH, SYSTEM_NAME_EN, SYSTEM_NAME_FR
from translations import TRANSLATIONS, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, get_text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 管理员配置
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # 支持环境变量
ADMIN_SESSION_KEY = "is_admin"

# 语言支持
def get_current_language():
    """获取当前语言"""
    return session.get('language', DEFAULT_LANGUAGE)

def set_language(lang):
    """设置语言"""
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        return True
    return False

@app.context_processor
def inject_globals():
    """向模板注入全局变量"""
    current_lang = get_current_language()
    return {
        'current_language': current_lang,
        'supported_languages': SUPPORTED_LANGUAGES,
        'version': VERSION,
        'version_name': VERSION_NAME,
        'company_name_zh': COMPANY_NAME_ZH,
        'company_name_en': COMPANY_NAME_EN,
        'system_name_zh': SYSTEM_NAME_ZH,
        'system_name_en': SYSTEM_NAME_EN,
        'system_name_fr': SYSTEM_NAME_FR,
        't': lambda key: get_text(key, current_lang)
    }

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get(ADMIN_SESSION_KEY):
            # 检查是否是Ajax请求
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.headers.get('Content-Type', '').startswith('application/json') or
                request.is_json or
                (request.method in ['POST', 'PUT', 'DELETE'] and 
                 request.content_type and 'json' in request.content_type) or
                # 检查Accept头部是否主要接受JSON
                ('application/json' in request.headers.get('Accept', '') and 
                 'text/html' not in request.headers.get('Accept', ''))
            )
            
            if is_ajax:
                # 对Ajax请求返回401状态码
                return jsonify({'error': '需要管理员权限', 'redirect': '/admin_login'}), 401
            else:
                # 对普通请求进行重定向
                next_page = request.url if request.method == 'GET' else None
                return redirect(url_for('admin_login', next=next_page))
        return f(*args, **kwargs)
    return decorated_function

def is_admin():
    """检查当前用户是否为管理员"""
    return session.get(ADMIN_SESSION_KEY, False)

os.makedirs('data', exist_ok=True)

# 全局变量存储数据
standard_prices = {}
occw_prices = {}  # OCCW价格表
sku_mappings = {}  # SKU映射关系：{原SKU: 用户选择的SKU}
sku_rules = {
    'cabinet_rule': 'OCCW编码去掉"-L"和"-R"，SKU=OCCW编码&"-PLY-"&花色',
    'hardware_rule': 'SKU="HW-"&User Code',
    'accessory_rule': 'SKU=花色&"-"&User Code',
    'default_rule': 'SKU=花色&"-"&User Code'
}

def load_standard_prices():
    """加载标准价格表"""
    global standard_prices
    try:
        if os.path.exists('data/standard_prices.json'):
            with open('data/standard_prices.json', 'r', encoding='utf-8') as f:
                standard_prices = json.load(f)
    except Exception as e:
        print(f"加载标准价格表失败: {e}")
        standard_prices = {}

def save_standard_prices():
    """保存标准价格表"""
    try:
        with open('data/standard_prices.json', 'w', encoding='utf-8') as f:
            json.dump(standard_prices, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存标准价格表失败: {e}")

def load_occw_prices():
    """加载OCCW价格表"""
    global occw_prices
    try:
        if os.path.exists('data/occw_prices.json'):
            with open('data/occw_prices.json', 'r', encoding='utf-8') as f:
                occw_prices = json.load(f)
                print(f"已加载 {len(occw_prices)} 个OCCW价格")
    except Exception as e:
        print(f"加载OCCW价格表失败: {e}")
        occw_prices = {}

def save_occw_prices():
    """保存OCCW价格表"""
    try:
        with open('data/occw_prices.json', 'w', encoding='utf-8') as f:
            json.dump(occw_prices, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存OCCW价格表失败: {e}")
        return False

def load_sku_mappings():
    """加载SKU映射关系"""
    global sku_mappings
    try:
        if os.path.exists('data/sku_mappings.json'):
            with open('data/sku_mappings.json', 'r', encoding='utf-8') as f:
                sku_mappings = json.load(f)
                print(f"已加载 {len(sku_mappings)} 个SKU映射关系")
    except Exception as e:
        print(f"加载SKU映射关系失败: {e}")
        sku_mappings = {}

def save_sku_mappings():
    """保存SKU映射关系"""
    try:
        with open('data/sku_mappings.json', 'w', encoding='utf-8') as f:
            json.dump(sku_mappings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存SKU映射关系失败: {e}")
        return False

def load_sku_rules():
    """加载SKU规则配置"""
    global sku_rules
    try:
        if os.path.exists('data/sku_rules.json'):
            with open('data/sku_rules.json', 'r', encoding='utf-8') as f:
                sku_rules = json.load(f)
    except Exception as e:
        print(f"加载SKU规则失败: {e}")

def save_sku_rules():
    """保存SKU规则配置"""
    try:
        with open('data/sku_rules.json', 'w', encoding='utf-8') as f:
            json.dump(sku_rules, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存SKU规则失败: {e}")

def extract_pdf_content(pdf_path, add_page_markers=True, force_line_split=True):
    """提取PDF文件内容，支持强制将页脚和表头分行"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if add_page_markers:
                    text += f"\n=== PAGE {page_num + 1} ===\n"
                text += page_text
                if add_page_markers:
                    text += "\n"
            if force_line_split:
                # 强制将页脚和表头分行
                # 页脚: Print date: ... Page ... /
                text = re.sub(r'(Print date: ?\d+ ?\d{4}-\d{2}-\d{2} Page ?\d+ ?/)', r'\n\1\n', text)
                # 表头: Description Manuf. code # Qty User code
                text = re.sub(r'(Description Manuf\. code # Qty User code)', r'\n\1\n', text)
            return text
    except Exception as e:
        print(f"PDF解析失败: {e}")
        return ""

def parse_quotation_pdf(pdf_content):
    """解析报价单PDF内容 - 严格区分Manuf. code是否以数字开头，准确提取数量和用户编码，并比对PDF合计金额"""
    products = []
    current_door_color = None
    pdf_total = None
    compare_result = None
    compare_message = ''
    
    lines = pdf_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 识别PDF合计金额
        if 'OPWM_1 Net Total' in line:
            all_amounts = re.findall(r'([\$￥]?[0-9,]+\.\d{2})', line)
            if all_amounts:
                pdf_total = float(all_amounts[-1].replace('$','').replace('￥','').replace(',',''))
        
        # 查找door color
        if 'door color' in line.lower():
            door_match = re.search(r'door\s+color\s+\d+\s+([A-Z]+)', line)
            if door_match:
                current_door_color = door_match.group(1)
        
        # 检测多行产品格式（如 WF330 FOR）
        if (len(line) < 30 and 
            re.search(r'[A-Z]+\d+\s+FOR|WF330\s+FOR', line) and 
            not re.search(r'\d+\.\d{2}', line)):
            
            # 尝试合并接下来的行形成完整的产品信息
            multiline_result = parse_multiline_product_sequence(lines, i, current_door_color)
            if multiline_result:
                products.append(multiline_result['product'])
                i = multiline_result['next_index']
                continue
        
        # 查找单行产品
        if re.match(r'^[A-Z0-9]', line) and re.search(r'\d+\.\d{2}', line):
            if (line.startswith('Style') or line.startswith('Door') or 
                line.startswith('Cabinet') or line.startswith('Cabinets') or 
                line.startswith('Print') or line.startswith('Volume')):
                i += 1
                continue
            parts = line.split()
            if len(parts) >= 5:
                manuf_code = parts[0]
                seq_num = parts[1]
                price_index = -1
                for j, part in enumerate(parts):
                    if re.match(r'^\d+,?\d*\.\d{2}$', part):
                        price_index = j
                        break
                if price_index > 0:
                    description = ' '.join(parts[2:price_index])
                    price = parts[price_index]
                    last_col = parts[price_index + 1] if price_index + 1 < len(parts) else '1'
                    # 处理*号
                    if seq_num.startswith('*'):
                        description = '* ' + description
                        seq_num = seq_num[1:]
                    # 根据Manuf. code是否以数字开头来解析数量和user code
                    if re.match(r'^\d', manuf_code):
                        # 情况1: Manuf. code以数字开头（如3DB30）
                        user_code_final = manuf_code
                        if last_col.endswith(user_code_final):
                            qty_part = last_col[:-len(user_code_final)]
                            if qty_part and qty_part.isdigit():
                                qty = qty_part
                            else:
                                qty = '1'
                        else:
                            qty = '1'
                    else:
                        # 情况2: Manuf. code不以数字开头（如B30）
                        qty_match = re.match(r'^(\d+)(.*)$', last_col)
                        if qty_match:
                            qty = qty_match.group(1)
                            remaining_part = qty_match.group(2)
                            if remaining_part and re.match(r'^[A-Z0-9-]+$', remaining_part):
                                user_code_final = remaining_part
                            else:
                                user_code_final = manuf_code
                        else:
                            qty = '1'
                            user_code_final = manuf_code
                    # 生成SKU（包含映射处理）
                    sku = generate_final_sku(user_code_final, description, current_door_color)
                    # 获取标准价格并计算单价
                    try:
                        total_price_float = float(price.replace(',', ''))
                        qty_int = int(qty) if qty.isdigit() and int(qty) > 0 else 1
                        unit_price_calculated = total_price_float / qty_int
                        # 优先使用标准价格表中的单价，如果没有则使用计算出的单价
                        standard_price = standard_prices.get(sku, unit_price_calculated)
                    except ValueError:
                        standard_price = standard_prices.get(sku, 0.0)
                    product = {
                        'seq_num': seq_num,
                        'manuf_code': manuf_code,
                        'sku': sku,
                        'qty': qty,
                        'door_color': current_door_color or 'N/A',
                        'unit_price': standard_price,
                        'user_code': user_code_final,
                        'description': description
                    }
                    products.append(product)
        
        i += 1
    # 计算解析产品的总价
    # 现在unit_price是真正的单价，所以需要乘以数量
    calc_total = 0
    for p in products:
        try:
            qty = int(p['qty']) if str(p['qty']).isdigit() else 0
            unit_price = float(p['unit_price']) if p['unit_price'] is not None else 0
            calc_total += qty * unit_price
        except Exception:
            continue
    if pdf_total is not None:
        if abs(calc_total - pdf_total) < 0.01:
            compare_result = True
            compare_message = f"✅ 解析总价与PDF合计金额一致: {calc_total:.2f}"
        else:
            compare_result = False
            compare_message = f"❌ 解析总价({calc_total:.2f})与PDF合计金额({pdf_total:.2f})不一致，请检查解析逻辑或PDF内容！"
    else:
        compare_result = None
        compare_message = "⚠️ 未识别到PDF合计金额，无法比对！"
    def extract_seq_num(seq_str):
        try:
            return int(seq_str.replace('*', ''))
        except ValueError:
            return 0
    products.sort(key=lambda x: extract_seq_num(x['seq_num']))
    return products, compare_result, compare_message

def parse_multiline_product_sequence(lines, start_index, current_door_color):
    """解析多行产品序列，返回合并后的产品信息"""
    
    # 收集候选行
    candidate_lines = []
    i = start_index
    
    # 最多向前看3行
    while i < len(lines) and i < start_index + 3:
        line = lines[i].strip()
        if line:
            candidate_lines.append(line)
            
            # 如果这一行包含价格，可能是完整的产品信息
            if re.search(r'\d+\.\d{2}', line):
                merged_text = ' '.join(candidate_lines)
                parsed = parse_multiline_product_correctly(merged_text, current_door_color)
                
                if parsed:
                    return {
                        'product': parsed,
                        'next_index': i + 1
                    }
        i += 1
    
    return None

def parse_multiline_product_correctly(merged_text, current_door_color):
    """正确解析多行产品格式"""
    
    parts = merged_text.split()
    if len(parts) < 6:
        return None
    
    # 找到价格位置
    price_index = -1
    for i, part in enumerate(parts):
        if re.match(r'^\d+\.\d{2}$', part):
            price_index = i
            break
    
    if price_index == -1:
        return None
    
    price = parts[price_index]
    
    # 价格后面：数量 + 制造编码
    after_price = parts[price_index + 1:]
    if not after_price:
        return None
    
    qty_match = re.match(r'^(\d+)', after_price[0])
    if not qty_match:
        return None
    
    qty = qty_match.group(1)
    
    # 制造编码
    remaining_after_qty = after_price[0][len(qty):]
    if remaining_after_qty:
        manuf_code_parts = [remaining_after_qty] + after_price[1:]
    else:
        manuf_code_parts = after_price[1:]
    
    manuf_code = ' '.join(manuf_code_parts)
    
    # 价格前面的部分：用户编码 + 序号+描述
    before_price = parts[:price_index]
    
    # 关键修复：正确识别序号
    user_code_parts = []
    seq_num = None
    description_parts = []
    
    # 从后往前找包含数字的部分（这是序号+描述的开始）
    for i in range(len(before_price) - 1, -1, -1):
        part = before_price[i]
        
        # 如果这个部分包含数字，且符合BASExx格式
        if re.search(r'BASE\d+|[A-Z]+\d+', part):
            # 提取序号
            seq_match = re.search(r'(\d+)', part)
            if seq_match:
                seq_num = seq_match.group(1)
                
                # 分离序号前后的部分
                before_seq_match = re.search(r'^(.*)(\d+)(.*)$', part)
                if before_seq_match:
                    before_seq = before_seq_match.group(1)  # "BASE"
                    after_seq = before_seq_match.group(3)   # ""
                    
                    # 用户编码是序号前面的所有部分
                    user_code_parts = before_price[:i]
                    if before_seq and before_seq != 'BASE':
                        # 如果序号前有非BASE内容，添加到描述中
                        description_parts = [before_seq]
                    if after_seq:
                        description_parts.append(after_seq)
                    
                    # 序号后面的部分是描述
                    description_parts.extend(before_price[i+1:])
                    
                    break
    
    if not seq_num:
        return None
    
    # 用户编码：制造编码去掉最后的"BASE"部分
    user_code_match = re.match(r'^(.+?)\s*BASE?$', manuf_code)
    if user_code_match:
        user_code = user_code_match.group(1)
    else:
        user_code = ' '.join(user_code_parts) if user_code_parts else manuf_code
    
    # 描述：去掉"BASE"，保留描述性词汇
    description = ' '.join([d for d in description_parts if d != 'BASE']).strip()
    if not description:
        description = 'Base Accessory'  # 默认描述
    
    # 生成SKU（包含映射处理）
    sku = generate_final_sku(user_code, description, current_door_color)
    
    # 获取价格（使用PDF中的价格作为unit_price）
    try:
        unit_price = float(price.replace(',', ''))
    except ValueError:
        unit_price = 0.0
    
    return {
        'seq_num': seq_num,
        'manuf_code': manuf_code,
        'sku': sku,
        'qty': qty,
        'door_color': current_door_color or 'N/A',
        'unit_price': unit_price,
        'user_code': user_code,
        'description': description
    }

def parse_single_product(user_code, seq_num, description, price, qty_user, current_door_color, products):
    """解析单个产品信息"""
    # 处理*号：如果序号包含*号，将其移到描述前面
    if seq_num.startswith('*'):
        description = '* ' + description.strip()
        seq_num = seq_num[1:]  # 移除*号
    
    # 从qty_user中提取数量
    qty_match = re.match(r'^(\d+)', qty_user)
    qty = qty_match.group(1) if qty_match else '1'
    
    # 生成SKU（包含映射处理）
    sku = generate_final_sku(user_code, description.strip(), current_door_color)
    
    # 获取标准价格
    try:
        price_float = float(price.replace(',', ''))
        standard_price = standard_prices.get(sku, price_float)
    except ValueError:
        standard_price = standard_prices.get(sku, 0.0)
    
    product = {
        'seq_num': seq_num,
        'sku': sku,
        'qty': qty,
        'door_color': current_door_color or 'N/A',
        'unit_price': standard_price,
        'user_code': user_code,
        'description': description.strip()
    }
    
    products.append(product)
    print(f"解析产品: {product}")

def parse_product_line(line, current_door_color, products):
    """解析单个产品行"""
    parts = line.split()
    if len(parts) >= 4:
        # 查找价格（包含小数点的价格格式）
        price_index = -1
        for i, part in enumerate(parts):
            # 查找包含小数点的价格格式，如 602.00, 1,759.00
            if re.match(r'^\d+,?\d*\.\d{2}$', part):
                price_index = i
                break
        
        if price_index > 0:
            user_code = parts[0]  # 第1列：用户编码
            seq_num = parts[1]    # 第2列：序号
            description = ' '.join(parts[2:price_index])  # 第3列：描述
            price = parts[price_index].replace(',', '')   # 第4列：价格
            
            # 处理*号：如果序号包含*号，将其移到描述前面
            if seq_num.startswith('*'):
                description = '* ' + description
                seq_num = seq_num[1:]  # 移除*号
            
            # 第5列：数量+用户编码，需要拆分
            last_part = parts[-1] if len(parts) > price_index else '1' + user_code
            
            # 从最后一列提取数量（数字部分）
            qty_match = re.match(r'^(\d+)', last_part)
            if qty_match:
                qty = qty_match.group(1)
            else:
                qty = '1'
            
            # 验证数量
            if not qty.isdigit():
                qty = '1'
            
            # 生成SKU（包含映射处理）
            sku = generate_final_sku(user_code, description, current_door_color)
            
            # 获取标准价格
            try:
                price_float = float(price)
                standard_price = standard_prices.get(sku, price_float)
            except ValueError:
                # 如果价格解析失败，使用默认值
                standard_price = standard_prices.get(sku, 0.0)
            
            product = {
                'seq_num': seq_num,
                'sku': sku,
                'qty': qty,
                'door_color': current_door_color or 'N/A',
                'unit_price': standard_price,
                'user_code': user_code,
                'description': description
            }
            
            products.append(product)
            print(f"解析产品: {product}")

def parse_product_segment(segment, current_door_color, products):
    """解析产品段落（可能包含多个产品）"""
    print(f"解析段落: {segment}")
    
    # 查找所有可能的产品模式，包括包含*号的序号
    # 改进正则表达式以更好地处理包含页面信息的产品行
    product_patterns = re.findall(r'([A-Z0-9]+)\s+(\*?\d+)\s+([^0-9]+?)\s+(\d+,?\d*\.\d{2})\s+(\d+[A-Z0-9]+)', segment)
    
    if not product_patterns:
        # 如果没有找到标准模式，尝试更宽松的匹配
        print(f"  未找到标准产品模式，尝试宽松匹配...")
        
        # 尝试查找所有可能的产品模式
        # 支持多种格式：用户编码 序号 描述 价格 数量用户编码
        loose_patterns = [
            r'([A-Z0-9]+)\s+(\*?\d+)\s+([^0-9]+?)\s+(\d+,?\d*\.\d{2})\s+(\d+[A-Z0-9]+)',
            r'([A-Z0-9]+)\s+(\*?\d+)\s+([^0-9]+?)\s+(\d+,?\d*\.\d{2})\s+(\d+)',
            r'([A-Z0-9]+)\s+(\*?\d+)\s+([^0-9]+?)\s+(\d+,?\d*\.\d{2})',
        ]
        
        for pattern in loose_patterns:
            matches = re.findall(pattern, segment)
            if matches:
                product_patterns = matches
                print(f"  使用宽松模式找到 {len(matches)} 个产品")
                break
        
        # 如果仍然没有找到，尝试手动解析特殊格式
        if not product_patterns:
            print(f"  尝试手动解析特殊格式...")
            # 查找包含3DB30的行
            if '3DB30' in segment:
                # 手动解析包含3DB30的产品
                parts = segment.split()
                for i, part in enumerate(parts):
                    if part == '3DB30' and i + 3 < len(parts):
                        try:
                            user_code = parts[i]
                            seq_num = parts[i + 1]
                            description = parts[i + 2] + ' ' + parts[i + 3] + ' ' + parts[i + 4]
                            price = parts[i + 5]
                            qty_user = parts[i + 6]
                            
                            # 处理*号
                            if seq_num.startswith('*'):
                                description = '* ' + description
                                seq_num = seq_num[1:]
                            
                            # 从qty_user中提取数量
                            qty_match = re.match(r'^(\d+)', qty_user)
                            qty = qty_match.group(1) if qty_match else '1'
                            
                            # 生成SKU（包含映射处理）
                            sku = generate_final_sku(user_code, description.strip(), current_door_color)
                            
                            # 获取标准价格
                            try:
                                price_float = float(price.replace(',', ''))
                                standard_price = standard_prices.get(sku, price_float)
                            except ValueError:
                                standard_price = standard_prices.get(sku, 0.0)
                            
                            product = {
                                'seq_num': seq_num,
                                'sku': sku,
                                'qty': qty,
                                'door_color': current_door_color or 'N/A',
                                'unit_price': standard_price,
                                'user_code': user_code,
                                'description': description.strip()
                            }
                            
                            products.append(product)
                            print(f"  手动解析产品: {product}")
                        except (IndexError, ValueError) as e:
                            print(f"  手动解析失败: {e}")
                            continue
    
    for match in product_patterns:
        user_code, seq_num, description, price, qty_user = match
        
        # 处理*号：如果序号包含*号，将其移到描述前面
        if seq_num.startswith('*'):
            description = '* ' + description.strip()
            seq_num = seq_num[1:]  # 移除*号
        
        # 从qty_user中提取数量
        qty_match = re.match(r'^(\d+)', qty_user)
        qty = qty_match.group(1) if qty_match else '1'
        
        # 生成SKU（包含映射处理）
        sku = generate_final_sku(user_code, description.strip(), current_door_color)
        
        # 获取标准价格
        try:
            price_float = float(price.replace(',', ''))
            standard_price = standard_prices.get(sku, price_float)
        except ValueError:
            standard_price = standard_prices.get(sku, 0.0)
        
        product = {
            'seq_num': seq_num,
            'sku': sku,
            'qty': qty,
            'door_color': current_door_color or 'N/A',
            'unit_price': standard_price,
            'user_code': user_code,
            'description': description.strip()
        }
        
        products.append(product)
        print(f"解析产品: {product}")

def generate_sku(user_code, description, door_color):
    """根据规则生成SKU"""
    description_upper = description.upper()
    door_color = door_color or 'N/A'
    
    # 规则4.1: 包含"Cabinet"
    if 'CABINET' in description_upper:
        # 从用户编码中提取OCCW编码（去掉-L和-R后缀）
        occw_code = user_code.replace('-L', '').replace('-R', '')
        return f"{occw_code}-PLY-{door_color}"
    
    # 规则4.2: 包含"Hardware"
    elif 'HARDWARE' in description_upper:
        return f"HW-{user_code}"
    
    # 规则4.3: 包含"Accessory"
    elif 'ACCESSORY' in description_upper:
        return f"{door_color}-{user_code}"
    
    # 规则4.4: 其他情形
    else:
        return f"{door_color}-{user_code}"

def apply_sku_mapping(original_sku):
    """应用SKU映射关系，返回映射后的SKU"""
    global sku_mappings
    return sku_mappings.get(original_sku, original_sku)

def generate_final_sku(user_code, description, door_color):
    """生成最终的SKU（包含映射处理）"""
    # 先生成原始SKU
    original_sku = generate_sku(user_code, description, door_color)
    
    # 应用映射关系
    final_sku = apply_sku_mapping(original_sku)
    
    return final_sku

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

# 修改上传接口，返回比对结果
@app.route('/upload_quotation', methods=['POST'])
def upload_quotation():
    """上传报价单PDF"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 先提取原始PDF文本（不添加页面分隔符）
        raw_pdf_content = extract_pdf_content(filepath, add_page_markers=False)
        
        # 再进行解析（使用带页面分隔符的版本）
        pdf_content_for_parsing = extract_pdf_content(filepath, add_page_markers=True)
        products, compare_result, compare_message = parse_quotation_pdf(pdf_content_for_parsing)
        
        # 计算总价
        total_price = 0
        for p in products:
            try:
                qty = int(p['qty']) if str(p['qty']).isdigit() else 0
                unit_price = float(p['unit_price']) if p['unit_price'] is not None else 0
                total_price += qty * unit_price
            except (ValueError, TypeError):
                continue
        
        return jsonify({
            'success': True,
            'products': products,
            'total_price': total_price,
            'filename': filename,
            'raw_text': raw_pdf_content,  # 返回原始PDF文本
            'compare_result': compare_result,
            'compare_message': compare_message
        })
    
    return jsonify({'error': '请上传PDF文件'}), 400

@app.route('/upload_prices', methods=['POST'])
def upload_prices():
    """上传标准价格表"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'error': '请上传Excel或CSV文件'}), 400
        
        # 假设第一列是SKU，第二列是价格
        for _, row in df.iterrows():
            sku = str(row.iloc[0])
            price = float(row.iloc[1])
            standard_prices[sku] = price
        
        save_standard_prices()
        
        return jsonify({
            'success': True,
            'message': f'成功导入 {len(df)} 条价格记录'
        })
        
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 400

@app.route('/upload_occw_prices', methods=['POST'])
@admin_required
def upload_occw_prices():
    """上传OCCW价格表"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        if not file.filename.endswith('.xlsx'):
            return jsonify({'error': '请上传Excel文件(.xlsx)'}), 400
        
        df = pd.read_excel(file)
        
        # 跳过表头行，假设第一列是SKU，第二列是销售价格
        global occw_prices
        occw_prices.clear()
        
        for i, row in df.iterrows():
            if i == 0:  # 跳过表头行
                continue
            try:
                sku = str(row.iloc[0]).strip()
                price = float(row.iloc[1])
                if sku and sku != 'nan':  # 过滤空值
                    occw_prices[sku] = price
            except (ValueError, IndexError):
                continue  # 跳过无效行
        
        if save_occw_prices():
            return jsonify({
                'success': True,
                'message': f'成功导入 {len(occw_prices)} 条OCCW价格记录'
            })
        else:
            return jsonify({'error': '保存OCCW价格表失败'}), 500
        
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 400

@app.route('/get_occw_skus', methods=['GET'])
def get_occw_skus():
    """获取OCCW SKU列表（用于下拉选择），支持按userCode过滤"""
    try:
        filter_user_code = request.args.get('filter_user_code')
        filter_manuf_code = request.args.get('filter_manuf_code')  # 保留兼容性
        
        if filter_user_code:
            # 过滤包含指定userCode的SKU
            filtered_skus = []
            for sku in occw_prices.keys():
                if filter_user_code in sku:
                    filtered_skus.append(sku)
            filtered_skus.sort()
            return jsonify({
                'success': True,
                'skus': filtered_skus
            })
        elif filter_manuf_code:
            # 兼容旧版本，按manufCode过滤
            filtered_skus = []
            for sku in occw_prices.keys():
                if filter_manuf_code in sku:
                    filtered_skus.append(sku)
            filtered_skus.sort()
            return jsonify({
                'success': True,
                'skus': filtered_skus
            })
        else:
            # 返回所有SKU
            sku_list = list(occw_prices.keys())
            sku_list.sort()
            return jsonify({
                'success': True,
                'skus': sku_list
            })
    except Exception as e:
        return jsonify({'error': f'获取SKU列表失败: {str(e)}'}), 500

@app.route('/save_sku_mapping', methods=['POST'])
@admin_required
def save_sku_mapping():
    """保存SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        mapped_sku = data.get('mapped_sku')
        
        if not original_sku or not mapped_sku:
            return jsonify({'error': '缺少必要参数'}), 400
        
        global sku_mappings
        sku_mappings[original_sku] = mapped_sku
        
        if save_sku_mappings():
            # 返回映射的SKU对应的价格
            occw_price = occw_prices.get(mapped_sku, 0.0)
            return jsonify({
                'success': True,
                'message': '映射关系保存成功',
                'occw_price': occw_price
            })
        else:
            return jsonify({'error': '保存映射关系失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'保存映射关系失败: {str(e)}'}), 500

@app.route('/get_occw_price', methods=['GET'])
def get_occw_price():
    """获取指定SKU的OCCW价格"""
    try:
        sku = request.args.get('sku')
        if not sku:
            return jsonify({'error': '缺少SKU参数'}), 400
        
        # 首先检查是否有映射关系
        mapped_sku = sku_mappings.get(sku, sku)
        price = occw_prices.get(mapped_sku, 0.0)
        
        return jsonify({
            'success': True,
            'price': price,
            'mapped_sku': mapped_sku if mapped_sku != sku else None
        })
        
    except Exception as e:
        return jsonify({'error': f'获取价格失败: {str(e)}'}), 500

@app.route('/get_occw_stats', methods=['GET'])
@admin_required
def get_occw_stats():
    """获取OCCW价格表统计信息"""
    try:
        return jsonify({
            'success': True,
            'count': len(occw_prices)
        })
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@app.route('/get_sku_mappings', methods=['GET'])
@admin_required
def get_sku_mappings():
    """获取所有SKU映射关系"""
    try:
        return jsonify({
            'success': True,
            'mappings': sku_mappings
        })
    except Exception as e:
        return jsonify({'error': f'获取映射关系失败: {str(e)}'}), 500

@app.route('/delete_sku_mapping', methods=['POST'])
@admin_required
def delete_sku_mapping():
    """删除SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        
        if not original_sku:
            return jsonify({'error': '缺少原始SKU参数'}), 400
        
        global sku_mappings
        if original_sku in sku_mappings:
            del sku_mappings[original_sku]
            
            if save_sku_mappings():
                return jsonify({
                    'success': True,
                    'message': '映射关系已删除'
                })
            else:
                return jsonify({'error': '保存映射关系失败'}), 500
        else:
            return jsonify({'error': '映射关系不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'删除映射关系失败: {str(e)}'}), 500

@app.route('/sku_mappings')
@admin_required
def sku_mappings_page():
    """SKU映射管理页面"""
    return render_template('sku_mappings.html')

@app.route('/export/occw_excel')
def export_occw_excel():
    """导出OCCW Excel报价单"""
    occw_data = request.args.get('occw_data', '[]')
    occw_data = json.loads(occw_data)
    
    if not occw_data:
        return "没有数据可导出", 400
    
    try:
        # 创建DataFrame
        df_data = []
        total_amount = 0
        
        for item in occw_data:
            df_data.append({
                '序号': item['seq_num'],
                'OCCW SKU': item['occw_sku'],
                '数量': item['qty'],
                'OCCW单价': item['unit_price'],
                'OCCW总价': item['total_price']
            })
            total_amount += item['total_price']
        
        # 添加合计行
        df_data.append({
            '序号': '',
            'OCCW SKU': '',
            '数量': '',
            'OCCW单价': '合计:',
            'OCCW总价': total_amount
        })
        
        df = pd.DataFrame(df_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, engine='openpyxl')
            
            # 设置文件名
            filename = f'OCCW报价单_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            
            return send_file(tmp.name, as_attachment=True, download_name=filename)
            
    except Exception as e:
        return f"导出失败: {str(e)}", 500

@app.route('/export/<format>')
def export_quotation(format):
    """导出报价单"""
    products = request.args.get('products', '[]')
    products = json.loads(products)
    
    if format == 'excel':
        df = pd.DataFrame(products)
        df['总价'] = df['qty'].astype(int) * df['unit_price'].astype(float)
        
        filename = f'quotation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='报价单', index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    elif format == 'csv':
        df = pd.DataFrame(products)
        df['总价'] = df['qty'].astype(int) * df['unit_price'].astype(float)
        
        filename = f'quotation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    elif format == 'pdf':
        df = pd.DataFrame(products)
        df['总价'] = df['qty'].astype(int) * df['unit_price'].astype(float)
        
        filename = f'quotation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # 创建表格数据
        table_data = [['序号', 'SKU', '数量', '花色', '单价', '总价']]
        for _, row in df.iterrows():
            table_data.append([
                row['seq_num'],
                row['sku'],
                row['qty'],
                row['door_color'],
                f"${row['unit_price']}",
                f"${row['总价']}"
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    return jsonify({'error': '不支持的导出格式'}), 400

@app.route('/config')
@admin_required
def config():
    """配置页面"""
    return render_template('config.html', sku_rules=sku_rules)

@app.route('/help')
def help():
    """帮助页面"""
    return render_template('help.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session[ADMIN_SESSION_KEY] = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            return render_template('admin_login.html', error='密码错误')
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    """管理员登出"""
    session.pop(ADMIN_SESSION_KEY, None)
    return redirect(url_for('index'))

@app.route('/set_language/<lang>')
def set_language_route(lang):
    """设置语言"""
    if set_language(lang):
        return jsonify({'success': True, 'language': lang})
    else:
        return jsonify({'success': False, 'error': 'Unsupported language'}), 400

@app.route('/save_config', methods=['POST'])
@admin_required
def save_config():
    """保存配置"""
    global sku_rules
    sku_rules = request.json
    save_sku_rules()
    return jsonify({'success': True, 'message': '配置保存成功'})

@app.route('/prices')
@admin_required
def prices():
    """价格管理页面"""
    return render_template('prices.html', prices=standard_prices)

@app.route('/get_pdf_text')
def get_pdf_text():
    """获取PDF识别的原始文本"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': '没有指定文件名'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        # 返回原始PDF文本（不添加页面分隔符）
        pdf_content = extract_pdf_content(filepath, add_page_markers=False)
        return jsonify({
            'success': True,
            'text': pdf_content
        })
    except Exception as e:
        return jsonify({'error': f'读取PDF失败: {str(e)}'}), 500

# 确保目录存在
for directory in ['uploads', 'data']:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")

# 初始化数据（无论如何都要加载）
load_standard_prices()
load_occw_prices()
load_sku_mappings()
load_sku_rules()
print(f"已加载 {len(occw_prices)} 个OCCW价格")
print(f"已加载 {len(sku_mappings)} 个SKU映射关系")

if __name__ == '__main__':
    # 生产环境配置
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug) 