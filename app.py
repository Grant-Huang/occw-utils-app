import os
import re
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from urllib.parse import urlencode
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
from typing import Dict, List, Tuple, Any
from io import BytesIO
import xlsxwriter
import hashlib
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据加载将在应用启动时进行

# 管理员配置
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123')  # 支持环境变量
ADMIN_SESSION_KEY = "is_admin"

# 语言支持
def get_current_language():
    """获取当前语言"""
    return session.get('language', DEFAULT_LANGUAGE)

def set_language(lang):
    """设置语言"""
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        # 清除自动检测标记，表示用户已手动设置语言
        session.pop('auto_detected', None)
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
        'system_settings': system_settings,
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
                return jsonify({'error': get_text('admin_required'), 'redirect': '/admin_login'}), 401
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
system_settings = {}  # 系统设置
users = {}  # 用户数据：{username: {password_hash, email, created_at}}
quotations = {}  # 用户报价单数据：{username: [{quotation_id, title, data, created_at, updated_at}]}
current_quotation_id = 1  # 用于生成报价单编号

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

def load_system_settings():
    """加载系统设置"""
    global system_settings
    try:
        if os.path.exists('data/system_settings.json'):
            with open('data/system_settings.json', 'r', encoding='utf-8') as f:
                system_settings = json.load(f)
        else:
            # 默认设置
            system_settings = {
                'default_sales_person': '',
                'sales_persons': []
            }
            save_system_settings()
    except Exception as e:
        print(f"加载系统设置失败: {e}")
        system_settings = {
            'default_sales_person': '',
            'sales_persons': [],
            'user_login_enabled': True,
            'admin_password': ADMIN_PASSWORD
        }

