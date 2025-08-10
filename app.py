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
from flask_babel import Babel, gettext as _, lazy_gettext as _l
from version import VERSION, VERSION_NAME, COMPANY_NAME_ZH, COMPANY_NAME_EN, SYSTEM_NAME_ZH, SYSTEM_NAME_EN, SYSTEM_NAME_FR
from translations import get_text
from typing import Dict, List, Tuple, Any
from io import BytesIO
import xlsxwriter
import hashlib
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 立即配置Jinja2定界符，避免与JavaScript模板语法冲突
app.jinja_env.variable_start_string = '[['
app.jinja_env.variable_end_string = ']]'
app.jinja_env.block_start_string = '[%'
app.jinja_env.block_end_string = '%]'
app.jinja_env.comment_start_string = '[#'
app.jinja_env.comment_end_string = '#]'

# 配置Jinja2定界符，避免与JavaScript模板语法冲突
# 配置Jinja2定界符，避免与JavaScript模板语法冲突
app.config['JINJA2_ENVIRONMENT_OPTIONS'] = {
    'variable_start_string': '[[',
    'variable_end_string': ']]',
    'block_start_string': '[%',
    'block_end_string': '%]',
    'comment_start_string': '[#',
    'comment_end_string': '#]'
}

def configure_jinja2_delimiters():
    """配置Jinja2定界符（备用方法）"""
    app.jinja_env.variable_start_string = '[['
    app.jinja_env.variable_end_string = ']]'
    app.jinja_env.block_start_string = '[%'
    app.jinja_env.block_end_string = '%]'
    app.jinja_env.comment_start_string = '[#'
    app.jinja_env.comment_end_string = '#]'

# 立即配置定界符
configure_jinja2_delimiters()

# Babel配置
app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['LANGUAGES'] = {
    'zh': '中文',
    'en': 'English',
    'fr': 'Français'
}

# 初始化Babel
babel = Babel(app)

# 应用启动后的回调，确保Jinja2定界符配置
@app.before_request
def ensure_jinja2_delimiters():
    """确保Jinja2定界符配置正确"""
    if not hasattr(app, '_jinja2_delimiters_configured'):
        configure_jinja2_delimiters()
        app._jinja2_delimiters_configured = True

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 数据加载将在应用启动时进行

# 管理员配置
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin123')  # 支持环境变量
ADMIN_SESSION_KEY = "is_admin"

# 语言支持
def get_current_language():
    """获取当前语言"""
    return session.get('language', app.config['BABEL_DEFAULT_LOCALE'])

def set_language(lang):
    """设置语言"""
    if lang in app.config['LANGUAGES']:
        session['language'] = lang
        # 清除自动检测标记，表示用户已手动设置语言
        session.pop('auto_detected', None)
        return True
    return False

