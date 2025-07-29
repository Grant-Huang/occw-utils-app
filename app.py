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
from typing import Dict, List, Tuple, Any

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
sku_rules = {}  # SKU生成规则配置

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
                print(f"已加载SKU规则配置")
        else:
            # 如果没有配置文件，复制默认配置
            if os.path.exists('sku_rules.json'):
                with open('sku_rules.json', 'r', encoding='utf-8') as f:
                    sku_rules = json.load(f)
                save_sku_rules()  # 保存到data目录
                print(f"已复制默认SKU规则配置")
            else:
                sku_rules = {}
    except Exception as e:
        print(f"加载SKU规则失败: {e}")
        sku_rules = {}

def save_sku_rules():
    """保存SKU规则配置"""
    try:
        with open('data/sku_rules.json', 'w', encoding='utf-8') as f:
            json.dump(sku_rules, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存SKU规则失败: {e}")
        return False

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
    """根据配置的规则生成SKU"""
    global sku_rules
    
    description_upper = description.upper()
    door_color = door_color or 'N/A'
    
    # 使用配置的规则
    if 'pdf_parsing_rules' in sku_rules and 'rules' in sku_rules['pdf_parsing_rules']:
        for rule in sku_rules['pdf_parsing_rules']['rules']:
            if not rule.get('enabled', True):
                continue
                
            pattern = rule.get('pattern', '')
            if pattern == '*' or pattern.upper() in description_upper:
                # 应用规则
                format_str = rule.get('format', '')
                preprocessing = rule.get('preprocessing', '')
                
                # 预处理
                processed_user_code = user_code
                if preprocessing and 'L和-R后缀' in preprocessing:
                    processed_user_code = user_code.replace('-L', '').replace('-R', '')
                
                # 生成SKU
                sku = format_str.replace('{user_code}', processed_user_code)\
                                .replace('{occw_code}', processed_user_code)\
                                .replace('{door_color}', door_color)
                return sku
    
    # 回退到硬编码规则
    if 'CABINET' in description_upper:
        occw_code = user_code.replace('-L', '').replace('-R', '')
        return f"{occw_code}-PLY-{door_color}"
    elif 'HARDWARE' in description_upper:
        return f"HW-{user_code}"
    elif 'ACCESSORY' in description_upper:
        return f"{door_color}-{user_code}"
    else:
        return f"{door_color}-{user_code}"

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
    if not possible_skus:
        if category == "Assm.组合件":
            if product and box_variant and door_variant:
                possible_skus.append(f"{product}-{box_variant}-{door_variant}")
        elif category == "Door":
            if product and door_variant:
                possible_skus.append(f"{door_variant}-{product}-Door")
        elif category == "BOX":
            if door_variant and not box_variant:
                if product.upper().endswith("-OPEN"):
                    possible_skus.append(f"{door_variant}-{product}")
                else:
                    possible_skus.append(f"{door_variant}-{product}-OPEN")
            elif box_variant:
                possible_skus.append(f"{box_variant}-{product}-BOX")
        elif category == "HARDWARE":
            possible_skus.append(f"HW-{product}")
        else:
            possible_skus.append(product)
            if door_variant:
                possible_skus.append(f"{product}-{door_variant}")
    
    return possible_skus

def evaluate_sku_condition(condition, product, box_variant, door_variant):
    """评估SKU生成条件"""
    if not condition:
        return True
        
    # 简单的条件评估
    condition = condition.replace('product', str(bool(product)))
    condition = condition.replace('box_variant', str(bool(box_variant)))
    condition = condition.replace('door_variant', str(bool(door_variant)))
    condition = condition.replace('&&', ' and ')
    condition = condition.replace('!', ' not ')
    
    try:
        return eval(condition)
    except:
        return True

def apply_sku_format(format_str, product, box_variant, door_variant, special_handling=""):
    """应用SKU格式模板"""
    if not format_str or not product:
        return None
        
    # 处理特殊情况
    if special_handling and "不重复添加" in special_handling and "OPEN" in special_handling:
        if product.upper().endswith("-OPEN") and format_str.endswith("-OPEN"):
            # 移除格式中的-OPEN后缀
            format_str = format_str.replace("-OPEN", "")
    
    # 替换变量
    sku = format_str.replace('{product}', product)\
                    .replace('{product_name}', product)\
                    .replace('{box_variant}', box_variant or '')\
                    .replace('{door_variant}', door_variant or '')
    
    # 清理空的连字符
    sku = re.sub(r'-+', '-', sku)  # 多个连字符合并为一个
    sku = sku.strip('-')  # 去掉首尾的连字符
    
    return sku if sku else None

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
        return jsonify({'error': f'清空映射关系失败: {str(e)}'}), 500

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
        return jsonify({'error': f'导出映射关系失败: {str(e)}'}), 500

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

@app.route('/rules')
@admin_required
def rules_page():
    """SKU规则配置页面"""
    return render_template('rules.html')

@app.route('/get_sku_rules', methods=['GET'])
@admin_required  
def get_sku_rules():
    """获取SKU规则配置"""
    return jsonify(sku_rules)

@app.route('/save_sku_rules', methods=['POST'])
@admin_required
def save_sku_rules_api():
    """保存SKU规则配置"""
    try:
        global sku_rules
        sku_rules = request.json
        success = save_sku_rules()
        if success:
            return jsonify({'success': True, 'message': 'SKU规则保存成功'})
        else:
            return jsonify({'success': False, 'message': '保存失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/reset_sku_rules', methods=['POST'])
@admin_required
def reset_sku_rules():
    """重置SKU规则到默认配置"""
    try:
        global sku_rules
        if os.path.exists('sku_rules.json'):
            with open('sku_rules.json', 'r', encoding='utf-8') as f:
                sku_rules = json.load(f)
            success = save_sku_rules()
            if success:
                return jsonify({'success': True, 'message': '已恢复默认配置'})
            else:
                return jsonify({'success': False, 'message': '恢复失败'}), 500
        else:
            return jsonify({'success': False, 'message': '默认配置文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'恢复失败: {str(e)}'}), 500

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
        return jsonify({'error': f'获取产品类别失败: {str(e)}'}), 500

@app.route('/get_products_by_category', methods=['GET'])
def get_products_by_category():
    """根据类别获取产品列表 - 使用结构化数据"""
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': '缺少category参数'}), 400
        
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
        return jsonify({'error': f'获取产品列表失败: {str(e)}'}), 500

@app.route('/search_sku_price', methods=['GET'])
def search_sku_price():
    """根据产品信息搜索SKU和价格"""
    try:
        category = request.args.get('category', '')
        product = request.args.get('product', '')
        box_variant = request.args.get('box_variant', '')
        door_variant = request.args.get('door_variant', '')
        
        # 根据配置的规则生成可能的SKU
        possible_skus = generate_sku_by_rules(category, product, box_variant, door_variant)
        
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
        return jsonify({'error': f'搜索SKU失败: {str(e)}'}), 500

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
        return jsonify({'error': f'获取价格表失败: {str(e)}'}), 500

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
        return jsonify({'error': f'获取过滤选项失败: {str(e)}'}), 500

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