def save_system_settings():
    """保存系统设置到文件"""
    try:
        with open('data/system_settings.json', 'w', encoding='utf-8') as f:
            json.dump(system_settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存系统设置失败: {e}")
        return False

def load_users():
    """加载用户数据"""
    global users
    try:
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r', encoding='utf-8') as f:
                users = json.load(f)
    except Exception as e:
        print(f"加载用户数据失败: {e}")
        users = {}

def save_users():
    """保存用户数据"""
    try:
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存用户数据失败: {e}")
        return False

def load_quotations():
    """加载报价单数据"""
    global quotations
    try:
        if os.path.exists('data/quotations.json'):
            with open('data/quotations.json', 'r', encoding='utf-8') as f:
                quotations = json.load(f)
    except Exception as e:
        print(f"加载报价单数据失败: {e}")
        quotations = {}

def save_quotations():
    """保存报价单数据"""
    try:
        with open('data/quotations.json', 'w', encoding='utf-8') as f:
            json.dump(quotations, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存报价单数据失败: {e}")
        return False

def generate_quotation_id():
    """生成报价单编号 Q + 5位数字"""
    global current_quotation_id
    
    # 从现有报价单中找出最大ID
    max_id = 0
    for username, user_quotations in quotations.items():
        for quotation in user_quotations:
            if 'quotation_id' in quotation:
                try:
                    id_num = int(quotation['quotation_id'][1:])  # 去掉'Q'前缀
                    max_id = max(max_id, id_num)
                except ValueError:
                    continue
    
    # 使用最大ID + 1，或者使用current_quotation_id（取较大值）
    current_quotation_id = max(current_quotation_id, max_id + 1)
    quotation_id = f"Q{current_quotation_id:05d}"
    current_quotation_id += 1
    return quotation_id

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('username'):
            return redirect(url_for('user_login'))
        return f(*args, **kwargs)
    return decorated_function



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


class OCCWPriceTransformer:
    """OCCW价格表转换器 - 完全重写版本"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def transform_excel_file(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        转换Excel文件
        返回: (转换后的数据列表, 错误信息列表)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # 读取Excel文件，第一行为表头
            df = pd.read_excel(file_path, header=0)
            print(f"读取Excel文件成功，共 {len(df)} 行数据")
            print(f"检测到的列名: {list(df.columns)}")
            
            # 检查必需的列
            required_columns = ['内部参考号', '销售价', '变体值', '名称', '产品类别/名称']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Excel文件缺少必需的列: {', '.join(missing_columns)}"
                print(f"错误: {error_msg}")
                self.errors.append(error_msg)
                return [], self.errors
            
            transformed_data = []
            
            # 逐行转换
            for index, row in df.iterrows():
                row_number = index + 2  # Excel行号（第1行是表头）
                
                try:
                    transformed_row = self.transform_single_row(row, row_number)
                    if transformed_row:
                        transformed_data.append(transformed_row)
                except Exception as e:
                    error_msg = f"第{row_number}行转换失败: {str(e)}"
                    print(f"错误: {error_msg}")
                    self.errors.append(error_msg)
            
            print(f"转换完成: 成功 {len(transformed_data)} 条，错误 {len(self.errors)} 个")
            return transformed_data, self.errors
            
        except Exception as e:
            error_msg = f"文件读取失败: {str(e)}"
            print(f"错误: {error_msg}")
            self.errors.append(error_msg)
            return [], self.errors
    
    def transform_single_row(self, row: pd.Series, row_number: int) -> Dict[str, Any]:
        """转换单行数据"""
        
        # 提取原始数据
        internal_ref = str(row.get('内部参考号', '')).strip()
        unit_price = row.get('销售价', 0)
        variant_value = str(row.get('变体值', '')).strip()
        name = str(row.get('名称', '')).strip()
        category = str(row.get('产品类别/名称', '')).strip()
        
        # 处理pandas的NaN值
        if internal_ref == 'nan':
            internal_ref = ''
        if variant_value == 'nan':
            variant_value = ''
        if name == 'nan':
            name = ''
        if category == 'nan':
            category = ''
        
        # 验证必需字段
        if not internal_ref:
            self.errors.append(f"第{row_number}行：内部参考号不能为空")
            return None
        
        if not name:
            self.errors.append(f"第{row_number}行：名称不能为空")
            return None
        
        if not category:
            self.errors.append(f"第{row_number}行：产品类别/名称不能为空")
            return None
        
        # 验证名称格式：必须以英文字母或数字开头
        if not re.match(r'^[A-Za-z0-9]', name):
            self.errors.append(f"第{row_number}行：名称 '{name}' 必须以英文字母或数字开头")
            return None
        
        # 标准化类别名称（转换为大写并去除空格）
        category = category.upper().strip()
        
        # 初始化输出变量
        door_variant = ""
        box_variant = ""
        product_name = ""
        output_category = ""
        
        try:
            # 根据产品类别应用转换规则
            if category in ["RTA ASSM.组合件", "ASSM.组合件", "组合件"]:
                door_variant = self._extract_door_variant(variant_value, row_number)
                box_variant, product_name = self._split_name_for_assm(name, row_number)
                output_category = "Assm.组合件"
                
            elif category in ["DOOR", "门板"]:
                door_variant = self._extract_door_variant(variant_value, row_number)
                box_variant = ""
                product_name = self._extract_product_name_for_door(name, row_number)
                output_category = "Door"
                
            elif category in ["BOX", "柜体"] or "BOX" in category:
                if "OPEN" in name.upper():
                    # 开放柜体
                    door_variant = self._extract_door_variant(variant_value, row_number)
                    box_variant = ""
                    product_name = self._extract_product_name_for_open_box(name, row_number)
                    output_category = "BOX"
                else:
                    # 标准柜体
                    door_variant = ""
                    box_variant = self._extract_box_variant(variant_value, row_number)
                    product_name = self._extract_product_name_for_standard_box(name, row_number)
                    output_category = "BOX"
                    
            elif category in ["ENDING PANEL", "MOLDING", "TOE KICK", "FILLER"]:
                door_variant = self._extract_door_variant(variant_value, row_number)
                box_variant = ""
                product_name = name  # 保持原名称
                output_category = category
                
            else:
                # 其他情况归类为五金件
                door_variant = ""
                box_variant = ""
                product_name = self._extract_hardware_product_name(name, row_number)
                output_category = "HARDWARE"
            
            return {
                'SKU': internal_ref,
                'product_name': product_name,
                'door_variant': door_variant,
                'box_variant': box_variant,
                'category': output_category,
                'unit_price': float(unit_price) if unit_price else 0.0,
                'original_row': row_number
            }
            
        except Exception as e:
            self.errors.append(f"第{row_number}行：数据处理错误 - {str(e)}")
            return None
    
    def _extract_assm_variants(self, variant_value: str, row_number: int) -> tuple:
        """提取组合件的门板和柜身变体"""
        if not variant_value:
            self.errors.append(f"第{row_number}行：组合件的变体值不能为空")
            return "", ""
        
        door_variant = ""
        box_variant = ""
        
        # 解析格式：'门板: XXX 柜身: YYY'
        parts = variant_value.split()
        
        for i, part in enumerate(parts):
            if part == "门板:" and i + 1 < len(parts):
                door_variant = parts[i + 1]
            elif part == "柜身:" and i + 1 < len(parts):
                box_variant = parts[i + 1]
        
        # 验证门板变体
        if not door_variant:
            self.errors.append(f"第{row_number}行：组合件变体值中缺少门板变体，实际值为'{variant_value}'")
        elif len(door_variant) < 2 or len(door_variant) > 3:
            self.errors.append(f"第{row_number}行：门板变体应为2-3个字符，实际为{len(door_variant)}个字符（'{door_variant}'）")
        
        # 验证柜身变体
        if not box_variant:
            self.errors.append(f"第{row_number}行：组合件变体值中缺少柜身变体，实际值为'{variant_value}'")
        elif len(box_variant) < 2 or len(box_variant) > 3:
            self.errors.append(f"第{row_number}行：柜身变体应为2-3个字符，实际为{len(box_variant)}个字符（'{box_variant}'）")
        
        return door_variant, box_variant
    
    def _extract_door_variant(self, variant_value: str, row_number: int) -> str:
        """提取门板变体"""
        if not variant_value:
            return ""
        
        if not variant_value.startswith("门板: "):
            self.errors.append(f"第{row_number}行：变体值格式错误，应以'门板: '开头，实际值为'{variant_value}'")
            return ""
        
        variant = variant_value.replace("门板: ", "")
        if len(variant) < 2 or len(variant) > 3:
            self.errors.append(f"第{row_number}行：门板变体应为2-3个字符，实际为{len(variant)}个字符（'{variant}'）")
        
        return variant
    
    def _extract_box_variant(self, variant_value: str, row_number: int) -> str:
        """提取柜身变体"""
        if not variant_value:
            self.errors.append(f"第{row_number}行：标准BOX柜体的变体值不能为空")
            return ""
        
        if not variant_value.startswith("柜身: "):
            self.errors.append(f"第{row_number}行：变体值格式错误，应以'柜身: '开头，实际值为'{variant_value}'")
            return ""
        
        variant = variant_value.replace("柜身: ", "")
        if len(variant) < 2 or len(variant) > 3:
            self.errors.append(f"第{row_number}行：柜身变体应为2-3个字符，实际为{len(variant)}个字符（'{variant}'）")
        
        return variant
    
    def _split_name_for_assm(self, name: str, row_number: int) -> Tuple[str, str]:
        """为RTA组合件拆分名称：返回(柜身变体, 产品名称)"""
        if "-" not in name:
            # 如果没有分隔符，产品名称=名称，柜身变体为空
            return "", name
        
        parts = name.split("-", 1)  # 只分割第一个"-"
        box_variant = parts[0]      # "-"前面的部分作为柜身变体
        product_name = parts[1]     # "-"后面的部分作为产品名称
        
        return box_variant, product_name
    
    def _extract_product_name_for_door(self, name: str, row_number: int) -> str:
        """为Door产品提取产品名称："-"前面的部分"""
        if "-" not in name:
            return name
        
        parts = name.split("-")
        return parts[0]
    
    def _extract_product_name_for_open_box(self, name: str, row_number: int) -> str:
        """为开放BOX产品提取产品名称："-"前面的部分"""
        if "-" not in name:
            return name
        
        parts = name.split("-")
        return parts[0]
    
    def _extract_product_name_for_standard_box(self, name: str, row_number: int) -> str:
        """为标准BOX产品提取产品名称："-"前面的部分"""
        if "-" not in name:
            return name
        
        parts = name.split("-")
        return parts[0]
    
    def _extract_hardware_product_name(self, name: str, row_number: int) -> str:
        """为五金件产品提取产品名称：去掉"HW-"前缀"""
        if name.upper().startswith("HW-"):
            return name[3:]
        return name
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return {
            'total_errors': len(self.errors),
            'error_details': self.errors,
            'has_errors': len(self.errors) > 0
        }


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
    """根据产品描述生成SKU"""
    description_upper = description.upper()
    door_color = door_color or 'N/A'
    
    # 处理用户代码，移除L和R后缀
    processed_user_code = user_code.replace('-L', '').replace('-R', '')
    
    # 根据产品类型生成SKU
    if 'CABINET' in description_upper or 'BOX' in description_upper:
        # 柜身类产品
        return f"{processed_user_code}-PLY-{door_color}"
    elif 'DOOR' in description_upper:
        # 门板类产品
        return f"{processed_user_code}-DOOR-{door_color}"
    elif 'HARDWARE' in description_upper or 'HW' in description_upper:
        # 五金件
        return f"HW-{user_code}"
    elif 'MOLDING' in description_upper:
        # 装饰条
        return f"{door_color}-MOLD-{user_code}"
    elif 'TOE KICK' in description_upper:
        # 踢脚线
        return f"{door_color}-TK-{user_code}"
    elif 'FILLER' in description_upper:
        # 填充板
        return f"{door_color}-FILL-{user_code}"
    elif 'ENDING PANEL' in description_upper or 'END PANEL' in description_upper:
        # 端板
        return f"{door_color}-EP-{user_code}"
    elif 'RTA ASSM' in description_upper or 'ASSEMBLY' in description_upper:
        # 组合件
        return f"{processed_user_code}-ASSM-{door_color}"
    else:
        # 其他产品，使用默认格式
        return f"{door_color}-{user_code}"


def generate_possible_skus(category, product, box_variant, door_variant):
    """根据产品信息生成可能的SKU列表"""
    possible_skus = []
    
    # 基础SKU格式
    base_sku = product.upper() if product else ""
    
    if not base_sku:
        return possible_skus
    
    # 根据产品类别生成不同的SKU格式
    if category == 'RTA Assm.组合件':
        # 组合件格式：{产品代码}-ASSM-{门板颜色}
        if door_variant:
            possible_skus.append(f"{base_sku}-ASSM-{door_variant}")
        possible_skus.append(f"{base_sku}-ASSM")
        
    elif category == 'Door门板':
        # 门板格式：{产品代码}-DOOR-{门板颜色}
        if door_variant:
            possible_skus.append(f"{base_sku}-DOOR-{door_variant}")
        possible_skus.append(f"{base_sku}-DOOR")
        
    elif category == 'BOX柜身':
        # 柜身格式：{产品代码}-PLY-{门板颜色}
        if door_variant:
            possible_skus.append(f"{base_sku}-PLY-{door_variant}")
        possible_skus.append(f"{base_sku}-PLY")
        
    elif category == 'Ending Panel端板':
        # 端板格式：{门板颜色}-EP-{产品代码}
        if door_variant:
            possible_skus.append(f"{door_variant}-EP-{base_sku}")
        possible_skus.append(f"EP-{base_sku}")
        
    elif category == 'Molding装饰条':
        # 装饰条格式：{门板颜色}-MOLD-{产品代码}
        if door_variant:
            possible_skus.append(f"{door_variant}-MOLD-{base_sku}")
        possible_skus.append(f"MOLD-{base_sku}")
        
    elif category == 'Toe Kick踢脚线':
        # 踢脚线格式：{门板颜色}-TK-{产品代码}
        if door_variant:
            possible_skus.append(f"{door_variant}-TK-{base_sku}")
        possible_skus.append(f"TK-{base_sku}")
        
    elif category == 'Filler填充板':
        # 填充板格式：{门板颜色}-FILL-{产品代码}
        if door_variant:
            possible_skus.append(f"{door_variant}-FILL-{base_sku}")
        possible_skus.append(f"FILL-{base_sku}")
        
    elif category == 'Hardware五金件':
        # 五金件格式：HW-{产品代码}
        possible_skus.append(f"HW-{base_sku}")
        
    else:
        # 默认格式：{门板颜色}-{产品代码}
        if door_variant:
            possible_skus.append(f"{door_variant}-{base_sku}")
        possible_skus.append(base_sku)
    
    return possible_skus


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
    return render_template('index.html', today_date=datetime.now().strftime('%Y-%m-%d'))
    # 自动检测用户语言偏好
    user_language = detect_user_language()
    return render_template('index.html', detected_language=user_language)

def detect_user_language():
    """自动检测用户语言偏好"""
    # 1. 首先检查用户是否已经设置过语言偏好
    if 'language' in session:
        return session['language']
    
    # 2. 检查登录用户的语言偏好设置
    username = session.get('username')
    if username and username in users:
        user_preferred_language = users[username].get('preferred_language')
        if user_preferred_language:
            session['language'] = user_preferred_language
            return user_preferred_language
    
    # 3. 检查是否已经自动检测过语言，避免重复检测
    if 'auto_detected' in session:
        return session.get('language', 'zh')
    
    # 4. 检查请求头中的Accept-Language
    accept_language = request.headers.get('Accept-Language', '')
    if accept_language:
        # 解析Accept-Language头，获取首选语言
        languages = accept_language.split(',')
        for lang in languages:
            lang_code = lang.split(';')[0].strip().lower()
            if lang_code.startswith('zh'):
                session['language'] = 'zh'
                session['auto_detected'] = True
                return 'zh'
            elif lang_code.startswith('en'):
                session['language'] = 'en'
                session['auto_detected'] = True
                return 'en'
            elif lang_code.startswith('fr'):
                session['language'] = 'fr'
                session['auto_detected'] = True
                return 'fr'
    
    # 5. 默认返回中文
    session['language'] = 'zh'
    session['auto_detected'] = True
    return 'zh'

# 修改上传接口，返回比对结果
@app.route('/upload_quotation', methods=['POST'])
def upload_quotation():
    """上传报价单PDF"""
    if 'file' not in request.files:
        return jsonify({'error': get_text('no_file_selected')}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': get_text('no_file_selected')}), 400
    
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
    
    return jsonify({'error': get_text('upload_pdf_file')}), 400

@app.route('/upload_prices', methods=['POST'])
def upload_prices():
    """上传标准价格表"""
    if 'file' not in request.files:
        return jsonify({'error': get_text('no_file_selected')}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': get_text('no_file_selected')}), 400
    
    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'error': get_text('upload_excel_csv')}), 400
        
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
        return jsonify({'error': f'{get_text("file_processing_failed")}: {str(e)}'}), 400

@app.route('/upload_occw_prices', methods=['POST'])
@admin_required 
def upload_occw_prices():
    """上传OCCW价格表 - 完全重写版本"""
    print("=" * 50)
    print("开始处理OCCW价格表上传...")
    
    try:
        # 1. 验证文件
        if 'file' not in request.files:
            error_msg = '没有选择文件'
            print(f"错误: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        file = request.files['file']
        if file.filename == '':
            error_msg = '没有选择文件'
            print(f"错误: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            error_msg = '文件格式不支持，请选择Excel文件(.xlsx或.xls)'
            print(f"错误: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        print(f"接收到文件: {file.filename}")
        
        # 2. 获取导入模式
        import_mode = request.form.get('import_mode', 'create')
        clear_existing = import_mode == 'create'
        print(f"导入模式: {import_mode} ({'清空现有数据' if clear_existing else '追加模式'})")
        
        # 3. 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), f"occw_upload_{filename}")
        file.save(temp_path)
        print(f"临时文件保存到: {temp_path}")
        
        try:
            # 4. 使用转换器处理Excel文件
            print("开始转换Excel文件...")
            transformer = OCCWPriceTransformer()
            transformed_data, errors = transformer.transform_excel_file(temp_path)
            
            print(f"转换完成: 成功 {len(transformed_data)} 条，错误 {len(errors)} 个")
            
            # 5. 如果没有有效数据（全部行都解析失败）
            if not transformed_data:
                if errors:
                    error_msg = f'所有数据行解析失败，发现 {len(errors)} 个错误'
                else:
                    error_msg = '没有有效的价格数据'
                print(f"错误: {error_msg}")
                return jsonify({
                    'success': False, 
                    'error': error_msg,
                    'has_errors': True,
                    'error_details': errors,
                    'data_count': 0,
                    'error_count': len(errors)
                }), 400
            
            # 7. 更新价格数据
            global occw_prices
            original_count = len(occw_prices)
            added_count = 0
            updated_count = 0
            
            print(f"开始更新价格数据，原有记录: {original_count}")
            
            if clear_existing:
                occw_prices.clear()
                print("已清空现有价格数据")
            
            # 处理转换后的数据
            for item in transformed_data:
                sku = item['SKU']
                
                if clear_existing or sku not in occw_prices:
                    added_count += 1
                else:
                    updated_count += 1
                
                # 保存完整的产品信息
                occw_prices[sku] = {
                    'product_name': item['product_name'],
                    'door_variant': item['door_variant'],
                    'box_variant': item['box_variant'],
                    'category': item['category'],
                    'unit_price': item['unit_price'],
                    'updated_at': datetime.now().isoformat()
                }
            
            final_count = len(occw_prices)
            print(f"价格数据更新完成: 新增 {added_count} 条，更新 {updated_count} 条，总计 {final_count} 条")
            
            # 8. 保存到文件
            if save_occw_prices():
                print("价格数据保存成功")
                
                # 构建成功消息
                if clear_existing:
                    if errors:
                        message = f'成功导入 {len(transformed_data)} 条OCCW价格记录，{len(errors)} 行解析失败（创建模式：已清空原有数据）'
                    else:
                        message = f'成功导入 {len(transformed_data)} 条OCCW价格记录（创建模式：已清空原有数据）'
                else:
                    if errors:
                        message = f'成功处理 {len(transformed_data)} 条记录（追加模式：新增 {added_count} 条，更新 {updated_count} 条），{len(errors)} 行解析失败，总计 {final_count} 条价格记录'
                    else:
                        message = f'成功处理 {len(transformed_data)} 条记录（追加模式：新增 {added_count} 条，更新 {updated_count} 条），总计 {final_count} 条价格记录'
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'data_count': len(transformed_data),
                    'error_count': len(errors),
                    'has_errors': len(errors) > 0,
                    'error_details': errors if errors else [],
                    'total_count': final_count,
                    'added_count': added_count,
                    'updated_count': updated_count,
                    'mode': 'create' if clear_existing else 'append',
                    'original_count': original_count
                })
            else:
                error_msg = '保存价格数据失败'
                print(f"错误: {error_msg}")
                return jsonify({'success': False, 'error': error_msg}), 500
                
        finally:
            # 9. 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"已删除临时文件: {temp_path}")
                
    except Exception as e:
        error_msg = f'处理文件时发生错误: {str(e)}'
        print(f"异常错误: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500
    
    finally:
        print("OCCW价格表上传处理完成")
        print("=" * 50)

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
        return jsonify({'error': f'{get_text("get_sku_list_failed")}: {str(e)}'}), 500

@app.route('/save_sku_mapping', methods=['POST'])
@admin_required
def save_sku_mapping():
    """保存SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        mapped_sku = data.get('mapped_sku')
        
        if not original_sku or not mapped_sku:
            return jsonify({'error': get_text('missing_required_params')}), 400
        
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
            return jsonify({'error': get_text('save_mapping_failed')}), 500
            
    except Exception as e:
        return jsonify({'error': f'{get_text("save_mapping_failed")}: {str(e)}'}), 500

@app.route('/get_occw_price', methods=['GET'])
def get_occw_price():
    """获取指定SKU的OCCW价格"""
    try:
        sku = request.args.get('sku')
        if not sku:
            return jsonify({'error': get_text('missing_sku_param')}), 400
        
        # 首先检查是否有映射关系
        mapped_sku = sku_mappings.get(sku, sku)
        price_data = occw_prices.get(mapped_sku, 0.0)
        
        # 处理新旧数据格式兼容性
        if isinstance(price_data, dict):
            # 新格式：完整产品信息
            price = price_data.get('unit_price', 0.0)
            product_info = {
                'product_name': price_data.get('product_name', ''),
                'door_variant': price_data.get('door_variant', ''),
                'box_variant': price_data.get('box_variant', ''),
                'category': price_data.get('category', ''),
                'updated_at': price_data.get('updated_at', '')
            }
        else:
            # 旧格式：只有价格
            price = price_data
            product_info = {}
        
        return jsonify({
            'success': True,
            'price': price,
            'mapped_sku': mapped_sku if mapped_sku != sku else None,
            'product_info': product_info
        })
        
    except Exception as e:
        return jsonify({'error': f'{get_text("get_price_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{get_text("get_stats_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{get_text("get_mapping_failed")}: {str(e)}'}), 500

@app.route('/delete_sku_mapping', methods=['POST'])
@admin_required
def delete_sku_mapping():
    """删除SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        
        if not original_sku:
            return jsonify({'error': get_text('missing_original_sku')}), 400
        
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
            return jsonify({'error': get_text('mapping_not_exists')}), 404
            
    except Exception as e:
        return jsonify({'error': f'{get_text("delete_mapping_failed")}: {str(e)}'}), 500

@app.route('/clear_all_sku_mappings', methods=['POST'])
@admin_required
def clear_all_sku_mappings():
    """清空所有SKU映射关系"""
    try:
        global sku_mappings
        original_count = len(sku_mappings)
        sku_mappings.clear()
        
        if save_sku_mappings():
            return jsonify({
                'success': True,
                'message': f'已清空 {original_count} 个SKU映射关系'
            })
        else:
            return jsonify({'error': '保存映射关系失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'{get_text("clear_mapping_failed")}: {str(e)}'}), 500

@app.route('/export_sku_mappings', methods=['GET'])
@admin_required
def export_sku_mappings():
    """导出SKU映射关系为JSON格式"""
    try:
        return jsonify({
            'success': True,
            'mappings': sku_mappings,
            'count': len(sku_mappings),
            'export_time': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("export_mapping_failed")}: {str(e)}'}), 500

@app.route('/sku_mappings')
@admin_required
def sku_mappings_page():
    """SKU映射管理页面"""
    return render_template('sku_mappings.html')

@app.route('/export/occw_excel')
def export_occw_excel():
    """导出OCCW格式的Excel文件 - 新6列格式"""
    try:
        occw_data = request.args.get('occw_data')
        export_date = request.args.get('export_date')
        export_username = request.args.get('export_username')
        export_sales_person = request.args.get('export_sales_person')
        
        if not occw_data:
            return jsonify({'error': 'No data provided'}), 400
        
        occw_data = json.loads(occw_data)
        
        # 创建Excel文件
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # 设置标题行 - 新6列格式
        headers = ['订单日期', '客户', '销售人员', '订单行/产品', '订单行/数量', '订单行/单价']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        for row, item in enumerate(occw_data, 1):
            # 第一行包含日期、客户、销售人员信息
            if row == 1:
                worksheet.write(row, 0, export_date)  # 订单日期
                worksheet.write(row, 1, export_username)  # 客户
                worksheet.write(row, 2, export_sales_person)  # 销售人员
            else:
                # 其他行为空
                worksheet.write(row, 0, '')
                worksheet.write(row, 1, '')
                worksheet.write(row, 2, '')
            
            # 产品信息
            worksheet.write(row, 3, item['occw_sku'])  # 订单行/产品 (SKU)
            worksheet.write(row, 4, item['qty'])  # 订单行/数量
            worksheet.write(row, 5, item['unit_price'])  # 订单行/单价
        
        workbook.close()
        output.seek(0)
        
        # 生成文件名：用户名_日期_quote.xlsx
        filename = f"{export_username}_{export_date}_quote.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/manual_excel')
def export_manual_excel():
    """导出手动创建的报价单 - 新6列格式"""
    try:
        manual_data = request.args.get('manual_data')
        export_date = request.args.get('export_date')
        export_username = request.args.get('export_username')
        export_sales_person = request.args.get('export_sales_person')
        
        if not manual_data:
            return jsonify({'error': 'No data provided'}), 400
        
        manual_data = json.loads(manual_data)
        
        # 创建Excel文件
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # 设置标题行 - 新6列格式
        headers = ['订单日期', '客户', '销售人员', '订单行/产品', '订单行/数量', '订单行/单价']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        for row, item in enumerate(manual_data, 1):
            # 第一行包含日期、客户、销售人员信息
            if row == 1:
                worksheet.write(row, 0, export_date)  # 订单日期
                worksheet.write(row, 1, export_username)  # 客户
                worksheet.write(row, 2, export_sales_person)  # 销售人员
            else:
                # 其他行为空
                worksheet.write(row, 0, '')
                worksheet.write(row, 1, '')
                worksheet.write(row, 2, '')
            
            # 产品信息
            worksheet.write(row, 3, item['sku'])  # 订单行/产品 (SKU)
            worksheet.write(row, 4, item['qty'])  # 订单行/数量
            worksheet.write(row, 5, float(item['price'].replace('$', '')))  # 订单行/单价
        
        workbook.close()
        output.seek(0)
        
        # 生成文件名：用户名_日期_quote.xlsx
        filename = f"{export_username}_{export_date}_quote.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
    return jsonify({'error': get_text('unsupported_export_format')}), 400



@app.route('/help')
def help():
    """帮助页面"""
    return render_template('help.html')

@app.route('/test_frontend')
def test_frontend():
    """前端API测试页面"""
    return render_template('test_frontend_issue.html')

@app.route('/debug_quotation')
def debug_quotation():
    """quotation_detail.html调试页面"""
    return render_template('debug_quotation.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录"""
    if request.method == 'POST':
        password = request.form.get('password')
        # 从系统设置中获取管理员密码，如果没有则使用默认密码
        admin_password = system_settings.get('admin_password', ADMIN_PASSWORD)
        if password == admin_password:
            session[ADMIN_SESSION_KEY] = True
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='密码错误')
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    """管理员登出"""
    session.pop(ADMIN_SESSION_KEY, None)
    return redirect(url_for('index'))

@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    """用户注册"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password or not email:
            return jsonify({'success': False, 'error': get_text('all_fields_required')})
        
        if username in users:
            return jsonify({'success': False, 'error': get_text('username_exists')})
        
        # 创建新用户
        users[username] = {
            'password_hash': hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        
        if save_users():
            return jsonify({'success': True, 'message': get_text('registration_success')})
        else:
            return jsonify({'success': False, 'error': get_text('registration_failed')})
    
    return render_template('user_register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    """用户登录"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': get_text('username_password_required')})
        
        if username not in users:
            return jsonify({'success': False, 'error': get_text('invalid_credentials')})
        
        if not verify_password(password, users[username]['password_hash']):
            return jsonify({'success': False, 'error': get_text('invalid_credentials')})
        
        session['username'] = username
        return jsonify({'success': True, 'message': get_text('login_success')})
    
    return render_template('user_login.html')

@app.route('/user_logout')
def user_logout():
    """用户登出"""
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/update_user_profile', methods=['POST'])
@login_required
def update_user_profile():
    """更新用户信息"""
    try:
        data = request.get_json()
        new_password = data.get('new_password', '').strip()
        username = session.get('username')
        
        if not username or username not in users:
            return jsonify({'success': False, 'error': get_text('user_not_found')})
        
        # 如果提供了新密码，则更新密码
        if new_password:
            if len(new_password) < 6:
                return jsonify({'success': False, 'error': get_text('password_too_short')})
            
            users[username]['password_hash'] = hash_password(new_password)
            
            if save_users():
                return jsonify({'success': True, 'message': get_text('password_updated_success')})
            else:
                return jsonify({'success': False, 'error': get_text('save_failed')})
        else:
            return jsonify({'success': False, 'error': get_text('no_changes_made')})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_language/<lang>')
def set_language_route(lang):
    """设置语言"""
    if set_language(lang):
        # 如果用户已登录，将语言偏好保存到用户信息中
        username = session.get('username')
        if username and username in users:
            users[username]['preferred_language'] = lang
            save_users()
        return jsonify({'success': True, 'language': lang})
    else:
        return jsonify({'success': False, 'error': 'Unsupported language'}), 400





@app.route('/prices')
@admin_required
def prices():
    """价格管理页面 - 重定向到管理员仪表板"""
    return redirect('/admin')

@app.route('/admin')
@admin_required
def admin_dashboard():
    """管理员仪表板页面"""
    return render_template('admin.html', system_settings=system_settings)

@app.route('/settings')
@login_required
def settings():
    """设置页面"""
    username = session.get('username')
    user_info = users.get(username, {}) if username else {}
    return render_template('settings.html', 
                         settings=system_settings, 
                         user_info=user_info,
                         today_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/save_settings', methods=['POST'])
@admin_required
def save_settings():
    """保存系统设置"""
    try:
        data = request.get_json()
        system_settings.update(data)
        if save_system_settings():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reset_settings', methods=['POST'])
@admin_required
def reset_settings():
    """重置系统设置"""
    try:
        global system_settings
        system_settings = {
            'default_sales_person': '',
            'sales_persons': [],
            'user_login_enabled': True,
            'admin_password': ADMIN_PASSWORD
        }
        if save_system_settings():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_system_settings', methods=['POST'])
@admin_required
def update_system_settings():
    """更新系统设置"""
    try:
        data = request.get_json()
        system_settings.update(data)
        if save_system_settings():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/change_admin_password', methods=['POST'])
@admin_required
def change_admin_password():
    """修改管理员密码"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': get_text('all_fields_required')})
        
        # 验证当前密码
        admin_password = system_settings.get('admin_password', ADMIN_PASSWORD)
        if current_password != admin_password:
            return jsonify({'success': False, 'error': get_text('current_password_incorrect')})
        
        # 验证新密码长度
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': get_text('password_too_short')})
        
        # 更新管理员密码
        system_settings['admin_password'] = new_password
        
        if save_system_settings():
            return jsonify({'success': True, 'message': get_text('admin_password_changed_success')})
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_sales_persons', methods=['GET'])
def get_sales_persons():
    """获取销售人员列表"""
    try:
        return jsonify({
            'success': True,
            'sales_persons': system_settings.get('sales_persons', [])
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_sales_person', methods=['POST'])
@admin_required
def add_sales_person():
    """添加销售人员"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'error': get_text('name_and_email_required')})
        
        # 检查是否已存在
        sales_persons = system_settings.get('sales_persons', [])
        for person in sales_persons:
            if person['name'] == name or person['email'] == email:
                return jsonify({'success': False, 'error': get_text('sales_person_already_exists')})
        
        # 添加新销售人员
        sales_persons.append({
            'name': name,
            'email': email
        })
        system_settings['sales_persons'] = sales_persons
        
        if save_system_settings():
            return jsonify({
                'success': True,
                'message': get_text('sales_person_added_success')
            })
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_sales_person', methods=['POST'])
@admin_required
def delete_sales_person():
    """删除销售人员"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': get_text('name_required')})
        
        # 删除销售人员
        sales_persons = system_settings.get('sales_persons', [])
        sales_persons = [person for person in sales_persons if person['name'] != name]
        system_settings['sales_persons'] = sales_persons
        
        if save_system_settings():
            return jsonify({
                'success': True,
                'message': get_text('sales_person_deleted_success')
            })
        else:
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_quotation', methods=['POST'])
@login_required
def save_quotation():
    """保存报价单"""
    try:
        data = request.get_json()
        username = session.get('username')
        title = data.get('title', '')
        quotation_data = data.get('data', {})
        
        print(f"保存报价单 - 用户: {username}, 标题: {title}")
        print(f"报价单数据: {quotation_data}")
        
        if not title:
            return jsonify({'success': False, 'error': get_text('quotation_title_required')})
        
        # 生成报价单编号
        quotation_id = generate_quotation_id()
        print(f"生成的报价单ID: {quotation_id}")
        
        # 简化数据结构，只保存6个核心信息
        simplified_data = {
            'type': quotation_data.get('type', 'manual'),  # pdf 或 manual
            'order_date': quotation_data.get('export_date', datetime.now().strftime('%Y-%m-%d')),
            'user': quotation_data.get('export_username', username),
            'sales_person': quotation_data.get('export_sales_person', ''),
            'products': []
        }
        
        # 处理产品数据，统一格式
        products = quotation_data.get('products', [])
        for product in products:
            # 清理SKU数据
            sku = product.get('sku', '').strip() if isinstance(product.get('sku', ''), str) else str(product.get('sku', ''))
            qty = int(product.get('qty', 1))
            
            # 统一价格格式为数字
            if quotation_data.get('type') == 'pdf':
                # PDF类型：直接使用unit_price
                price = float(product.get('unit_price', 0))
            else:
                # 手动创建：从price字段提取数字
                price_raw = product.get('price', '$0.00')
                if isinstance(price_raw, str):
                    # 移除$符号和空白字符，转换为数字
                    price_str = price_raw.strip().replace('$', '').replace('\n', '').replace('\r', '').replace(' ', '')
                    price = float(price_str) if price_str else 0.0
                else:
                    price = float(price_raw) if price_raw else 0.0
            
            simplified_product = {
                'sku': sku,
                'qty': qty,
                'price': price  # 统一保存为数字格式
            }
            simplified_data['products'].append(simplified_product)
        
        # 保存报价单
        if username not in quotations:
            quotations[username] = []
        
        quotation = {
            'quotation_id': quotation_id,
            'title': title,
            'data': simplified_data,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        quotations[username].append(quotation)
        print(f"已添加报价单到内存，当前用户报价单数量: {len(quotations[username])}")
        
        if save_quotations():
            print(f"报价单已保存到文件")
            return jsonify({
                'success': True, 
                'message': get_text('quotation_saved_success'),
                'quotation_id': quotation_id
            })
        else:
            print(f"保存报价单到文件失败")
            return jsonify({'success': False, 'error': get_text('save_failed')})
    except Exception as e:
        print(f"保存报价单异常: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_user_quotations', methods=['GET'])
@login_required
def get_user_quotations():
    """获取用户的报价单列表"""
    try:
        username = session.get('username')
        print(f"=== 调试信息 ===")
        print(f"当前session内容: {dict(session)}")
        print(f"当前登录用户: {username}")
        print(f"所有用户: {list(users.keys())}")
        print(f"所有报价单用户: {list(quotations.keys())}")
        
        if not username:
            print(f"错误: session中没有username")
            return jsonify({'success': False, 'error': '用户未登录'})
        
        if username not in quotations:
            print(f"错误: 用户 {username} 在quotations中不存在")
            return jsonify({'success': False, 'error': f'用户 {username} 没有报价单'})
        
        user_quotations = quotations.get(username, [])
        print(f"用户 {username} 的报价单数量: {len(user_quotations)}")
        print(f"用户 {username} 的报价单: {user_quotations}")
        
        return jsonify({
            'success': True,
            'quotations': user_quotations
        })
    except Exception as e:
        print(f"获取用户报价单异常: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_all_quotations', methods=['GET'])
@admin_required
def get_all_quotations():
    """获取所有用户的报价单列表（管理员专用）"""
    try:
        print(f"获取所有报价单 - 管理员: {session.get('username')}")
        print(f"所有报价单数据: {quotations}")
        return jsonify({
            'success': True,
            'quotations': quotations
        })
    except Exception as e:
        print(f"获取所有报价单异常: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_quotation/<quotation_id>', methods=['GET'])
def load_quotation(quotation_id):
    """加载指定报价单"""
    try:
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return jsonify({'success': False, 'error': get_text('login_required')})
        
        # 管理员可以加载所有报价单，普通用户只能加载自己的
        if is_admin_user:
            # 在所有用户的报价单中查找
            for user_name, user_quotations in quotations.items():
                for quotation in user_quotations:
                    if quotation['quotation_id'] == quotation_id:
                        return jsonify({
                            'success': True,
                            'quotation': quotation
                        })
        else:
            # 普通用户只能加载自己的报价单
            user_quotations = quotations.get(username, [])
            for quotation in user_quotations:
                if quotation['quotation_id'] == quotation_id:
                    return jsonify({
                        'success': True,
                        'quotation': quotation
                    })
        
        return jsonify({'success': False, 'error': get_text('quotation_not_found')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_quotation/<quotation_id>', methods=['POST'])
def update_quotation(quotation_id):
    """更新报价单"""
    try:
        data = request.get_json()
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        title = data.get('title', '')
        quotation_data = data.get('data', {})
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return jsonify({'success': False, 'error': get_text('login_required')})
        
        if not title:
            return jsonify({'success': False, 'error': get_text('quotation_title_required')})
        
        # 管理员可以更新所有报价单，普通用户只能更新自己的
        if is_admin_user:
            # 在所有用户的报价单中查找
            for user_name, user_quotations in quotations.items():
                for quotation in user_quotations:
                    if quotation['quotation_id'] == quotation_id:
                        quotation['title'] = title
                        quotation['data'] = quotation_data
                        quotation['updated_at'] = datetime.now().isoformat()
                        
                        if save_quotations():
                            return jsonify({
                                'success': True, 
                                'message': get_text('quotation_updated_success')
                            })
                        else:
                            return jsonify({'success': False, 'error': get_text('save_failed')})
        else:
            # 普通用户只能更新自己的报价单
            user_quotations = quotations.get(username, [])
            for quotation in user_quotations:
                if quotation['quotation_id'] == quotation_id:
                    quotation['title'] = title
                    quotation['data'] = quotation_data
                    quotation['updated_at'] = datetime.now().isoformat()
                    
                    if save_quotations():
                        return jsonify({
                            'success': True, 
                            'message': get_text('quotation_updated_success')
                        })
                    else:
                        return jsonify({'success': False, 'error': get_text('save_failed')})
        
        return jsonify({'success': False, 'error': get_text('quotation_not_found')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_quotation/<quotation_id>', methods=['POST'])
def delete_quotation(quotation_id):
    """删除报价单"""
    try:
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return jsonify({'success': False, 'error': get_text('login_required')})
        
        # 管理员可以删除所有报价单，普通用户只能删除自己的
        if is_admin_user:
            # 在所有用户的报价单中查找
            for user_name, user_quotations in quotations.items():
                for i, quotation in enumerate(user_quotations):
                    if quotation['quotation_id'] == quotation_id:
                        del user_quotations[i]
                        
                        if save_quotations():
                            return jsonify({
                                'success': True, 
                                'message': get_text('quotation_deleted_success')
                            })
                        else:
                            return jsonify({'success': False, 'error': get_text('delete_failed')})
        else:
            # 普通用户只能删除自己的报价单
            user_quotations = quotations.get(username, [])
            for i, quotation in enumerate(user_quotations):
                if quotation['quotation_id'] == quotation_id:
                    del user_quotations[i]
                    
                    if save_quotations():
                        return jsonify({
                            'success': True, 
                            'message': get_text('quotation_deleted_success')
                        })
                    else:
                        return jsonify({'success': False, 'error': get_text('delete_failed')})
        
        return jsonify({'success': False, 'error': get_text('quotation_not_found')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/view_quotation/<quotation_id>')
def view_quotation_detail(quotation_id):
    """查看报价单详情页面"""
    try:
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return redirect(url_for('user_login'))
        
        # 管理员可以查看所有报价单，普通用户只能查看自己的
        if is_admin_user:
            # 在所有用户的报价单中查找
            for user_name, user_quotations in quotations.items():
                for quotation in user_quotations:
                    if quotation['quotation_id'] == quotation_id:
                        # 清理报价单数据
                        cleaned_quotation = clean_quotation_data(quotation)
                        return render_template('quotation_detail.html', quotation=cleaned_quotation)
        else:
            # 普通用户只能查看自己的报价单
            user_quotations = quotations.get(username, [])
            for quotation in user_quotations:
                if quotation['quotation_id'] == quotation_id:
                    # 清理报价单数据
                    cleaned_quotation = clean_quotation_data(quotation)
                    return render_template('quotation_detail.html', quotation=cleaned_quotation)
        
        return render_template('quotation_detail.html', quotation=None, error=get_text('quotation_not_found'))
    except Exception as e:
        return render_template('quotation_detail.html', quotation=None, error=str(e))

def clean_quotation_data(quotation):
    """清理报价单数据，去除多余的空白字符，并计算总计"""
    if not quotation or 'data' not in quotation:
        return quotation
    
    cleaned_quotation = quotation.copy()
    cleaned_data = quotation['data'].copy()
    
    # 清理产品数据并计算总计
    total_amount = 0.0
    
    if 'products' in cleaned_data:
        cleaned_products = []
        for product in cleaned_data['products']:
            cleaned_product = product.copy()
            
            # 清理SKU
            if 'sku' in cleaned_product and isinstance(cleaned_product['sku'], str):
                cleaned_product['sku'] = cleaned_product['sku'].strip()
            
            # 处理价格并计算小计
            if 'price' in cleaned_product:
                # 统一处理价格（现在应该都是数字格式，但兼容旧数据）
                if isinstance(cleaned_product['price'], str):
                    # 处理旧数据中的字符串价格
                    price_str = cleaned_product['price'].strip()
                    price_value = float(price_str.replace('$', '').replace('\n', '').replace('\r', '').replace(' ', ''))
                else:
                    # 新数据中的数字价格
                    price_value = float(cleaned_product['price'])
                
                # 计算小计
                qty = int(cleaned_product.get('qty', 1))
                line_total = price_value * qty
                total_amount += line_total
                
                # 保存标准化的价格（数字格式）
                cleaned_product['price'] = price_value
                cleaned_product['line_total'] = line_total  # 添加小计字段
            
            cleaned_products.append(cleaned_product)
        
        cleaned_data['products'] = cleaned_products
    
    # 添加总计到报价单数据中
    cleaned_data['total_amount'] = total_amount
    cleaned_quotation['data'] = cleaned_data
    return cleaned_quotation

@app.route('/export_quotation/<quotation_id>')
def export_quotation_detail(quotation_id):
    """导出报价单"""
    try:
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return redirect(url_for('user_login'))
        
        # 管理员可以导出所有报价单，普通用户只能导出自己的
        if is_admin_user:
            # 在所有用户的报价单中查找
            for user_name, user_quotations in quotations.items():
                for quotation in user_quotations:
                    if quotation['quotation_id'] == quotation_id:
                        # 这里可以根据报价单类型调用相应的导出函数
                        quotation_data = quotation.get('data', {})
                        if quotation_data.get('type') == 'pdf':
                            # PDF类型的报价单导出
                            return export_pdf_quotation(quotation_data)
                        else:
                            # 手动创建的报价单导出
                            return export_manual_quotation(quotation_data)
        else:
            # 普通用户只能导出自己的报价单
            user_quotations = quotations.get(username, [])
            for quotation in user_quotations:
                if quotation['quotation_id'] == quotation_id:
                    # 这里可以根据报价单类型调用相应的导出函数
                    quotation_data = quotation.get('data', {})
                    if quotation_data.get('type') == 'pdf':
                        # PDF类型的报价单导出
                        return export_pdf_quotation(quotation_data)
                    else:
                        # 手动创建的报价单导出
                        return export_manual_quotation(quotation_data)
        
        return jsonify({'success': False, 'error': get_text('quotation_not_found')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def export_pdf_quotation(quotation_data):
    """导出PDF类型的报价单"""
    try:
        products = quotation_data.get('products', [])
        export_date = quotation_data.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        export_username = quotation_data.get('user', '')
        export_sales_person = quotation_data.get('sales_person', '')
        
        # 构造导出参数，使用原有的导出格式
        occw_data = []
        for i, product in enumerate(products, 1):
            occw_data.append({
                'seq_num': str(i),
                'occw_sku': product.get('sku', ''),
                'qty': str(product.get('qty', 1)),
                'unit_price': product.get('price', 0),
                'total_price': product.get('price', 0) * product.get('qty', 1)
            })
        
        # 构造URL参数
        from urllib.parse import urlencode
        params = {
            'occw_data': json.dumps(occw_data),
            'export_date': export_date,
            'export_username': export_username,
            'export_sales_person': export_sales_person
        }
        
        # 重定向到原有的导出接口
        return redirect(f'/export/occw_excel?{urlencode(params)}')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def export_manual_quotation(quotation_data):
    """导出手动创建的报价单"""
    try:
        products = quotation_data.get('products', [])
        export_date = quotation_data.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        export_username = quotation_data.get('user', '')
        export_sales_person = quotation_data.get('sales_person', '')
        
        # 构造导出参数，使用原有的导出格式
        manual_data = []
        for i, product in enumerate(products, 1):
            manual_data.append({
                'seq_num': str(i),
                'category': '',
                'product': '',
                'box_variant': '',
                'door_variant': '',
                'sku': product.get('sku', ''),
                'price': product.get('price', '$0.00'),
                'qty': str(product.get('qty', 1))
            })
        
        # 构造URL参数
        from urllib.parse import urlencode
        params = {
            'manual_data': json.dumps(manual_data),
            'export_date': export_date,
            'export_username': export_username,
            'export_sales_person': export_sales_person
        }
        
        # 重定向到原有的导出接口
        return redirect(f'/export/manual_excel?{urlencode(params)}')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_pdf_text')
def get_pdf_text():
    """获取PDF识别的原始文本"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': get_text('no_filename_specified')}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': get_text('file_not_exists')}), 404
    
    try:
        # 返回原始PDF文本（不添加页面分隔符）
        pdf_content = extract_pdf_content(filepath, add_page_markers=False)
        return jsonify({
            'success': True,
            'text': pdf_content
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("read_pdf_failed")}: {str(e)}'}), 500

@app.route('/get_product_categories', methods=['GET'])
def get_product_categories():
    """获取产品类别列表"""
    try:
        categories = set()
        for item in occw_prices.keys():
            # 从现有的OCCW价格表中提取类别信息
            # 这里需要根据实际的数据结构来分析
            pass
        
        # 暂时返回预定义的类别
        default_categories = [
            "Assm.组合件",
            "Door", 
            "BOX",
            "ENDING PANEL",
            "MOLDING", 
            "TOE KICK",
            "FILLER",
            "HARDWARE"
        ]
        
        return jsonify({
            'success': True,
            'categories': default_categories
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("get_categories_failed")}: {str(e)}'}), 500

@app.route('/get_products_by_category', methods=['GET'])
def get_products_by_category():
    """根据类别获取产品列表 - 使用结构化数据"""
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': get_text('missing_category_param')}), 400
        
        products = set()
        box_variants = set()
        door_variants = set()
        
        # 从OCCW价格表中提取结构化数据
        for sku, price_data in occw_prices.items():
            if not isinstance(price_data, dict):
                continue  # 跳过旧格式数据
            
            # 获取产品信息
            product_category = price_data.get('category', '').strip()
            product_name = price_data.get('product_name', '').strip()
            door_variant = price_data.get('door_variant', '').strip()
            box_variant = price_data.get('box_variant', '').strip()
            
            # 只处理匹配类别的产品
            if product_category == category:
                if product_name:
                    products.add(product_name)
                if door_variant:
                    door_variants.add(door_variant)
                if box_variant:
                    box_variants.add(box_variant)
        
        # 如果请求的类别在价格表中没有数据，提供默认选项
        if not products and not door_variants and not box_variants:
            # 根据类别提供默认的变体选项
            if category in ["Door", "Assm.组合件", "BOX", "ENDING PANEL", "MOLDING", "TOE KICK", "FILLER"]:
                door_variants = {'BSS', 'GSS', 'MNW', 'MWM', 'PGW', 'SSW', 'WSS'}
            
            if category in ["Assm.组合件", "BOX"]:
                box_variants = {'PLY', 'PB'}
            
            # 为某些类别提供默认产品选项
            if category == "ENDING PANEL":
                products = {'PANEL-24', 'PANEL-36', 'PANEL-48'}
            elif category == "MOLDING":
                products = {'CROWN-M', 'LIGHT-RAIL', 'SCRIBE-M'}
            elif category == "TOE KICK":
                products = {'TOE-4.5', 'TOE-6', 'TOE-8'}
            elif category == "FILLER":
                products = {'FILLER-3', 'FILLER-6', 'FILLER-9'}
        
        # 根据类别调整返回的变体选项
        if category == "Door":
            # 门板产品不需要柜身变体
            box_variants = set()
        elif category == "HARDWARE":
            # 五金件不需要变体
            door_variants = set()
            box_variants = set()
        elif category in ["ENDING PANEL", "MOLDING", "TOE KICK", "FILLER"]:
            # 配件只需要门板变体
            box_variants = set()
        
        return jsonify({
            'success': True,
            'products': sorted(list(products)),
            'box_variants': sorted(list(box_variants)),
            'door_variants': sorted(list(door_variants))
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("get_products_failed")}: {str(e)}'}), 500

@app.route('/search_sku_price', methods=['GET'])
def search_sku_price():
    """根据产品信息搜索SKU和价格"""
    try:
        category = request.args.get('category', '')
        product = request.args.get('product', '')
        box_variant = request.args.get('box_variant', '')
        door_variant = request.args.get('door_variant', '')
        
        # 根据产品信息生成可能的SKU
        possible_skus = generate_possible_skus(category, product, box_variant, door_variant)
        
        # 在OCCW价格表中查找匹配的SKU和价格
        found_sku = None
        found_price = 0.0
        
        # 精确匹配
        for sku in possible_skus:
            if sku in occw_prices:
                found_sku = sku
                # 处理新旧数据格式兼容性
                price_data = occw_prices[sku]
                if isinstance(price_data, dict):
                    found_price = price_data.get('unit_price', 0)
                else:
                    found_price = price_data
                break
        
        # 如果没有找到精确匹配，尝试模糊匹配
        if not found_sku and product:
            for sku in occw_prices.keys():
                # 检查产品名是否在SKU中
                if product in sku:
                    # 进一步检查门板变体（如果指定了的话）
                    if door_variant and door_variant in sku:
                        found_sku = sku
                        # 处理新旧数据格式兼容性
                        price_data = occw_prices[sku]
                        if isinstance(price_data, dict):
                            found_price = price_data.get('unit_price', 0)
                        else:
                            found_price = price_data
                        break
                    elif not door_variant:
                        found_sku = sku
                        # 处理新旧数据格式兼容性
                        price_data = occw_prices[sku]
                        if isinstance(price_data, dict):
                            found_price = price_data.get('unit_price', 0)
                        else:
                            found_price = price_data
                        break
        
        return jsonify({
            'success': True,
            'sku': found_sku,
            'price': found_price,
            'found': found_sku is not None,
            'possible_skus': possible_skus  # 调试信息
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("search_sku_failed")}: {str(e)}'}), 500

@app.route('/get_occw_price_table', methods=['GET'])
@admin_required
def get_occw_price_table():
    """获取OCCW价格表内容 - 支持多种过滤条件"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # 获取过滤条件
        search_sku = request.args.get('search_sku', '').strip()
        door_variant = request.args.get('door_variant', '').strip()
        box_variant = request.args.get('box_variant', '').strip()
        category = request.args.get('category', '').strip()
        
        # 兼容老版本的通用搜索
        search = request.args.get('search', '').strip()
        
        # 获取所有价格数据
        all_prices = []
        for sku, price_data in occw_prices.items():
            # 应用过滤条件
            should_include = True
            
            if isinstance(price_data, dict):
                product_data = {
                    'sku': sku.upper(),
                    'product_name': price_data.get('product_name', '').upper(),
                    'category': price_data.get('category', '').upper(),
                    'door_variant': price_data.get('door_variant', '').upper(),
                    'box_variant': price_data.get('box_variant', '').upper()
                }
            else:
                product_data = {
                    'sku': sku.upper(),
                    'product_name': '',
                    'category': '',
                    'door_variant': '',
                    'box_variant': ''
                }
            
            # SKU搜索过滤
            if search_sku and search_sku.upper() not in product_data['sku']:
                should_include = False
            
            # 门板变体过滤
            if door_variant and door_variant.upper() != product_data['door_variant']:
                should_include = False
            
            # 柜身变体过滤
            if box_variant and box_variant.upper() != product_data['box_variant']:
                should_include = False
            
            # 类别过滤
            if category and category.upper() != product_data['category']:
                should_include = False
            
            # 兼容通用搜索（在所有字段中搜索）
            if search and not any(search.upper() in field for field in product_data.values()):
                should_include = False
            
            if not should_include:
                continue
            
            # 处理新旧数据格式兼容性
            if isinstance(price_data, dict):
                # 新格式：完整产品信息
                all_prices.append({
                    'sku': sku,
                    'product_name': price_data.get('product_name', ''),
                    'door_variant': price_data.get('door_variant', ''),
                    'box_variant': price_data.get('box_variant', ''),
                    'category': price_data.get('category', ''),
                    'price': price_data.get('unit_price', 0)
                })
            else:
                # 旧格式：只有价格
                all_prices.append({
                    'sku': sku,
                    'product_name': '',
                    'door_variant': '',
                    'box_variant': '',
                    'category': '',
                    'price': price_data
                })
        
        # 排序
        all_prices.sort(key=lambda x: x['sku'])
        
        # 分页
        total = len(all_prices)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_prices = all_prices[start:end]
        
        return jsonify({
            'success': True,
            'data': paginated_prices,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("get_price_table_failed")}: {str(e)}'}), 500

@app.route('/get_price_filter_options', methods=['GET'])
@admin_required
def get_price_filter_options():
    """获取价格表过滤选项"""
    try:
        door_variants = set()
        box_variants = set()
        categories = set()
        
        for sku, price_data in occw_prices.items():
            if isinstance(price_data, dict):
                door_variant = price_data.get('door_variant', '').strip()
                box_variant = price_data.get('box_variant', '').strip()
                category = price_data.get('category', '').strip()
                
                if door_variant:
                    door_variants.add(door_variant)
                if box_variant:
                    box_variants.add(box_variant)
                if category:
                    categories.add(category)
        
        return jsonify({
            'success': True,
            'data': {
                'door_variants': sorted(list(door_variants)),
                'box_variants': sorted(list(box_variants)),
                'categories': sorted(list(categories))
            }
        })
    except Exception as e:
        return jsonify({'error': f'{get_text("get_filter_options_failed")}: {str(e)}'}), 500

# 确保目录存在
for directory in ['uploads', 'data']:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")

# 初始化数据（无论如何都要加载）
load_standard_prices()
load_occw_prices()
load_sku_mappings()
print(f"已加载 {len(occw_prices)} 个OCCW价格")
print(f"已加载 {len(sku_mappings)} 个SKU映射关系")

if __name__ == '__main__':
    # 加载数据
    load_standard_prices()
    load_occw_prices()
    load_sku_mappings()
    load_system_settings()
    load_users()
    load_quotations()
    
    # 生产环境配置
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug) 