def get_locale():
    """获取当前语言环境"""
    # 优先使用session中保存的语言
    if 'language' in session:
        return session['language']
    
    # 如果没有设置，使用浏览器语言
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_globals():
    """向模板注入全局变量"""
    current_lang = get_current_language()
    return {
        'current_language': current_lang,
        'supported_languages': app.config['LANGUAGES'],
        'version': VERSION,
        'version_name': VERSION_NAME,
        'company_name_zh': COMPANY_NAME_ZH,
        'company_name_en': COMPANY_NAME_EN,
        'system_name_zh': SYSTEM_NAME_ZH,
        'system_name_en': SYSTEM_NAME_EN,
        'system_name_fr': SYSTEM_NAME_FR,
        'system_settings': system_settings,
        't': lambda key: get_text(key, current_lang)  # 使用自定义翻译函数
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
                return jsonify({'error': _('admin_required'), 'redirect': '/admin_login'}), 401
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
        print(f"提取PDF内容失败: {e}")
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
            compare_message = f"✅ {_('parsing_total_matches_pdf')}: {calc_total:.2f}"
        else:
            compare_result = False
            compare_message = f"❌ {_('parsing_total_mismatch_pdf').format(calc_total=calc_total, pdf_total=pdf_total)}"
    else:
        compare_result = None
        compare_message = _("⚠️ 未识别到PDF合计金额，无法比对！")
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

            
            # 检查必需的列
            required_columns = ['内部参考号', '销售价', '变体值', '名称', '产品类别/名称']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Excel文件缺少必需的列: {', '.join(missing_columns)}"
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
                    self.errors.append(error_msg)
            
            return transformed_data, self.errors
            
        except Exception as e:
            error_msg = f"文件读取失败: {str(e)}"
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

def parse_product_segment(segment, current_door_color, products):
    """解析产品段落（可能包含多个产品）"""

    
    # 查找所有可能的产品模式，包括包含*号的序号
    # 改进正则表达式以更好地处理包含页面信息的产品行
    product_patterns = re.findall(r'([A-Z0-9]+)\s+(\*?\d+)\s+([^0-9]+?)\s+(\d+,?\d*\.\d{2})\s+(\d+[A-Z0-9]+)', segment)
    
    if not product_patterns:
        # 如果没有找到标准模式，尝试更宽松的匹配

        
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
        
                break
        
        # 如果仍然没有找到，尝试手动解析特殊格式
        if not product_patterns:
    
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
                
                        except (IndexError, ValueError) as e:
                            
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
        return jsonify({'error': _('no_file_selected')}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': _('no_file_selected')}), 400
    
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
    
    return jsonify({'error': _('upload_pdf_file')}), 400

@app.route('/upload_prices', methods=['POST'])
def upload_prices():
    """上传标准价格表"""
    if 'file' not in request.files:
        return jsonify({'error': _('no_file_selected')}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': _('no_file_selected')}), 400
    
    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'error': _('upload_excel_csv')}), 400
        
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
        return jsonify({'error': f'{_("file_processing_failed")}: {str(e)}'}), 400

@app.route('/upload_occw_prices', methods=['POST'])
@admin_required 
def upload_occw_prices():
    """上传OCCW价格表 - 完全重写版本"""
    
    
    try:
        # 1. 验证文件
        if 'file' not in request.files:
            error_msg = '没有选择文件'
            return jsonify({'success': False, 'error': error_msg}), 400
        
        file = request.files['file']
        if file.filename == '':
            error_msg = '没有选择文件'
            return jsonify({'success': False, 'error': error_msg}), 400
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            error_msg = '文件格式不支持，请选择Excel文件(.xlsx或.xls)'
            return jsonify({'success': False, 'error': error_msg}), 400
        

        
        # 2. 获取导入模式
        import_mode = request.form.get('import_mode', 'create')
        clear_existing = import_mode == 'create'

        
        # 3. 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), f"occw_upload_{filename}")
        file.save(temp_path)

        
        try:
            # 4. 使用转换器处理Excel文件

            transformer = OCCWPriceTransformer()
            transformed_data, errors = transformer.transform_excel_file(temp_path)
            

            
            # 5. 如果没有有效数据（全部行都解析失败）
            if not transformed_data:
                if errors:
                    error_msg = f'所有数据行解析失败，发现 {len(errors)} 个错误'
                else:
                    error_msg = '没有有效的价格数据'
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
            

            
            if clear_existing:
                occw_prices.clear()

            
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

            
            # 8. 保存到文件
            if save_occw_prices():

                
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
                return jsonify({'success': False, 'error': error_msg}), 500
                
        finally:
            # 9. 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

                
    except Exception as e:
        error_msg = f'处理文件时发生错误: {str(e)}'

        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': error_msg}), 500

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
        return jsonify({'error': f'{_("get_sku_list_failed")}: {str(e)}'}), 500

@app.route('/save_sku_mapping', methods=['POST'])
@admin_required
def save_sku_mapping():
    """保存SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        mapped_sku = data.get('mapped_sku')
        
        if not original_sku or not mapped_sku:
            return jsonify({'error': _('missing_required_params')}), 400
        
        global sku_mappings
        sku_mappings[original_sku] = mapped_sku
        
        if save_sku_mappings():
            # 返回映射的SKU对应的价格（处理新旧数据格式兼容性）
            price_data = occw_prices.get(mapped_sku, 0.0)
            
            # 调试：打印价格数据信息
            
            
            # 处理新旧数据格式兼容性
            if isinstance(price_data, dict):
                # 新格式：完整产品信息
                occw_price = price_data.get('unit_price', 0.0)
    
            else:
                # 旧格式：只有价格
                occw_price = price_data

            
            # 确保价格是数字类型
            try:
                occw_price = float(occw_price) if occw_price is not None else 0.0
            except (ValueError, TypeError):
                occw_price = 0.0
            
    
            
            return jsonify({
                'success': True,
                'message': _('映射关系保存成功'),
                'occw_price': occw_price
            })
        else:
            return jsonify({'error': _('save_mapping_failed')}), 500
            
    except Exception as e:
        return jsonify({'error': f'{_("save_mapping_failed")}: {str(e)}'}), 500

@app.route('/get_occw_price', methods=['GET'])
def get_occw_price():
    """获取指定SKU的OCCW价格"""
    try:
        sku = request.args.get('sku')
        if not sku:
            return jsonify({'error': _('missing_sku_param')}), 400
        
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
        return jsonify({'error': f'{_("get_price_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{_("get_stats_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{_("get_mapping_failed")}: {str(e)}'}), 500

@app.route('/delete_sku_mapping', methods=['POST'])
@admin_required
def delete_sku_mapping():
    """删除SKU映射关系"""
    try:
        data = request.get_json()
        original_sku = data.get('original_sku')
        
        if not original_sku:
            return jsonify({'error': _('missing_original_sku')}), 400
        
        global sku_mappings
        if original_sku in sku_mappings:
            del sku_mappings[original_sku]
            
            if save_sku_mappings():
                return jsonify({
                    'success': True,
                    'message': _('映射关系已删除')
                })
            else:
                return jsonify({'error': _('保存映射关系失败')}), 500
        else:
            return jsonify({'error': _('mapping_not_exists')}), 404
            
    except Exception as e:
        return jsonify({'error': f'{_("delete_mapping_failed")}: {str(e)}'}), 500

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
            return jsonify({'error': _('保存映射关系失败')}), 500
            
    except Exception as e:
        return jsonify({'error': f'{_("clear_mapping_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{_("export_mapping_failed")}: {str(e)}'}), 500

@app.route('/sku_mappings')
@admin_required
def sku_mappings_page():
    """SKU映射管理页面"""
    return render_template('sku_mappings.html')

@app.route('/export/occw_excel')
def export_occw_excel():
    """导出OCCW格式的Excel文件 - 新5列格式（移除单价列）"""
    try:
        occw_data = request.args.get('occw_data')
        export_date = request.args.get('export_date')
        export_username = request.args.get('export_username')
        export_sales_person = request.args.get('export_sales_person')
        
        # 检查用户登录功能是否被禁用，如果被禁用且没有提供用户名和销售人员，使用默认值
        user_login_enabled = system_settings.get('user_login_enabled', True)
        if not user_login_enabled:
            if not export_username:
                export_username = 'Public User'
            if not export_sales_person:
                export_sales_person = get_default_sales_person()
        
        if not occw_data:
            return jsonify({'error': _('No data provided')}), 400
        
        occw_data = json.loads(occw_data)
        
        # 创建Excel文件
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # 设置标题行 - 新5列格式（移除单价列）
        headers = ['订单日期', '客户', '销售人员', '订单行/产品', '订单行/数量']
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

@app.route('/export/manual_excel', methods=['GET', 'POST'])
def export_manual_excel():
    """导出手动创建的报价单 - 新5列格式（移除单价列）"""
    try:
        # 支持GET和POST请求
        if request.method == 'POST':
            # 处理表单数据
            manual_data = request.form.get('manual_data')
            export_date = request.form.get('export_date')
            export_username = request.form.get('export_username')
            export_sales_person = request.form.get('export_sales_person')
        else:
            # 处理GET请求参数
            manual_data = request.args.get('manual_data')
            export_date = request.args.get('export_date')
            export_username = request.args.get('export_username')
            export_sales_person = request.args.get('export_sales_person')
        
        # 检查用户登录功能是否被禁用，如果被禁用且没有提供用户名和销售人员，使用默认值
        user_login_enabled = system_settings.get('user_login_enabled', True)
        if not user_login_enabled:
            if not export_username:
                export_username = 'Public User'
            if not export_sales_person:
                export_sales_person = get_default_sales_person()
        
        if not manual_data:
            return jsonify({'error': _('No data provided')}), 400
        
        manual_data = json.loads(manual_data)
        
        # 创建Excel文件
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # 设置标题行 - 新5列格式（移除单价列）
        headers = ['订单日期', '客户', '销售人员', '订单行/产品', '订单行/数量']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # 写入数据
        for row, item in enumerate(manual_data, 1):
            # 第一行包含日期、客户、销售人员信息，其他行为空
            if row == 1:
                worksheet.write(row, 0, export_date)  # 订单日期
                worksheet.write(row, 1, export_username)  # 客户
                worksheet.write(row, 2, export_sales_person)  # 销售人员
            else:
                # 其他行的日期、客户、销售人员列为空
                worksheet.write(row, 0, '')  # 订单日期
                worksheet.write(row, 1, '')  # 客户
                worksheet.write(row, 2, '')  # 销售人员
            
            # 产品信息（每行都有完整数据）
            worksheet.write(row, 3, item['sku'])  # 订单行/产品 (SKU)
            worksheet.write(row, 4, item['qty'])  # 订单行/数量
        
        workbook.close()
        output.seek(0)
        
        # 生成文件名：用户名_日期_quote.xlsx
        filename = f"{export_username}_{export_date}_quote.xlsx"
        
        # 统一使用send_file返回，确保文件格式正确
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
    
    return jsonify({'error': _('unsupported_export_format')}), 400



@app.route('/help')
def help():
    """帮助页面 - 根据语言选择返回相应的帮助文件"""
    current_lang = get_current_language()
    
    # 根据当前语言选择相应的帮助模板
    if current_lang == 'en':
        template_name = 'help_en.html'
    elif current_lang == 'fr':
        template_name = 'help_fr.html'
    else:
        # 默认使用中文帮助文件
        template_name = 'help.html'
    
    return render_template(template_name)

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
            return render_template('admin_login.html', error=_('密码错误'))
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
            return jsonify({'success': False, 'error': _('all_fields_required')})
        
        if username in users:
            return jsonify({'success': False, 'error': _('username_exists')})
        
        # 创建新用户
        users[username] = {
            'password_hash': hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        
        if save_users():
            return jsonify({'success': True, 'message': _('registration_success')})
        else:
            return jsonify({'success': False, 'error': _('registration_failed')})
    
    return render_template('user_register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    """用户登录"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': _('username_password_required')})
        
        if username not in users:
            return jsonify({'success': False, 'error': _('invalid_credentials')})
        
        if not verify_password(password, users[username]['password_hash']):
            return jsonify({'success': False, 'error': _('invalid_credentials')})
        
        session['username'] = username
        return jsonify({'success': True, 'message': _('login_success')})
    
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
            return jsonify({'success': False, 'error': _('user_not_found')})
        
        # 如果提供了新密码，则更新密码
        if new_password:
            if len(new_password) < 6:
                return jsonify({'success': False, 'error': _('password_too_short')})
            
            users[username]['password_hash'] = hash_password(new_password)
            
            if save_users():
                return jsonify({'success': True, 'message': _('password_updated_success')})
            else:
                return jsonify({'success': False, 'error': _('save_failed')})
        else:
            return jsonify({'success': False, 'error': _('no_changes_made')})
            
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
        return jsonify({'success': False, 'error': _('Unsupported language')}), 400





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
            return jsonify({'success': False, 'error': _('save_failed')})
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
            return jsonify({'success': False, 'error': _('save_failed')})
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
            return jsonify({'success': False, 'error': _('save_failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_system_settings', methods=['GET'])
def get_system_settings():
    """获取系统设置"""
    try:
        return jsonify(system_settings)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_import_filter_settings', methods=['POST'])
@admin_required
def save_import_filter_settings():
    """保存导入过滤设定"""
    try:
        data = request.get_json()
        
        # 更新系统设置中的导入过滤设定
        for key, value in data.items():
            if key.startswith('import_filter_'):
                system_settings[key] = value
        
        if save_system_settings():
            return jsonify({'success': True, 'message': _('导入过滤设定保存成功')})
        else:
            return jsonify({'success': False, 'error': _('保存失败')})
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_import_filters', methods=['GET'])
@admin_required
def get_import_filters():
    """获取导入过滤设置"""
    try:
        # 提取所有以import_filter_开头的设置
        filters = {}
        for key, value in system_settings.items():
            if key.startswith('import_filter_'):
                filters[key] = value
        
        # 如果没有设置，返回默认值
        if not filters:
            filters = {
                'import_filter_min_amount': 1000,
                'import_filter_start_date': None,
                'import_filter_end_date': None,
                'import_filter_sales_person': None,
                'import_filter_customer': None,
                'import_filter_order_status': '销售订单,报价单,已发送报价单'
            }
        
        return jsonify({'success': True, 'filters': filters})
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_import_filters', methods=['POST'])
@admin_required 
def save_import_filters():
    """保存导入过滤设置"""
    try:
        data = request.get_json()
        
        # 更新系统设置中的导入过滤设定
        for key, value in data.items():
            if key.startswith('import_filter_'):
                # 处理空值和None值
                if value == '' or value is None:
                    system_settings[key] = None
                else:
                    system_settings[key] = value
        
        if save_system_settings():
            return jsonify({'success': True, 'message': _('导入过滤设置保存成功')})
        else:
            return jsonify({'success': False, 'error': _('保存失败')})
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
            return jsonify({'success': False, 'error': _('all_fields_required')})
        
        # 验证当前密码
        admin_password = system_settings.get('admin_password', ADMIN_PASSWORD)
        if current_password != admin_password:
            return jsonify({'success': False, 'error': _('current_password_incorrect')})
        
        # 验证新密码长度
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': _('password_too_short')})
        
        # 更新管理员密码
        system_settings['admin_password'] = new_password
        
        if save_system_settings():
            return jsonify({'success': True, 'message': _('admin_password_changed_success')})
        else:
            return jsonify({'success': False, 'error': _('save_failed')})
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

@app.route('/get_order_statuses', methods=['GET'])
def get_order_statuses():
    """获取所有订单状态列表（从已上传的数据中提取）"""
    try:
        # 优先从转换后数据获取（因为这是用户实际看到的数据）
        if 'converted_data_file' in session and os.path.exists(session['converted_data_file']):
    
            with open(session['converted_data_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        # 其次尝试从原始导入数据获取
        elif 'imported_data_file' in session and os.path.exists(session['imported_data_file']):
    
            with open(session['imported_data_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:
            # 如果没有session数据，尝试从upload文件夹读取
    
            file_path = os.path.join('upload', '销售订单.xlsx')
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
            else:
        
                return jsonify([])
        
        # 获取订单状态列表，去除空值和重复值
        if '订单状态' in df.columns:
            order_statuses = df['订单状态'].dropna().unique().tolist()
            # 过滤掉NaN和空字符串，并排序
            order_statuses = sorted([str(status) for status in order_statuses 
                                   if str(status) != 'nan' and str(status).strip() != ''])
    
            return jsonify(order_statuses)
        else:
    
            return jsonify([])
    except Exception as e:
        import traceback
        return jsonify([])

@app.route('/add_sales_person', methods=['POST'])
@admin_required
def add_sales_person():
    """添加销售人员"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name or not email:
            return jsonify({'success': False, 'error': _('name_and_email_required')})
        
        # 检查是否已存在
        sales_persons = system_settings.get('sales_persons', [])
        for person in sales_persons:
            if person['name'] == name or person['email'] == email:
                return jsonify({'success': False, 'error': _('sales_person_already_exists')})
        
        # 添加新销售人员
        sales_persons.append({
            'name': name,
            'email': email
        })
        system_settings['sales_persons'] = sales_persons
        
        if save_system_settings():
            return jsonify({
                'success': True,
                'message': _('sales_person_added_success')
            })
        else:
            return jsonify({'success': False, 'error': _('save_failed')})
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
            return jsonify({'success': False, 'error': _('name_required')})
        
        # 删除销售人员
        sales_persons = system_settings.get('sales_persons', [])
        sales_persons = [person for person in sales_persons if person['name'] != name]
        system_settings['sales_persons'] = sales_persons
        
        if save_system_settings():
            return jsonify({
                'success': True,
                'message': _('sales_person_deleted_success')
            })
        else:
            return jsonify({'success': False, 'error': _('save_failed')})
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
        

        
        if not title:
            return jsonify({'success': False, 'error': _('quotation_title_required')})
        
        # 生成报价单编号
        quotation_id = generate_quotation_id()

        
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

        
        if save_quotations():

            return jsonify({
                'success': True, 
                'message': _('quotation_saved_success'),
                'quotation_id': quotation_id
            })
        else:

            return jsonify({'success': False, 'error': _('save_failed')})
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_user_quotations', methods=['GET'])
@login_required
def get_user_quotations():
    """获取用户的报价单列表"""
    try:
        username = session.get('username')

        
        if not username:

            return jsonify({'success': False, 'error': _('用户未登录')})
        
        if username not in quotations:

            return jsonify({'success': False, 'error': f'用户 {username} 没有报价单'})
        
        user_quotations = quotations.get(username, [])

        
        return jsonify({
            'success': True,
            'quotations': user_quotations
        })
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_all_quotations', methods=['GET'])
@admin_required
def get_all_quotations():
    """获取所有用户的报价单列表（管理员专用）"""
    try:

        return jsonify({
            'success': True,
            'quotations': quotations
        })
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)})

@app.route('/load_quotation/<quotation_id>', methods=['GET'])
def load_quotation(quotation_id):
    """加载指定报价单"""
    try:
        username = session.get('username')
        is_admin_user = session.get('is_admin', False)
        
        # 检查用户是否登录（管理员或普通用户）
        if not username and not is_admin_user:
            return jsonify({'success': False, 'error': _('login_required')})
        
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
        
        return jsonify({'success': False, 'error': _('quotation_not_found')})
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
            return jsonify({'success': False, 'error': _('login_required')})
        
        if not title:
            return jsonify({'success': False, 'error': _('quotation_title_required')})
        
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
                                'message': _('quotation_updated_success')
                            })
                        else:
                            return jsonify({'success': False, 'error': _('save_failed')})
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
                            'message': _('quotation_updated_success')
                        })
                    else:
                        return jsonify({'success': False, 'error': _('save_failed')})
        
        return jsonify({'success': False, 'error': _('quotation_not_found')})
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
            return jsonify({'success': False, 'error': _('login_required')})
        
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
                                'message': _('quotation_deleted_success')
                            })
                        else:
                            return jsonify({'success': False, 'error': _('delete_failed')})
        else:
            # 普通用户只能删除自己的报价单
            user_quotations = quotations.get(username, [])
            for i, quotation in enumerate(user_quotations):
                if quotation['quotation_id'] == quotation_id:
                    del user_quotations[i]
                    
                    if save_quotations():
                        return jsonify({
                            'success': True, 
                            'message': _('quotation_deleted_success')
                        })
                    else:
                        return jsonify({'success': False, 'error': _('delete_failed')})
        
        return jsonify({'success': False, 'error': _('quotation_not_found')})
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
        
        return render_template('quotation_detail.html', quotation=None, error=_('quotation_not_found'))
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
        
        # 检查用户登录功能是否被禁用
        user_login_enabled = system_settings.get('user_login_enabled', True)
        
        # 如果用户登录功能被禁用，允许未登录用户导出报价单
        if not user_login_enabled:
            # 用户登录被禁用时，允许任何人导出报价单
            pass
        else:
            # 用户登录启用时，检查用户是否登录（管理员或普通用户）
            if not username and not is_admin_user:
                return redirect(url_for('user_login'))
        
        # 如果用户登录功能被禁用，允许导出所有报价单
        if not user_login_enabled:
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
            # 用户登录功能启用时的原有逻辑
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
        
        return jsonify({'success': False, 'error': _('quotation_not_found')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_default_sales_person():
    """获取默认销售人员（邮箱为info@oppeincabinet.ca的销售人员）"""
    sales_persons = system_settings.get('sales_persons', [])
    for person in sales_persons:
        if person.get('email') == 'info@oppeincabinet.ca':
            return person.get('name', '')
    return ''

def apply_amount_filter(df):
    """应用金额过滤，过滤掉低于阈值的订单"""
    try:
        # 获取系统设置中的过滤阈值（优先使用新的合并后设置）
        load_system_settings()  # 加载设置到全局变量
        threshold = system_settings.get('import_filter_min_amount', 
                                       system_settings.get('quotation_amount_filter_threshold', 1000))
        try:
            threshold = float(threshold) if threshold else 1000
        except (ValueError, TypeError):
            threshold = 1000
        

        
        # 确保总计列是数值类型
        df['总计'] = pd.to_numeric(df['总计'], errors='coerce')
        
        # 过滤掉总计金额低于阈值的行
        df_filtered = df[df['总计'] >= threshold].copy()
        
        filtered_count = len(df) - len(df_filtered)

        
        return df_filtered
        
    except Exception as e:

        # 如果过滤出错，返回原数据
        return df

def apply_amount_range_filter(df, amount_range):
    """根据金额区间过滤数据（按报价单金额）"""
    if not amount_range:
        return df
    
    try:
        df_copy = df.copy()
        
        # 检查是否有报价单金额字段，如果没有则使用总计字段
        amount_column = '报价单金额' if '报价单金额' in df_copy.columns else '总计'
        
        if amount_range == '0-1000':
            df_filtered = df_copy[df_copy[amount_column] <= 1000]
        elif amount_range == '1000-5000':
            df_filtered = df_copy[(df_copy[amount_column] > 1000) & (df_copy[amount_column] <= 5000)]
        elif amount_range == '5000-10000':
            df_filtered = df_copy[(df_copy[amount_column] > 5000) & (df_copy[amount_column] <= 10000)]
        elif amount_range == '10000+':
            df_filtered = df_copy[df_copy[amount_column] > 10000]
        else:
            df_filtered = df_copy
        

        return df_filtered
        
    except Exception as e:
        import traceback
        # 如果过滤出错，返回原数据
        return df

def apply_import_filters(df):
    """应用导入时的所有过滤条件"""
    try:
        # 加载系统设置
        load_system_settings()
        
        original_count = len(df)
        # 1. 应用金额阈值过滤（优先使用新的import_filter_min_amount设置）
        threshold = system_settings.get('import_filter_min_amount', 
                                       system_settings.get('quotation_amount_filter_threshold', 1000))
        try:
            threshold = float(threshold) if threshold is not None else 1000
        except (ValueError, TypeError):
            threshold = 1000
            
        if threshold is not None:
            df['总计'] = pd.to_numeric(df['总计'], errors='coerce')
            df = df[df['总计'] >= threshold].copy()
        
        # 2. 应用销售人员过滤
        sales_person_filter = system_settings.get('import_filter_sales_person', '') or ''
        if sales_person_filter.strip():
            sales_persons = [sp.strip() for sp in sales_person_filter.split(',') if sp.strip()]
            if sales_persons:
                df = df[df['销售人员'].isin(sales_persons)].copy()
        
        # 3. 应用客户过滤
        customer_filter = system_settings.get('import_filter_customer', '') or ''
        if customer_filter.strip():
            customers = [c.strip() for c in customer_filter.split(',') if c.strip()]
            if customers:
                df = df[df['客户'].isin(customers)].copy()
        
        # 4. 应用日期范围过滤
        start_date = (system_settings.get('import_filter_start_date', '') or '').strip()
        end_date = (system_settings.get('import_filter_end_date', '') or '').strip()
        
        if start_date or end_date:
            df['订单日期'] = pd.to_datetime(df['订单日期'], errors='coerce')
            
            if start_date:
                start_date_obj = pd.to_datetime(start_date)
                df = df[df['订单日期'] >= start_date_obj].copy()
            
            if end_date:
                end_date_obj = pd.to_datetime(end_date)
                df = df[df['订单日期'] <= end_date_obj].copy()
        
        # 5. 应用订单状态过滤（支持多选）
        order_status_filter = system_settings.get('import_filter_order_status', '') or ''
        if order_status_filter.strip():
            # 支持多个状态，用逗号分隔
            selected_statuses = [status.strip() for status in order_status_filter.split(',') if status.strip()]
            if selected_statuses:
                df = df[df['订单状态'].isin(selected_statuses)].copy()
        
        # 注意：金额过滤已在第1步完成，不需要重复过滤
        final_count = len(df)
        filtered_count = original_count - final_count
        
        return df
        
    except Exception as e:
        print(f"应用导入过滤时出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        # 如果过滤出错，返回原数据
        return df

def analyze_converted_time_trends(df, time_period='monthly'):
    """基于转换后数据分析时间趋势"""
    try:
        # 创建副本避免SettingWithCopyWarning
        df_copy = df.copy()
        
        if time_period == 'weekly':
            df_copy['time_period'] = df_copy['订单日期'].dt.to_period('W')
        else:  # monthly
            df_copy['time_period'] = df_copy['订单日期'].dt.to_period('M')
        
        # 按时间周期分组统计，直接使用转换后的字段
        monthly_stats = df_copy.groupby('time_period').agg({
            '总计': 'sum',
            '订单金额': 'sum',
            '报价单金额': 'sum'
        }).reset_index()
        
        labels = [str(period) for period in monthly_stats['time_period']]
        total_amounts = [float(x) for x in monthly_stats['总计'].tolist()]
        order_amounts = [float(x) for x in monthly_stats['订单金额'].tolist()]
        quotation_amounts = [float(x) for x in monthly_stats['报价单金额'].tolist()]
        
        # 🔧 计算金额转化率
        amount_conversion_rates = []
        for i in range(len(order_amounts)):
            if quotation_amounts[i] > 0:
                rate = float((order_amounts[i] / quotation_amounts[i]) * 100)
            else:
                rate = 0.0
            amount_conversion_rates.append(rate)
        


        
        return {
            'labels': labels,
            'total_amounts': total_amounts,
            'order_amounts': order_amounts,
            'quotation_amounts': quotation_amounts,
            'amount_conversion_rates': amount_conversion_rates  # 🆕 添加金额转化率
        }
    except Exception as e:
        print(f"转换后数据时间趋势分析错误: {e}")
        return {'labels': [], 'total_amounts': [], 'order_amounts': [], 'quotation_amounts': [], 'amount_conversion_rates': []}

def analyze_converted_conversion_rates(df, time_period='monthly'):
    """基于转换后数据分析转化率"""
    try:
        # 创建副本避免SettingWithCopyWarning
        df_copy = df.copy()
        
        if time_period == 'weekly':
            df_copy['time_period'] = df_copy['订单日期'].dt.to_period('W')
        else:  # monthly
            df_copy['time_period'] = df_copy['订单日期'].dt.to_period('M')
        
        # 按时间周期分组统计，直接使用转换后的字段
        monthly_stats = df_copy.groupby('time_period').agg({
            '订单数量': 'sum',
            '报价单数量': 'sum'
        }).reset_index()
        
        labels = [str(period) for period in monthly_stats['time_period']]
        order_counts = [int(x) for x in monthly_stats['订单数量'].tolist()]
        quotation_counts = [int(x) for x in monthly_stats['报价单数量'].tolist()]
        
        # 计算转化率
        rates = []
        for i in range(len(order_counts)):
            if quotation_counts[i] > 0:
                rate = float((order_counts[i] / quotation_counts[i]) * 100)
            else:
                rate = 0.0
            rates.append(rate)
        

        
        return {
            'labels': labels,
            'rates': rates,
            'order_counts': order_counts,
            'quotation_counts': quotation_counts
        }
    except Exception as e:
        print(f"转换后数据转化率分析错误: {e}")
        return {'labels': [], 'rates': [], 'order_counts': [], 'quotation_counts': []}

def analyze_converted_sales_person_performance(df):
    """基于转换后数据分析销售员业绩"""
    try:
        # 按销售员分组统计，直接使用转换后的字段
        sales_person_stats = df.groupby('销售人员').agg({
            '订单金额': 'sum',
            '报价单金额': 'sum', 
            '订单数量': 'sum',
            '报价单数量': 'sum',
            '毛利率（%）': 'mean'
        }).reset_index()
        
        result = []
        for _, row in sales_person_stats.iterrows():
            sales_person = row['销售人员']
            
            # 跳过NaN或无效的销售员姓名
            if pd.isna(sales_person) or str(sales_person).lower() == 'nan' or sales_person == '':
                continue
            
            # 转换为Python原生数据类型以避免JSON序列化问题
            order_amount = float(row['订单金额']) if pd.notna(row['订单金额']) else 0.0
            quotation_amount = float(row['报价单金额']) if pd.notna(row['报价单金额']) else 0.0
            order_count = int(row['订单数量']) if pd.notna(row['订单数量']) else 0
            quotation_count = int(row['报价单数量']) if pd.notna(row['报价单数量']) else 0
            
            # 计算转化率
            count_conversion_rate = float(order_count / quotation_count) if quotation_count > 0 else 0.0
            amount_conversion_rate = float(order_amount / quotation_amount) if quotation_amount > 0 else 0.0
            
            result.append({
                'sales_person': str(sales_person),
                'order_amount': order_amount,
                'quotation_amount': quotation_amount,
                'order_count': order_count,
                'quotation_count': quotation_count,
                'count_conversion_rate': count_conversion_rate,
                'amount_conversion_rate': amount_conversion_rate,
                'average_profit_margin': float(row['毛利率（%）']) if pd.notna(row['毛利率（%）']) else 0.0
            })
        
        return sorted(result, key=lambda x: x['order_amount'] + x['quotation_amount'], reverse=True)
    except Exception as e:
        print(f"转换后数据销售员业绩分析错误: {e}")
        return []

def analyze_converted_customer_orders(df):
    """基于转换后数据分析客户订单"""
    try:
        # 按客户分组统计，直接使用转换后的字段
        customer_stats = df.groupby('客户').agg({
            '订单金额': 'sum',
            '报价单金额': 'sum',
            '订单数量': 'sum', 
            '报价单数量': 'sum'
        }).reset_index()
        
        result = []
        for _, row in customer_stats.iterrows():
            customer = row['客户']
            
            # 跳过NaN或无效的客户名称
            if pd.isna(customer) or str(customer).lower() == 'nan' or customer == '':
                continue
            
            # 转换为Python原生数据类型以避免JSON序列化问题
            order_amount = float(row['订单金额']) if pd.notna(row['订单金额']) else 0.0
            quotation_amount = float(row['报价单金额']) if pd.notna(row['报价单金额']) else 0.0
            order_count = int(row['订单数量']) if pd.notna(row['订单数量']) else 0
            quotation_count = int(row['报价单数量']) if pd.notna(row['报价单数量']) else 0
            
            # 计算转化率
            count_conversion_rate = float(order_count / quotation_count) if quotation_count > 0 else 0.0
            amount_conversion_rate = float(order_amount / quotation_amount) if quotation_amount > 0 else 0.0
            
            result.append({
                'customer': str(customer),
                'order_amount': order_amount,
                'quotation_amount': quotation_amount,
                'order_count': order_count,
                'quotation_count': quotation_count,
                'count_conversion_rate': count_conversion_rate,
                'amount_conversion_rate': amount_conversion_rate
            })
        
        return sorted(result, key=lambda x: x['order_amount'] + x['quotation_amount'], reverse=True)
    except Exception as e:
        print(f"转换后数据客户订单分析错误: {e}")
        return []

def analyze_converted_sales_person_performance_by_month(df):
    """基于转换后数据按月分析销售员业绩"""
    try:
        # 创建年月列
        df_copy = df.copy()
        df_copy['year_month'] = df_copy['订单日期'].dt.to_period('M')
        
        # 按销售员和月份分组统计
        monthly_analysis = {}
        
        for sales_person in df_copy['销售人员'].unique():
            if pd.isna(sales_person) or str(sales_person).lower() == 'nan' or sales_person == '':
                continue
                
            person_data = df_copy[df_copy['销售人员'] == sales_person]
            monthly_analysis[sales_person] = {}
            
            for year_month in person_data['year_month'].unique():
                if pd.isna(year_month):
                    continue
                    
                month_data = person_data[person_data['year_month'] == year_month]
                
                monthly_analysis[sales_person][str(year_month)] = {
                    'order_amount': float(month_data['订单金额'].sum()),
                    'quotation_amount': float(month_data['报价单金额'].sum()),
                    'order_count': int(month_data['订单数量'].sum()),
                    'quotation_count': int(month_data['报价单数量'].sum())
                }
        
        return monthly_analysis
    except Exception as e:
        print(f"转换后数据按月销售员业绩分析错误: {e}")
        return {}

def generate_converted_data(df):
    """
    生成包含转换字段的数据
    
    ⭐ 核心业务逻辑 - 数据转换规则：
    1. 如果订单状态=报价单，则订单金额=0，订单数量=0，报价单金额=总计，报价单数量=1
    2. 如果订单状态=订单，则订单金额=总计，订单数量=1，报价单金额=总计，报价单数量=1
    3. 如果订单状态=已取消，过滤掉这一行（不包含在转换后数据中）
    4. 如果订单状态=已发送报价单，则订单金额=0，订单数量=0，报价单金额=总计，报价单数量=1
    
    ⚠️ 重要说明：
    - 规则2意味着每个"订单"状态的记录会同时贡献订单金额和报价单金额
    - 这样设计的目的是假设每个成功的订单都有对应的报价单过程
    - 转化率计算时，"订单"状态的记录会在分子和分母中都有贡献
    - 所有使用转换后数据的页面和分析函数都必须遵循此逻辑
    
    注意：此逻辑在整个系统中必须保持一致，所有使用转换后数据的页面都基于此逻辑
    """
    try:
        converted_data = []
        filtered_count = 0  # 记录被过滤掉的"已取消"订单数量
        
        for _, row in df.iterrows():
            order_status = str(row['订单状态']).strip() if pd.notna(row['订单状态']) else ''
            amount = float(row['总计']) if pd.notna(row['总计']) else 0.0
            
            # ⭐ 核心逻辑：根据订单状态过滤和转换数据
            if order_status == '已取消':
                # 规则3：已取消的订单直接过滤掉，不包含在转换后数据中
                filtered_count += 1
                continue
            
            # 基础记录信息
            record = {}
            for key, value in row.items():
                # 处理各种数据类型，确保JSON可序列化
                if pd.isna(value):
                    if key in ['销售人员', '客户', '编号', '订单状态']:
                        record[key] = ''
                    else:
                        record[key] = None
                elif isinstance(value, pd.Timestamp):
                    record[key] = value.strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(value) else None
                elif hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
                elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    record[key] = str(value)
                elif isinstance(value, (int, float, str, bool)) or value is None:
                    record[key] = value
                else:
                    record[key] = str(value)
            
            # ⭐ 核心逻辑：根据订单状态设置转换后的字段
            if order_status == '报价单':
                # 规则1：报价单状态
                record['订单金额'] = 0
                record['订单数量'] = 0
                record['报价单金额'] = amount
                record['报价单数量'] = 1
                
            elif order_status == '订单' or '销售订单' in order_status:
                # 规则2：订单状态（包括销售订单的各种变体）
                record['订单金额'] = amount
                record['订单数量'] = 1
                record['报价单金额'] = amount  # ⭐ 注意：订单状态下报价单金额也等于总计
                record['报价单数量'] = 1
                
            elif order_status == '已发送报价单':
                # 规则4：已发送报价单状态
                record['订单金额'] = 0
                record['订单数量'] = 0
                record['报价单金额'] = amount
                record['报价单数量'] = 1
                
            else:
                # 其他未明确定义的状态，按报价单处理（保守策略）
                print(f"警告：遇到未定义的订单状态 '{order_status}'，按报价单处理")
                record['订单金额'] = 0
                record['订单数量'] = 0
                record['报价单金额'] = amount
                record['报价单数量'] = 1
            
            # 单条记录级别不计算转化率，设置为0
            # 转化率应该在聚合层面计算（如按销售人员、客户等分组后计算）
            record['金额转化率'] = 0
            record['数量转化率'] = 0
            
            converted_data.append(record)
        

        return converted_data
        
    except Exception as e:
        print(f"生成转换数据时出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return []

def cleanup_old_imported_data_files():
    """清理超过1小时的临时导入数据文件"""
    try:
        temp_dir = tempfile.gettempdir()
        current_time = datetime.now()
        
        # 查找所有导入数据临时文件
        for filename in os.listdir(temp_dir):
            if filename.startswith('imported_data_') and filename.endswith('.json'):
                filepath = os.path.join(temp_dir, filename)
                try:
                    # 检查文件修改时间
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (current_time - file_time).total_seconds() > 3600:  # 1小时
                        os.remove(filepath)
                        print(f"清理过期临时文件: {filepath}")
                except Exception as e:
                    print(f"清理临时文件 {filepath} 失败: {e}")
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

def export_pdf_quotation(quotation_data):
    """导出PDF类型的报价单"""
    try:
        products = quotation_data.get('products', [])
        export_date = quotation_data.get('order_date', datetime.now().strftime('%Y-%m-%d'))
        
        # 检查用户登录功能是否被禁用
        user_login_enabled = system_settings.get('user_login_enabled', True)
        if not user_login_enabled:
            # 用户登录被禁用时，使用默认值
            export_username = 'Public User'
            export_sales_person = get_default_sales_person()
        else:
            # 用户登录启用时，使用原有逻辑
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
        
        # 检查用户登录功能是否被禁用
        user_login_enabled = system_settings.get('user_login_enabled', True)
        if not user_login_enabled:
            # 用户登录被禁用时，使用默认值
            export_username = 'Public User'
            export_sales_person = get_default_sales_person()
        else:
            # 用户登录启用时，使用原有逻辑
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

@app.route('/view_imported_data')
def view_imported_data():
    """查看导入的销售数据页面"""
    # 添加调试信息
    print(f"查看导入数据 - Session内容: {dict(session)}")
    print(f"Session中的键: {list(session.keys())}")
    
    # 检查session中是否有导入数据文件的信息
    if 'imported_data_file' not in session:
        print("错误：Session中没有找到 imported_data_file 键")
        return render_template('imported_data.html', error=_("没有找到导入的销售数据，请先导入数据。"), system_settings=system_settings)
    
    try:
        # 获取临时文件路径
        temp_filepath = session['imported_data_file']
        
        # 检查文件是否存在
        if not os.path.exists(temp_filepath):
            # 清除过期的session信息
            session.pop('imported_data_file', None)
            session.pop('imported_data_count', None)
            session.pop('imported_data_timestamp', None)
            return render_template('imported_data.html', error=_("导入的数据文件已过期，请重新导入数据。"), system_settings=system_settings)
        
        # 从临时文件读取数据
        with open(temp_filepath, 'r', encoding='utf-8') as f:
            imported_data = json.load(f)
        
        return render_template('imported_data.html', 
                             data=imported_data, 
                             total_records=len(imported_data),
                             system_settings=system_settings)
    except Exception as e:
        print(f"读取导入数据时出错: {str(e)}")
        return render_template('imported_data.html', error=f"{_(str(e))}", system_settings=system_settings)

@app.route('/view_converted_data')
def view_converted_data():
    """查看转换后的销售数据页面"""
    # 添加调试信息
    print(f"查看转换数据 - Session内容: {dict(session)}")
    print(f"Session中的键: {list(session.keys())}")
    
    # 检查session中是否有转换数据文件的信息
    if 'converted_data_file' not in session:
        print("错误：Session中没有找到 converted_data_file 键")
        return render_template('converted_data.html', error=_("没有找到转换后的销售数据，请先导入数据。"), system_settings=system_settings)
    
    try:
        # 获取临时文件路径
        temp_filepath = session['converted_data_file']
        
        # 检查文件是否存在
        if not os.path.exists(temp_filepath):
            # 清除过期的session信息
            session.pop('converted_data_file', None)
            session.pop('converted_data_count', None)
            return render_template('converted_data.html', error=_("转换后的数据文件已过期，请重新导入数据。"), system_settings=system_settings)
        
        # 从临时文件读取数据
        with open(temp_filepath, 'r', encoding='utf-8') as f:
            converted_data = json.load(f)
        
        return render_template('converted_data.html', 
                             data=converted_data, 
                             total_records=len(converted_data),
                             system_settings=system_settings)
    except Exception as e:
        print(f"读取转换数据时出错: {str(e)}")
        return render_template('converted_data.html', error=f"{_(str(e))}", system_settings=system_settings)

@app.route('/get_pdf_text')
def get_pdf_text():
    """获取PDF识别的原始文本"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': _('no_filename_specified')}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': _('file_not_exists')}), 404
    
    try:
        # 返回原始PDF文本（不添加页面分隔符）
        pdf_content = extract_pdf_content(filepath, add_page_markers=False)
        return jsonify({
            'success': True,
            'text': pdf_content
        })
    except Exception as e:
        return jsonify({'error': f'{_("read_pdf_failed")}: {str(e)}'}), 500

@app.route('/get_product_categories', methods=['GET'])
def get_product_categories():
    """获取产品类别列表"""
    try:
        categories = set()
        for sku, price_data in occw_prices.items():
            if isinstance(price_data, dict) and 'category' in price_data:
                category = price_data['category'].strip()
                if category:  # 确保类别不为空
                    categories.add(category)
        
        # 如果没有从数据中提取到类别，则返回默认类别作为后备
        if not categories:
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
            categories = set(default_categories)
        
        return jsonify({
            'success': True,
            'categories': sorted(list(categories))
        })
    except Exception as e:
        return jsonify({'error': f'{_("get_categories_failed")}: {str(e)}'}), 500

@app.route('/get_products_by_category', methods=['GET'])
def get_products_by_category():
    """根据类别获取产品列表 - 使用结构化数据"""
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': _('missing_category_param')}), 400
        
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
        return jsonify({'error': f'{_("get_products_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{_("search_sku_failed")}: {str(e)}'}), 500

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
                    'category': price_data.get('category', '').upper(),  # 保持与过滤逻辑一致
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
        return jsonify({'error': f'{_("get_price_table_failed")}: {str(e)}'}), 500

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
        return jsonify({'error': f'{_("get_filter_options_failed")}: {str(e)}'}), 500

# 销售分析相关路由
@app.route('/upload_sales_data', methods=['POST'])
def upload_sales_data():
    """上传销售数据Excel文件"""
    try:
        if 'file' not in request.files:
            response = jsonify({'success': False, 'error': _('file_required')})
            response.headers['Content-Type'] = 'application/json'
            return response
        
        file = request.files['file']
        if file.filename == '':
            response = jsonify({'success': False, 'error': _('file_required')})
            response.headers['Content-Type'] = 'application/json'
            return response
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            response = jsonify({'success': False, 'error': _('invalid_file_format')})
            response.headers['Content-Type'] = 'application/json'
            return response
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 读取Excel文件
        df = pd.read_excel(filepath)
        
        # 验证必要的列
        required_columns = ['编号', '订单日期', '销售人员', '客户', '总计', '毛利率（%）', '订单状态']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            response = jsonify({
                'success': False, 
                'error': f'缺少必要的列: {", ".join(missing_columns)}'
            })
            response.headers['Content-Type'] = 'application/json'
            return response
        
        # 预处理客户类型数据
        df = preprocess_customer_type_data(df)
        
        # 清理旧的临时文件
        cleanup_old_imported_data_files()
        
        # 注意：imported_data 将在过滤后生成，以确保保存的是过滤后的数据
        
        # 生成唯一的临时文件名
        import uuid
        temp_filename = f"imported_data_{uuid.uuid4().hex}.json"
        temp_filepath = os.path.join(tempfile.gettempdir(), temp_filename)
        
        # 先进行数据预处理，设置is_order和is_quotation字段
        df['订单日期'] = pd.to_datetime(df['订单日期']).dt.date  # 只保留日期部分，去掉时间
        df['总计'] = pd.to_numeric(df['总计'], errors='coerce').fillna(0)
        # 🔧 修复毛利率：Excel中的小数值需要乘以100转换为百分比
        df['毛利率（%）'] = pd.to_numeric(df['毛利率（%）'], errors='coerce').fillna(0) * 100
        
        # 过滤掉NaN销售员和客户的行，并创建副本
        df = df.dropna(subset=['销售人员', '客户']).copy()
        
        # 设置订单和报价单标识
        df.loc[:, 'is_order'] = df['订单状态'].str.contains('销售订单', na=False)
        df.loc[:, 'is_quotation'] = df['订单状态'].str.contains('报价单', na=False)
        
        # 处理同一编号的报价单和订单金额
        df = adjust_quotation_amounts(df)
        
        # 🔧 在保存数据之前应用所有过滤条件
        df_filtered = apply_import_filters(df)
        
        # 使用过滤后的数据生成导入数据列表
        imported_data = []
        for record in df_filtered.to_dict('records'):
            # 确保每个记录都是可序列化的
            clean_record = {}
            for key, value in record.items():
                # 处理各种数据类型，确保JSON可序列化
                if pd.isna(value):
                    # 对于重要的字符串字段，使用空字符串而不是None
                    if key in ['销售人员', '客户', '编号', '订单状态']:
                        clean_record[key] = ''
                    else:
                        clean_record[key] = None
                elif isinstance(value, pd.Timestamp):
                    # 处理pandas Timestamp对象
                    clean_record[key] = value.strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(value) else None
                elif hasattr(value, 'isoformat'):
                    # 处理其他日期时间对象
                    clean_record[key] = value.isoformat()
                elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    # 处理可能的生成器或其他可迭代对象
                    clean_record[key] = str(value)
                elif isinstance(value, (int, float, str, bool)) or value is None:
                    # 基本数据类型，直接使用
                    clean_record[key] = value
                else:
                    # 其他类型转换为字符串
                    clean_record[key] = str(value)
            imported_data.append(clean_record)
        
        # 保存过滤后的数据到临时文件
        try:
    
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(imported_data, f, ensure_ascii=False, indent=2)
            
            # 生成并保存转换后的数据（使用过滤后的df_filtered）
            converted_data = generate_converted_data(df_filtered)
            converted_temp_filename = f"converted_data_{uuid.uuid4().hex}.json"
            converted_temp_filepath = os.path.join(tempfile.gettempdir(), converted_temp_filename)
            
            with open(converted_temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
            # 在session中只保存文件路径和一些基本信息
            session['imported_data_file'] = temp_filepath
            session['converted_data_file'] = converted_temp_filepath
            session['imported_data_count'] = len(imported_data)
            session['converted_data_count'] = len(converted_data)
            session['imported_data_timestamp'] = datetime.now().isoformat()
            
            

        except Exception as e:
            import traceback
            # 如果保存失败，清除session标记
            session.pop('imported_data_file', None)
            session.pop('converted_data_file', None)
        
        # 使用转换后的数据进行分析
        if 'converted_data_file' in session and os.path.exists(session['converted_data_file']):
            analysis_data = analyze_converted_data(session['converted_data_file'])
        else:
            # 如果转换数据不存在，使用原始数据分析
            analysis_data = analyze_sales_data(df_filtered)
        
        response = jsonify({
            'success': True,
            'data': analysis_data
        })
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        import traceback
        print(f"销售数据上传错误: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        response = jsonify({'success': False, 'error': f'{_(str(e))}'})
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/update_sales_analysis', methods=['POST'])
def update_sales_analysis():
    """更新销售分析（根据时间周期和其他过滤条件）"""
    try:
        time_period = request.form.get('time_period', 'monthly')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        amount_range = request.form.get('amount_range')
        customer_company_type = request.form.get('customer_company_type')
        customer_types = request.form.get('customer_types')
        sales_person = request.form.get('sales_person')
        data = json.loads(request.form.get('data', '{}'))
        
        if not data:
            return jsonify({'success': False, 'error': _('no_data_found')})
        
        # 解析客户类型列表
        customer_types_list = []
        if customer_types:
            try:
                customer_types_list = json.loads(customer_types)
            except:
                customer_types_list = [customer_types] if customer_types else []
        
        # 重新分析数据（根据所有过滤条件）
        analysis_data = analyze_sales_data_by_period(
            data, 
            time_period, 
            start_date, 
            end_date, 
            amount_range,
            customer_company_type,
            customer_types_list,
            sales_person
        )
        
        return jsonify({
            'success': True,
            'data': analysis_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export_sales_analysis', methods=['POST'])
def export_sales_analysis():
    """导出销售分析报告"""
    try:
        time_period = request.form.get('time_period', 'monthly')
        data = json.loads(request.form.get('data', '{}'))
        
        if not data:
            return jsonify({'success': False, 'error': _('no_data_found')})
        
        # 生成Excel报告
        filename = f'sales_analysis_{time_period}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        export_sales_analysis_to_excel(data, filepath, time_period)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/get_sales_raw_data')
def get_sales_raw_data():
    """获取销售原始数据"""
    try:
        # 读取Excel文件
        file_path = os.path.join('upload', '销售订单.xlsx')
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': _('数据文件不存在')})
        
        df = pd.read_excel(file_path)
        
        # 转换为字典列表
        data = list(df.to_dict('records'))
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_sample_file')
def download_sample_file():
    """下载样本文件"""
    try:
        # 使用现有的销售订单文件作为样本
        sample_file_path = os.path.join('upload', '销售订单.xlsx')
        if os.path.exists(sample_file_path):
            return send_file(
                sample_file_path,
                as_attachment=True,
                download_name=_('销售数据样本.xlsx')
            )
        else:
            return jsonify({'error': _('样本文件不存在')}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

def analyze_converted_data(converted_data_file, amount_range=None):
    """使用转换后的数据进行分析"""
    try:

        
        # 读取转换后的数据
        with open(converted_data_file, 'r', encoding='utf-8') as f:
            converted_records = json.load(f)
        
        # 转换为DataFrame
        df = pd.DataFrame(converted_records)
        
        # 🆕 应用金额区间过滤
        if amount_range:
            df = apply_amount_range_filter(df, amount_range)
    
        
        # 确保日期列的格式正确
        df['订单日期'] = pd.to_datetime(df['订单日期'], errors='coerce')
        
        # 确保数值列的格式正确
        for col in ['总计', '订单金额', '报价单金额', '订单数量', '报价单数量']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        

        
        # 使用转换后数据的专门分析函数
        sales_person_analysis = analyze_converted_sales_person_performance(df)
        customer_analysis = analyze_converted_customer_orders(df)
        trend_data = analyze_converted_time_trends(df, 'monthly')
        conversion_data = analyze_converted_conversion_rates(df, 'monthly')
        sales_person_monthly_analysis = analyze_converted_sales_person_performance_by_month(df)
        
        # 🔧 添加客户类型相关分析
        customer_type_analysis = analyze_customer_type_performance(df)
        customer_type_trends = analyze_customer_type_trends(df, 'monthly')
        customer_type_distribution = analyze_customer_type_distribution(df)
        company_type_comparison = analyze_company_type_comparison(df, 'monthly')
        
        return {
            'sales_person_analysis': sales_person_analysis,
            'customer_analysis': customer_analysis,
            'trend_data': trend_data,
            'conversion_data': conversion_data,
            'sales_person_monthly_analysis': sales_person_monthly_analysis,
            'customer_type_analysis': customer_type_analysis,
            'customer_type_trends': customer_type_trends,
            'customer_type_distribution': customer_type_distribution,
            'company_type_comparison': company_type_comparison,
            'converted_data': converted_records  # 添加转换后的数据供前端使用
        }
        
    except Exception as e:
        print(f"分析转换后数据时出错: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        raise Exception(f'{_(str(e))}')

def analyze_sales_data(df):
    """分析销售数据（数据预处理已在调用前完成）"""
    try:
        
        # 销售员业绩分析
        sales_person_analysis = analyze_sales_person_performance(df)
        
        # 客户订单分析
        customer_analysis = analyze_customer_orders(df)
        
        # 时间趋势分析（默认按月）
        trend_data = analyze_time_trends(df, 'monthly')
        
        # 转化率分析（默认按月）
        conversion_data = analyze_conversion_rates(df, 'monthly')
        
        # 按月的销售员业绩分析
        sales_person_monthly_analysis = analyze_sales_person_performance_by_month(df)
        
        # 客户类型相关分析
        customer_type_analysis = analyze_customer_type_performance(df)
        customer_type_trends = analyze_customer_type_trends(df, 'monthly')
        customer_type_distribution = analyze_customer_type_distribution(df)
        company_type_comparison = analyze_company_type_comparison(df, 'monthly')
        
        return {
            'sales_person_analysis': sales_person_analysis,
            'customer_analysis': customer_analysis,
            'trend_data': trend_data,
            'conversion_data': conversion_data,
            'sales_person_monthly_analysis': sales_person_monthly_analysis,
            'customer_type_analysis': customer_type_analysis,
            'customer_type_trends': customer_type_trends,
            'customer_type_distribution': customer_type_distribution,
            'company_type_comparison': company_type_comparison
        }
        
    except Exception as e:
        raise Exception(f'{_(str(e))}')

def analyze_customer_type_performance(df):
    """分析客户类型业绩"""
    try:
        # 检查客户/类型列是否存在，如果不存在则添加默认列
        if '客户/类型' not in df.columns:
            df['客户/类型'] = '未设置'
        
        customer_type_stats = {}
        
        # 按客户类型分组处理数据
        for customer_type, group in df.groupby('客户/类型'):
            if pd.isna(customer_type) or customer_type == '' or str(customer_type).lower() == 'nan':
                customer_type = '未设置'
            
            if customer_type not in customer_type_stats:
                customer_type_stats[customer_type] = {
                    'order_amount': 0,
                    'quotation_amount': 0,
                    'order_count': 0,
                    'quotation_count': 0
                }
            
            # 处理每个客户类型下的所有记录
            for _, row in group.iterrows():
                # 检查是否存在转换后的字段，如果不存在则使用原始字段
                if '订单金额' in row and '报价单金额' in row and '订单数量' in row and '报价单数量' in row:
                    # 使用转换后数据的字段名
                    order_amount = row.get('订单金额', 0)
                    quotation_amount = row.get('报价单金额', 0)
                    order_count = row.get('订单数量', 0)
                    quotation_count = row.get('报价单数量', 0)
                else:
                    # 使用原始字段进行计算
                    order_status = str(row.get('订单状态', '')).strip()
                    amount = float(row.get('总计', 0)) if pd.notna(row.get('总计', 0)) else 0.0
                    
                    # 根据订单状态计算转换后的字段
                    if order_status == '报价单' or order_status == '已发送报价单':
                        order_amount = 0
                        quotation_amount = amount
                        order_count = 0
                        quotation_count = 1
                    elif order_status == '订单' or '销售订单' in order_status:
                        order_amount = amount
                        quotation_amount = amount
                        order_count = 1
                        quotation_count = 1
                    else:
                        # 其他状态按报价单处理
                        order_amount = 0
                        quotation_amount = amount
                        order_count = 0
                        quotation_count = 1
                
                if pd.isna(order_amount):
                    order_amount = 0
                if pd.isna(quotation_amount):
                    quotation_amount = 0
                if pd.isna(order_count):
                    order_count = 0
                if pd.isna(quotation_count):
                    quotation_count = 0
                
                customer_type_stats[customer_type]['order_amount'] += float(order_amount)
                customer_type_stats[customer_type]['quotation_amount'] += float(quotation_amount)
                customer_type_stats[customer_type]['order_count'] += int(order_count)
                customer_type_stats[customer_type]['quotation_count'] += int(quotation_count)
        
        # 转换为列表格式
        result = []
        for customer_type, stats in customer_type_stats.items():
            count_conversion_rate = (stats['order_count'] / stats['quotation_count'] * 100) if stats['quotation_count'] > 0 else 0
            amount_conversion_rate = (stats['order_amount'] / stats['quotation_amount'] * 100) if stats['quotation_amount'] > 0 else 0
            
            result.append({
                'customer_type': customer_type,
                'order_count': stats['order_count'],
                'quotation_count': stats['quotation_count'],
                'order_amount': round(stats['order_amount'], 2),
                'quotation_amount': round(stats['quotation_amount'], 2),
                'count_conversion_rate': round(count_conversion_rate, 1),
                'amount_conversion_rate': round(amount_conversion_rate, 1)
            })
            
        # 按订单金额排序
        result.sort(key=lambda x: x['order_amount'], reverse=True)
        return result
        
    except Exception as e:
        import traceback
        return []

def analyze_customer_type_trends(df, time_period='monthly'):
    """分析客户类型时间趋势"""
    try:
        # 检查必要的列是否存在，如果不存在则添加默认列
        if '客户/类型' not in df.columns:
            df['客户/类型'] = '未设置'
        
        if '订单日期' not in df.columns:
            return {'labels': [], 'datasets': []}
        
        # 确保订单日期是datetime类型
        df['订单日期'] = pd.to_datetime(df['订单日期'], errors='coerce')
        df = df.dropna(subset=['订单日期'])
        
        # 按时间周期分组
        if time_period == 'monthly':
            df['time_group'] = df['订单日期'].dt.to_period('M')
        elif time_period == 'weekly':
            df['time_group'] = df['订单日期'].dt.to_period('W')
        else:
            df['time_group'] = df['订单日期'].dt.to_period('M')
        
        # 获取所有客户类型
        customer_types = df['客户/类型'].unique()
        customer_types = [ct for ct in customer_types if not pd.isna(ct) and ct != '' and str(ct).lower() != 'nan']
        
        # 如果没有客户类型数据，使用默认值
        if not customer_types:
            customer_types = ['未设置']
        
        # 获取所有时间组
        time_groups = sorted(df['time_group'].unique())
        time_labels = [str(tg) for tg in time_groups]
        
        # 为每个客户类型创建数据集
        datasets = []
        colors = ['rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)', 
                 'rgb(75, 192, 192)', 'rgb(153, 102, 255)', 'rgb(255, 159, 64)']
        
        for i, customer_type in enumerate(customer_types):
            order_amounts = []
            quotation_amounts = []
            order_counts = []
            quotation_counts = []
            
            for time_group in time_groups:
                group_data = df[(df['客户/类型'] == customer_type) & (df['time_group'] == time_group)]
                
                # 计算该时间组的订单和报价单数据
                order_amount = 0
                quotation_amount = 0
                order_count = 0
                quotation_count = 0
                
                for _, row in group_data.iterrows():
                    # 检查是否存在转换后的字段，如果不存在则使用原始字段
                    if '订单金额' in row and '报价单金额' in row and '订单数量' in row and '报价单数量' in row:
                        # 使用转换后数据的字段名
                        order_amount += float(row.get('订单金额', 0) or 0)
                        quotation_amount += float(row.get('报价单金额', 0) or 0)
                        order_count += int(row.get('订单数量', 0) or 0)
                        quotation_count += int(row.get('报价单数量', 0) or 0)
                    else:
                        # 使用原始字段进行计算
                        order_status = str(row.get('订单状态', '')).strip()
                        amount = float(row.get('总计', 0)) if pd.notna(row.get('总计', 0)) else 0.0
                        
                        # 根据订单状态计算转换后的字段
                        if order_status == '报价单' or order_status == '已发送报价单':
                            quotation_amount += amount
                            quotation_count += 1
                        elif order_status == '订单' or '销售订单' in order_status:
                            order_amount += amount
                            quotation_amount += amount
                            order_count += 1
                            quotation_count += 1
                        else:
                            # 其他状态按报价单处理
                            quotation_amount += amount
                            quotation_count += 1
                
                order_amounts.append(round(float(order_amount), 2))
                quotation_amounts.append(round(float(quotation_amount), 2))
                order_counts.append(int(order_count))
                quotation_counts.append(int(quotation_count))
                
            # 添加订单金额数据集
            datasets.append({
                'label': f'{customer_type}-订单金额',
                'data': order_amounts,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                'tension': 0.1
            })
            
            # 添加报价单金额数据集
            datasets.append({
                'label': f'{customer_type}-报价单金额',
                'data': quotation_amounts,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                'borderDash': [5, 5],
                'tension': 0.1
            })
            
        result = {
            'labels': time_labels,
            'datasets': datasets
        }
        
        return result
        
    except Exception as e:
        import traceback
        return {'labels': [], 'datasets': []}

def analyze_customer_type_distribution(df):
    """分析客户类型分布（饼图数据）"""
    try:
        # 检查客户/类型列是否存在，如果不存在则添加默认列
        if '客户/类型' not in df.columns:
            df['客户/类型'] = '未设置'
        
        # 按客户类型统计订单金额和数量
        customer_type_stats = {}
        
        for _, row in df.iterrows():
            customer_type = row.get('客户/类型', '未设置')
            if pd.isna(customer_type) or customer_type == '' or str(customer_type).lower() == 'nan':
                customer_type = '未设置'
            
            # 检查是否存在转换后的字段，如果不存在则使用原始字段
            if '订单金额' in row and '订单数量' in row:
                # 使用转换后数据的字段名
                order_amount = row.get('订单金额', 0)
                order_count = row.get('订单数量', 0)
            else:
                # 使用原始字段进行计算
                order_status = str(row.get('订单状态', '')).strip()
                amount = float(row.get('总计', 0)) if pd.notna(row.get('总计', 0)) else 0.0
                
                # 根据订单状态计算转换后的字段
                if order_status == '订单' or '销售订单' in order_status:
                    order_amount = amount
                    order_count = 1
                else:
                    # 其他状态按0处理（只统计订单，不统计报价单）
                    order_amount = 0
                    order_count = 0
            
            if pd.isna(order_amount):
                order_amount = 0
            if pd.isna(order_count):
                order_count = 0
            
            if customer_type not in customer_type_stats:
                customer_type_stats[customer_type] = {
                    'order_amount': 0,
                    'order_count': 0
                }
            
            customer_type_stats[customer_type]['order_amount'] += float(order_amount)
            customer_type_stats[customer_type]['order_count'] += int(order_count)
        
        # 转换为饼图数据格式
        labels = list(customer_type_stats.keys())
        amount_values = [round(stats['order_amount'], 2) for stats in customer_type_stats.values()]
        count_values = [stats['order_count'] for stats in customer_type_stats.values()]
        
        result = {
            'amount_distribution': {
                'labels': labels,
                'values': amount_values
            },
            'count_distribution': {
                'labels': labels,
                'values': count_values
            }
        }
        
        return result
        
    except Exception as e:
        import traceback
        return {'amount_distribution': {'labels': [], 'values': []}, 'count_distribution': {'labels': [], 'values': []}}

def analyze_company_type_comparison(df, time_period='monthly'):
    """分析公司类型对比（零售vs批发）"""
    try:
        
        # 检查必要的列是否存在，如果不存在则添加默认列
        if '客户/公司类型' not in df.columns:
            print("⚠️ 客户/公司类型列不存在，添加默认列")
            df['客户/公司类型'] = '未设置'
        
        if '订单日期' not in df.columns:
            print("❌ 公司类型对比分析：缺少订单日期列")
            return {'labels': [], 'datasets': []}
        
        # 确保订单日期是datetime类型
        df['订单日期'] = pd.to_datetime(df['订单日期'], errors='coerce')
        df = df.dropna(subset=['订单日期'])
        
        # 按时间周期分组
        if time_period == 'monthly':
            df['time_group'] = df['订单日期'].dt.to_period('M')
        elif time_period == 'weekly':
            df['time_group'] = df['订单日期'].dt.to_period('W')
        else:
            df['time_group'] = df['订单日期'].dt.to_period('M')
        
        # 获取所有公司类型
        company_types = df['客户/公司类型'].unique()
        company_types = [ct for ct in company_types if not pd.isna(ct) and ct != '' and str(ct).lower() != 'nan']
        
        # 如果没有公司类型数据，使用默认值
        if not company_types:
            company_types = ['未设置']
        
        # 获取所有时间组
        time_groups = sorted(df['time_group'].unique())
        time_labels = [str(tg) for tg in time_groups]
        
        # 为每个公司类型创建数据集
        datasets = []
        colors = ['rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)', 
                 'rgb(75, 192, 192)', 'rgb(153, 102, 255)', 'rgb(255, 159, 64)']
        
        for i, company_type in enumerate(company_types):
            order_amounts = []
            quotation_amounts = []
            order_counts = []
            quotation_counts = []
            
            for time_group in time_groups:
                group_data = df[(df['客户/公司类型'] == company_type) & (df['time_group'] == time_group)]
                
                # 计算该时间组的订单和报价单数据
                order_amount = 0
                quotation_amount = 0
                order_count = 0
                quotation_count = 0
                
                for _, row in group_data.iterrows():
                    # 检查是否存在转换后的字段，如果不存在则使用原始字段
                    if '订单金额' in row and '报价单金额' in row and '订单数量' in row and '报价单数量' in row:
                        # 使用转换后数据的字段名
                        order_amount += float(row.get('订单金额', 0) or 0)
                        quotation_amount += float(row.get('报价单金额', 0) or 0)
                        order_count += int(row.get('订单数量', 0) or 0)
                        quotation_count += int(row.get('报价单数量', 0) or 0)
                    else:
                        # 使用原始字段进行计算
                        order_status = str(row.get('订单状态', '')).strip()
                        amount = float(row.get('总计', 0)) if pd.notna(row.get('总计', 0)) else 0.0
                        
                        # 根据订单状态计算转换后的字段
                        if order_status == '报价单' or order_status == '已发送报价单':
                            quotation_amount += amount
                            quotation_count += 1
                        elif order_status == '订单' or '销售订单' in order_status:
                            order_amount += amount
                            quotation_amount += amount
                            order_count += 1
                            quotation_count += 1
                        else:
                            # 其他状态按报价单处理
                            quotation_amount += amount
                            quotation_count += 1
                
                order_amounts.append(round(float(order_amount), 2))
                quotation_amounts.append(round(float(quotation_amount), 2))
                order_counts.append(int(order_count))
                quotation_counts.append(int(quotation_count))
                
            # 添加订单金额数据集
            datasets.append({
                'label': f'{company_type}-订单金额',
                'data': order_amounts,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                'tension': 0.1
            })
            
            # 添加报价单金额数据集
            datasets.append({
                'label': f'{company_type}-报价单金额',
                'data': quotation_amounts,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)'),
                'borderDash': [5, 5],
                'tension': 0.1
            })
        
        result = {
            'labels': time_labels,
            'datasets': datasets
        }
        
        return result
        
    except Exception as e:
        import traceback
        return {'labels': [], 'datasets': []}

def adjust_quotation_amounts(df):
    """调整报价单金额：如果同一编号的报价单金额小于订单金额，则将报价单金额调整为订单金额"""
    try:
        # 按编号分组处理
        for number, group in df.groupby('编号'):
            if len(group) > 1:  # 只有同一编号有多条记录时才需要处理
                # 找出该编号下的订单和报价单（使用已设置的标识）
                orders = group[group['is_order'] == True]
                quotations = group[group['is_quotation'] == True]
                
                if len(orders) > 0 and len(quotations) > 0:
                    # 获取订单金额（取最大值，以防有多个订单）
                    order_amount = orders['总计'].max()
                    
                    # 检查报价单金额是否小于订单金额
                    for idx in quotations.index:
                        quotation_amount = df.loc[idx, '总计']
                        if quotation_amount < order_amount:
                            print(f"调整报价单金额: 编号 {number}, 原金额 {quotation_amount}, 调整为 {order_amount}")
                            df.loc[idx, '总计'] = order_amount
        
        return df
        
    except Exception as e:
        print(f"调整报价单金额时出错: {str(e)}")
        return df

def analyze_sales_person_performance(df):
    """
    ⚠️ 废弃函数：分析销售员业绩 - 基于原始数据
    
    TODO: 此函数已被废弃，应在下一个版本中移除
    注意：此函数基于原始数据和旧的转换逻辑，已被废弃。
    请使用 analyze_converted_sales_person_performance() 函数，该函数基于最新的转换后数据。
    
    新的业务逻辑已在 generate_converted_data() 函数中实现。
    """
    sales_person_stats = {}

    # 按编号分组处理数据
    for number, group in df.groupby('编号'):
        # 获取销售员信息（取第一条记录）
        sales_person = group.iloc[0]['销售人员']

        # 跳过NaN销售员
        if pd.isna(sales_person) or sales_person == '' or str(sales_person).lower() == 'nan':
            continue

        if sales_person not in sales_person_stats:
            sales_person_stats[sales_person] = {
                'order_amount': 0,
                'quotation_amount': 0,
                'order_count': 0,
                'quotation_count': 0,
                'profit_margins': []
            }

        # 处理每个编号下的所有记录
        for _, row in group.iterrows():
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            amount = row['总计']
            profit_margin = row['毛利率（%）']

            if is_order:
                # 销售订单：订单金额=总计金额，报价单金额=总计金额，订单数量=1，报价单数量=1
                sales_person_stats[sales_person]['order_amount'] += amount
                sales_person_stats[sales_person]['quotation_amount'] += amount
                sales_person_stats[sales_person]['order_count'] += 1
                sales_person_stats[sales_person]['quotation_count'] += 1
            elif is_quotation:
                # 报价单：订单金额=0，报价单金额=总计金额，订单数量=0，报价单数量=1
                sales_person_stats[sales_person]['quotation_amount'] += amount
                sales_person_stats[sales_person]['quotation_count'] += 1

            # 收集毛利率数据
            if profit_margin > 0:
                sales_person_stats[sales_person]['profit_margins'].append(profit_margin)

    # 计算转化率和平均毛利率
    result = []
    for sales_person, stats in sales_person_stats.items():
        # 确保销售员姓名不是NaN
        if pd.isna(sales_person) or str(sales_person).lower() == 'nan':
            continue

        order_amount = stats['order_amount']
        quotation_amount = stats['quotation_amount']
        order_count = stats['order_count']
        quotation_count = stats['quotation_count']

        # 数量转化率 = 订单数量 / 报价单数量
        count_conversion_rate = order_count / quotation_count if quotation_count > 0 else 0
        # 金额转化率 = 订单金额 / 报价单金额
        amount_conversion_rate = order_amount / quotation_amount if quotation_amount > 0 else 0
        avg_profit_margin = sum(stats['profit_margins']) / len(stats['profit_margins']) if stats['profit_margins'] else 0

        result.append({
            'sales_person': sales_person,
            'order_amount': order_amount,
            'quotation_amount': quotation_amount,
            'order_count': order_count,
            'quotation_count': quotation_count,
            'count_conversion_rate': count_conversion_rate,
            'amount_conversion_rate': amount_conversion_rate,
            'average_profit_margin': avg_profit_margin
        })

    return sorted(result, key=lambda x: x['order_amount'] + x['quotation_amount'], reverse=True)

def analyze_sales_person_performance_by_month(df):
    """按月分析销售员业绩"""
    # 设置月份为索引
    df['month'] = df['订单日期'].dt.to_period('M')
    
    # 按销售员和月份分组
    monthly_analysis = {}
    
    for (sales_person, month), group in df.groupby(['销售人员', 'month']):
        if sales_person not in monthly_analysis:
            monthly_analysis[sales_person] = {}
        
        # 初始化统计数据
        stats = {
            'order_amount': 0,
            'quotation_amount': 0,
            'order_count': 0,
            'quotation_count': 0
        }
        
        # 统计每个月的数据
        for _, row in group.iterrows():
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            amount = row['总计']
            
            if is_order:
                # 销售订单：订单金额=总计金额，报价单金额=总计金额，订单数量=1，报价单数量=1
                stats['order_amount'] += amount
                stats['quotation_amount'] += amount
                stats['order_count'] += 1
                stats['quotation_count'] += 1
            elif is_quotation:
                # 报价单：订单金额=0，报价单金额=总计金额，订单数量=0，报价单数量=1
                stats['quotation_amount'] += amount
                stats['quotation_count'] += 1
                
        monthly_analysis[sales_person][str(month)] = stats
        
    return monthly_analysis

def analyze_customer_orders(df):
    """分析客户订单 - 重新设计逻辑确保每个编号都有完整的报价单和订单数据"""
    customer_stats = {}
    
    # 按编号分组处理数据
    for number, group in df.groupby('编号'):
        # 获取客户信息（取第一条记录）
        customer = group.iloc[0]['客户']
        
        # 跳过NaN客户
        if pd.isna(customer) or customer == '' or str(customer).lower() == 'nan':
            continue
        
        if customer not in customer_stats:
            customer_stats[customer] = {
                'order_count': 0,
                'quotation_count': 0,
                'order_amount': 0,
                'quotation_amount': 0
            }
        
        # 处理每个编号下的所有记录
        for _, row in group.iterrows():
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            amount = row['总计']
            
            if is_order:
                # 销售订单：订单金额=总计金额，报价单金额=总计金额，订单数量=1，报价单数量=1
                customer_stats[customer]['order_count'] += 1
                customer_stats[customer]['order_amount'] += amount
                customer_stats[customer]['quotation_count'] += 1
                customer_stats[customer]['quotation_amount'] += amount
            elif is_quotation:
                # 报价单：订单金额=0，报价单金额=总计金额，订单数量=0，报价单数量=1
                customer_stats[customer]['quotation_count'] += 1
                customer_stats[customer]['quotation_amount'] += amount
    
    result = []
    for customer, stats in customer_stats.items():
        # 确保客户姓名不是NaN
        if pd.isna(customer) or str(customer).lower() == 'nan':
            continue
            
        result.append({
            'customer_name': customer,
            'order_count': stats['order_count'],
            'quotation_count': stats['quotation_count'],
            'order_amount': stats['order_amount'],
            'quotation_amount': stats['quotation_amount']
        })
    
    return sorted(result, key=lambda x: x['order_amount'] + x['quotation_amount'], reverse=True)

def analyze_time_trends(df, time_period='monthly'):
    """分析时间趋势"""
    # 创建副本避免SettingWithCopyWarning
    df_copy = df.copy()
    
    if time_period == 'weekly':
        df_copy['time_period'] = df_copy['订单日期'].dt.to_period('W')
    else:  # monthly
        df_copy['time_period'] = df_copy['订单日期'].dt.to_period('M')
    
    # 按时间周期分组统计
    monthly_stats = df_copy.groupby('time_period').agg({
        '总计': 'sum',
        'is_order': 'sum',
        'is_quotation': 'sum'
    }).reset_index()
    
    labels = [str(period) for period in monthly_stats['time_period']]
    total_amounts = monthly_stats['总计'].tolist()
    
    # 按照正确的业务逻辑计算订单金额和报价单金额
    order_amounts = []
    quotation_amounts = []
    
    for time_period in monthly_stats['time_period']:
        # 获取这个时间段的所有数据
        period_data = df_copy[df_copy['time_period'] == time_period]
        
        order_amount = 0
        quotation_amount = 0
        
        for _, row in period_data.iterrows():
            amount = row['总计']
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            
            if is_order:
                # 销售订单：订单金额+=总计，报价单金额+=总计
                order_amount += amount
                quotation_amount += amount
            elif is_quotation:
                # 报价单：订单金额+=0，报价单金额+=总计
                quotation_amount += amount
        
        order_amounts.append(order_amount)
        quotation_amounts.append(quotation_amount)
    
    return {
        'labels': labels,
        'total_amounts': total_amounts,
        'order_amounts': order_amounts,
        'quotation_amounts': quotation_amounts
    }

def analyze_conversion_rates(df, time_period='monthly'):
    """分析转化率"""
    # 创建副本避免SettingWithCopyWarning
    df_copy = df.copy()
    
    if time_period == 'weekly':
        df_copy['time_period'] = df_copy['订单日期'].dt.to_period('W')
    else:  # monthly
        df_copy['time_period'] = df_copy['订单日期'].dt.to_period('M')
    
    monthly_stats = df_copy.groupby('time_period').agg({
        '总计': 'sum',
        'is_order': 'sum',
        'is_quotation': 'sum'
    }).reset_index()
    
    labels = [str(period) for period in monthly_stats['time_period']]
    rates = []
    order_counts = []
    quotation_counts = []
    
    for _, row in monthly_stats.iterrows():
        total_amount = row['总计']
        order_count = row['is_order']  # 订单数量
        quotation_only_count = row['is_quotation']  # 纯报价单数量
        total_quotation_count = order_count + quotation_only_count  # 总报价数量
        
        order_counts.append(order_count)
        quotation_counts.append(total_quotation_count)
        
        # 数量转化率 = 订单数量 / 总报价数量
        if total_quotation_count > 0:
            rate = (order_count / total_quotation_count) * 100
        else:
            rate = 0
        
        rates.append(rate)
    
    return {
        'labels': labels,
        'rates': rates,
        'order_counts': order_counts,
        'quotation_counts': quotation_counts
    }

def analyze_sales_data_by_period(data, time_period, start_date=None, end_date=None, amount_range=None, customer_company_type=None, customer_types=None, sales_person=None):
    """根据时间周期和其他过滤条件重新分析数据（从转换后数据集读取）"""
    try:
        # 🎯 遵循规则3：从转换后数据集读取数据
        from flask import session
        
        # 检查是否有转换后数据文件
        if 'converted_data_file' not in session or not os.path.exists(session['converted_data_file']):
            print("❌ 没有找到转换后数据文件，返回原数据")
            return data
        
        # 从转换后数据文件读取数据
        with open(session['converted_data_file'], 'r', encoding='utf-8') as f:
            converted_records = json.load(f)
        
        df = pd.DataFrame(converted_records)
        
        # 检查关键列是否存在
        required_columns = ['客户/类型', '订单日期', '总计', '订单状态']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠️ 缺少关键列: {missing_columns}")
        else:
            print(f"✅ 所有关键列都存在")
        
        # 数据预处理
        df['订单日期'] = pd.to_datetime(df['订单日期'], errors='coerce')
        for col in ['总计', '订单金额', '报价单金额', '订单数量', '报价单数量']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 根据日期范围过滤数据
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            df = df[(df['订单日期'] >= start_date) & (df['订单日期'] <= end_date)]
        
        # 根据金额区间过滤数据
        if amount_range:
            df = apply_amount_range_filter(df, amount_range)
        
        # 根据客户公司类型过滤数据
        if customer_company_type:
            df = df[df['客户/公司类型'] == customer_company_type]
        
        # 根据客户类型过滤数据
        if customer_types and isinstance(customer_types, list) and len(customer_types) > 0:
            df = df[df['客户/类型'].isin(customer_types)]
        
        # 根据销售人员过滤数据
        if sales_person:
            df = df[df['销售人员'] == sales_person]
        
        # 使用转换后数据的专门分析函数
        sales_person_analysis = analyze_converted_sales_person_performance(df)
        
        customer_analysis = analyze_converted_customer_orders(df)
        
        # 根据时间周期分析图表数据
        if time_period in ['monthly', 'weekly']:
            trend_data = analyze_converted_time_trends(df, time_period)
            conversion_data = analyze_converted_conversion_rates(df, time_period)
        else:
            # 默认按月分析
            trend_data = analyze_converted_time_trends(df, 'monthly')
            conversion_data = analyze_converted_conversion_rates(df, 'monthly')
        
        # 客户类型相关分析
        customer_type_analysis = analyze_customer_type_performance(df)
        
        customer_type_trends = analyze_customer_type_trends(df, time_period)
        
        customer_type_distribution = analyze_customer_type_distribution(df)
        
        company_type_comparison = analyze_company_type_comparison(df, time_period)
        
        # 返回完整的分析结果
        return {
            'sales_person_analysis': sales_person_analysis,
            'customer_analysis': customer_analysis,
            'trend_data': trend_data,
            'conversion_data': conversion_data,
            'customer_type_analysis': customer_type_analysis,
            'customer_type_trends': customer_type_trends,
            'customer_type_distribution': customer_type_distribution,
            'company_type_comparison': company_type_comparison,
            'converted_data': converted_records  # 添加转换后的数据供前端使用
        }
        
    except Exception as e:
        print(f"❌ 分析数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return data

def export_sales_analysis_to_excel(data, filepath, time_period):
    """导出销售分析报告到Excel"""
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        # 销售员业绩表
        sales_person_df = pd.DataFrame(data['sales_person_analysis'])
        sales_person_df.to_excel(writer, sheet_name='销售员业绩', index=False)
        
        # 客户订单表
        customer_df = pd.DataFrame(data['customer_analysis'])
        customer_df.to_excel(writer, sheet_name='客户订单', index=False)
        
        # 时间趋势表
        trend_df = pd.DataFrame({
            '时间': data['trend_data']['labels'],
            '总金额': data['trend_data']['total_amounts']
        })
        trend_df.to_excel(writer, sheet_name='时间趋势', index=False)
        
        # 转化率表
        conversion_df = pd.DataFrame({
            '时间': data['conversion_data']['labels'],
            '转化率(%)': data['conversion_data']['rates']
        })
        conversion_df.to_excel(writer, sheet_name='转化率', index=False)

# 确保目录存在
for directory in ['uploads', 'data']:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"创建目录: {directory}")

# 初始化数据（无论如何都要加载）
load_standard_prices()
load_occw_prices()
load_sku_mappings()


def preprocess_customer_type_data(df):
    """预处理客户类型数据"""
    try:
        # 处理客户/公司类型列
        if '客户/公司类型' in df.columns:
            df['客户/公司类型'] = df['客户/公司类型'].fillna('未设置')
            df['客户/公司类型'] = df['客户/公司类型'].replace('', '未设置')
            df['客户/公司类型'] = df['客户/公司类型'].replace('nan', '未设置')
            df['客户/公司类型'] = df['客户/公司类型'].replace('NaN', '未设置')
        else:
            df['客户/公司类型'] = '未设置'
        
        # 处理客户/类型列
        if '客户/类型' in df.columns:
            df['客户/类型'] = df['客户/类型'].fillna('未设置')
            df['客户/类型'] = df['客户/类型'].replace('', '未设置')
            df['客户/类型'] = df['客户/类型'].replace('nan', '未设置')
            df['客户/类型'] = df['客户/类型'].replace('NaN', '未设置')
        else:
            df['客户/类型'] = '未设置'
        
        return df
        
    except Exception as e:
        print(f"预处理客户类型数据时出错: {str(e)}")
        # 如果出错，设置默认值
        df['客户/公司类型'] = '未设置'
        df['客户/类型'] = '未设置'
        return df

@app.route('/get_customer_type_options', methods=['GET'])
def get_customer_type_options():
    """获取客户类型选项（动态从数据中提取）"""
    try:
        # 从session中获取当前导入的数据文件路径
        imported_data_file = session.get('imported_data_file')
        if not imported_data_file or not os.path.exists(imported_data_file):
            return jsonify({
                'success': False,
                'error': _('no_data_found')
            })
        
        # 读取导入的数据
        with open(imported_data_file, 'r', encoding='utf-8') as f:
            imported_data = json.load(f)
        
        if not imported_data:
            return jsonify({
                'success': False,
                'error': _('no_data_found')
            })
        
        # 提取唯一的客户类型和公司类型
        customer_types = set()
        company_types = set()
        
        for record in imported_data:
            # 提取客户类型
            customer_type = record.get('客户/类型', '未设置')
            if customer_type and customer_type != '未设置':
                customer_types.add(customer_type)
            
            # 提取公司类型
            company_type = record.get('客户/公司类型', '未设置')
            if company_type and company_type != '未设置':
                company_types.add(company_type)
        
        return jsonify({
            'success': True,
            'customer_types': sorted(list(customer_types)),
            'company_types': sorted(list(company_types))
        })
        
    except Exception as e:
        print(f"获取客户类型选项时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # 确保Jinja2定界符配置正确
    configure_jinja2_delimiters()
    
    # 加载数据
    load_standard_prices()
    load_occw_prices()
    load_sku_mappings()
    load_system_settings()
    load_users()
    load_quotations()
    
    # 生产环境配置
    port = int(os.environ.get('PORT', 999))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug) 