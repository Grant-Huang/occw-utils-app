# OCCW报价与销售分析系统设计文档

## 目录

1. [项目概述](#项目概述)
2. [需求设计](#需求设计)
3. [架构设计](#架构设计)
4. [功能设计](#功能设计)
5. [数据结构设计](#数据结构设计)
6. [转换规则详解](#转换规则详解)
7. [API设计](#api设计)
8. [界面设计](#界面设计)
9. [部署说明](#部署说明)
10. [版本更新记录](#版本更新记录)

---

## 项目概述

### 1.1 项目背景

OCCW报价与销售分析系统（OCCW Quote & Sales Analysis Platform）是一个综合性的Web应用平台，专门用于厨柜行业的报价管理和销售数据分析。该系统能够：

- **报价管理**：解析PDF格式的报价单文档，自动识别和转换产品SKU
- **价格管理**：管理OCCW价格表和映射关系，生成标准化报价单
- **销售分析**：完整的销售数据导入、转换、分析和可视化功能
- **智能过滤**：灵活的数据导入过滤条件配置，支持金额区间过滤
- **多语言界面**：支持中文、英文、法文三语言切换
- **数据可视化**：Chart.js图表展示销售趋势和转化率分析
- **用户权限管理**：管理员和普通用户权限分离
- **数据导出**：多格式数据导出（Excel、PDF）

### 1.2 系统特点

- **自动化处理**：减少手工转换的工作量和错误率
- **智能识别**：基于规则的SKU识别和转换
- **灵活配置**：支持自定义映射规则和价格管理
- **多语言支持**：适应国际化需求
- **现代化界面**：基于Bootstrap 5的响应式设计

---

## 需求设计

### 2.1 功能需求

#### 2.1.1 核心功能需求

| 功能模块 | 描述 | 优先级 |
|---------|------|-------|
| PDF解析 | 解析上传的PDF报价单，提取产品信息 | P0 |
| SKU转换 | 将原始SKU转换为OCCW标准SKU | P0 |
| 价格查询 | 根据SKU查询OCCW价格表中的价格 | P0 |
| 报价生成 | 生成标准化的OCCW报价单 | P0 |
| 映射管理 | 管理SKU映射关系 | P1 |
| 价格管理 | 管理OCCW价格表 | P1 |
| 多语言支持 | 支持中英法三种语言 | P2 |
| **销售数据导入** | 导入Excel格式的销售订单数据 | P1 |
| **销售数据转换** | 将原始数据转换为标准化分析格式 | P1 |
| **销售业绩分析** | 销售员业绩统计和转化率分析 | P1 |
| **客户订单分析** | 客户转化率和订单趋势分析 | P1 |
| **数据过滤系统** | 灵活的导入数据过滤条件配置 | P1 |
| **数据可视化** | 图表展示销售趋势和转化率 | P2 |

#### 2.1.2 业务需求

1. **准确性要求**
   - SKU识别准确率 ≥ 95%
   - 价格匹配准确率 ≥ 98%
   - 支持手动校正机制

2. **性能要求**
   - PDF解析时间 ≤ 30秒
   - 页面响应时间 ≤ 3秒
   - 支持并发用户数 ≥ 10

3. **兼容性要求**
   - 支持PDF 1.4+版本
   - 支持Excel .xlsx/.xls格式
   - 兼容主流浏览器

### 2.2 非功能需求

#### 2.2.1 性能需求

- **响应时间**：页面加载 < 3秒，API响应 < 1秒
- **并发处理**：支持10个并发用户
- **数据容量**：支持100万条价格记录
- **文件大小**：支持最大16MB的PDF文件

#### 2.2.2 安全需求

- **访问控制**：管理员密码保护
- **数据安全**：敏感数据加密存储
- **文件安全**：上传文件类型验证
- **会话管理**：安全的会话机制

#### 2.2.3 可用性需求

- **系统可用性**：99%正常运行时间
- **易用性**：直观的用户界面，操作步骤 ≤ 3步
- **容错性**：友好的错误提示和恢复机制
- **维护性**：模块化设计，便于扩展

---

## 架构设计

### 3.1 总体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   表示层(UI)     │    │   业务逻辑层     │    │    数据层       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • 报价单上传页面 │◄──►│ • PDF解析服务   │◄──►│ • OCCW价格表    │
│ • SKU映射管理   │    │ • SKU转换服务   │    │ • SKU映射表     │
│ • 价格表管理    │    │ • 价格查询服务   │    │ • 配置文件      │
│ • 系统配置页面  │    │ • 报价生成服务   │    │ • 日志文件      │
│ • 多语言支持    │    │ • 权限管理服务   │    │ • 临时文件      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2 技术架构

#### 3.2.1 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Bootstrap | 5.x | 响应式UI框架 |
| jQuery | 3.x | DOM操作和AJAX |
| Font Awesome | 6.x | 图标库 |
| HTML5 | - | 页面结构 |
| CSS3 | - | 样式设计 |
| JavaScript | ES6+ | 交互逻辑 |

#### 3.2.2 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Flask | 2.x | Web框架 |
| Python | 3.8+ | 后端语言 |
| PyPDF2 | 3.x | PDF解析 |
| pandas | 1.x | 数据处理 |
| ReportLab | 3.x | PDF生成 |
| Gunicorn | 20.x | WSGI服务器 |

#### 3.2.3 数据存储

| 类型 | 技术 | 用途 |
|------|------|------|
| 结构化数据 | JSON文件 | 价格表、映射关系 |
| 配置数据 | Python配置文件 | 系统配置 |
| 临时数据 | 文件系统 | 上传文件缓存 |
| 日志数据 | 日志文件 | 系统日志 |

### 3.3 部署架构

```
Internet
    │
    ▼
┌─────────────┐
│   负载均衡   │ (可选)
│  (Nginx)    │
└─────────────┘
    │
    ▼
┌─────────────┐
│  Web服务器   │
│  (Gunicorn) │
└─────────────┘
    │
    ▼
┌─────────────┐
│ Flask应用   │
│   (app.py)  │
└─────────────┘
    │
    ▼
┌─────────────┐
│  数据存储    │
│ (JSON文件)  │
└─────────────┘
```

---

## 功能设计

### 4.1 报价单处理功能

#### 4.1.1 PDF上传与解析

**输入**：PDF格式的报价单文件
**输出**：结构化的产品数据

**处理流程**：
1. 文件上传验证（格式、大小）
2. PDF文本内容提取
3. 文本清理和格式化
4. 产品信息识别和提取
5. 数据结构化组织

**关键算法**：
```python
def extract_pdf_content(pdf_path):
    """提取PDF内容的核心算法"""
    # 1. 打开PDF文件
    # 2. 逐页提取文本
    # 3. 清理特殊字符
    # 4. 识别表格结构
    # 5. 提取产品信息
    return structured_data
```

#### 4.1.2 产品信息识别

**识别规则**：
- **序列号识别**：数字序列 + 可选后缀
- **产品代码识别**：字母数字组合模式
- **尺寸识别**：宽x深x高 格式
- **数量识别**：纯数字或 数字+单位
- **描述识别**：文本描述信息

### 4.2 SKU转换功能

#### 4.2.1 转换规则引擎

**规则类型**：
1. **直接映射**：一对一映射关系（通过SKU映射表）
2. **产品类型识别**：基于产品描述的类型判断
3. **硬编码规则**：预定义的产品类型转换规则

**简化说明**：
- 系统已移除复杂的规则配置功能
- 使用简化的硬编码规则进行SKU生成
- 支持通过映射表进行自定义SKU转换

#### 4.2.2 SKU生成规则

**OCCW SKU格式**：`产品名-变体1-变体2`

**生成逻辑**：
```python
def generate_sku(user_code, description, door_color):
    """SKU生成核心逻辑"""
    description_upper = description.upper()
    processed_user_code = user_code.replace('-L', '').replace('-R', '')
    
    # 根据产品类型生成SKU
    if 'CABINET' in description_upper or 'BOX' in description_upper:
        return f"{processed_user_code}-PLY-{door_color}"
    elif 'DOOR' in description_upper:
        return f"{processed_user_code}-DOOR-{door_color}"
    elif 'HARDWARE' in description_upper or 'HW' in description_upper:
        return f"HW-{user_code}"
    elif 'MOLDING' in description_upper:
        return f"{door_color}-MOLD-{user_code}"
    elif 'TOE KICK' in description_upper:
        return f"{door_color}-TK-{user_code}"
    elif 'FILLER' in description_upper:
        return f"{door_color}-FILL-{user_code}"
    elif 'ENDING PANEL' in description_upper or 'END PANEL' in description_upper:
        return f"{door_color}-EP-{user_code}"
    elif 'RTA ASSM' in description_upper or 'ASSEMBLY' in description_upper:
        return f"{processed_user_code}-ASSM-{door_color}"
    else:
        return f"{door_color}-{user_code}"
```

**SKU格式说明**：
- **柜身类**：`{产品代码}-PLY-{门板颜色}`
- **门板类**：`{产品代码}-DOOR-{门板颜色}`
- **五金件**：`HW-{产品代码}`
- **装饰条**：`{门板颜色}-MOLD-{产品代码}`
- **踢脚线**：`{门板颜色}-TK-{产品代码}`
- **填充板**：`{门板颜色}-FILL-{产品代码}`
- **端板**：`{门板颜色}-EP-{产品代码}`
- **组合件**：`{产品代码}-ASSM-{门板颜色}`

### 4.3 价格查询功能

#### 4.3.1 价格匹配算法

**匹配优先级**：
1. **精确匹配**：完全相同的SKU
2. **映射匹配**：通过映射表查找
3. **模糊匹配**：相似度匹配
4. **默认价格**：使用默认值

#### 4.3.2 价格数据结构

```json
{
  "sku": {
    "product_name": "产品名称",
    "door_variant": "门板变体",
    "box_variant": "柜身变体", 
    "category": "产品类别",
    "unit_price": 价格数值,
    "updated_at": "更新时间"
  }
}
```

### 4.4 映射管理功能

#### 4.4.1 映射关系类型

| 类型 | 描述 | 示例 |
|------|------|------|
| 直接映射 | 原始SKU直接对应OCCW SKU | `B36FH-PLY-WSS` → `B36FH-PB-WSS` |
| 格式转换 | 格式调整后映射 | `PGW-WF330 FOR` → `PGW-WF330` |
| 组合映射 | 多个原始SKU对应一个OCCW SKU | - |
| 拆分映射 | 一个原始SKU对应多个OCCW SKU | - |

#### 4.4.2 映射优先级

1. **用户自定义映射** (优先级：最高)
2. **系统自动映射** (优先级：中等)
3. **默认规则映射** (优先级：最低)

### 4.5 销售数据分析功能

#### 4.5.1 数据导入与过滤

**导入流程**：
1. Excel文件上传验证
2. 数据格式标准化
3. 应用导入过滤条件
4. 数据转换处理
5. 临时存储和持久化

**智能过滤系统**：
```python
# 支持的过滤条件
filter_conditions = {
    'import_filter_min_amount': 1000,           # 最小金额阈值
    'import_filter_sales_person': 'John,Mary',   # 销售人员（多选）
    'import_filter_customer': 'CustomerA',      # 客户过滤
    'import_filter_start_date': '2024-01-01',   # 开始日期
    'import_filter_end_date': '2024-12-31',     # 结束日期
    'import_filter_order_status': '销售订单,报价单' # 订单状态（多选）
}
```

**动态状态获取**：
- 从已导入数据中实时提取所有可能的订单状态
- 支持多选复选框界面
- 全选/部分选择/全不选三态支持

#### 4.5.2 数据转换与标准化

**转换规则**：
```python
def convert_sales_data(raw_data):
    """销售数据转换核心逻辑"""
    for record in raw_data:
        if record['订单状态'] == '销售订单':
            # 销售订单：订单金额=总计，报价单金额=总计
            record['订单金额'] = record['总计']
            record['报价单金额'] = record['总计']
            record['订单数量'] = 1
            record['报价单数量'] = 1
        elif record['订单状态'] == '报价单':
            # 报价单：订单金额=0，报价单金额=总计
            record['订单金额'] = 0
            record['报价单金额'] = record['总计']
            record['订单数量'] = 0
            record['报价单数量'] = 1
    return converted_data
```

**转化率计算**：
- 数量转化率 = 订单数量 / 报价单数量 × 100%
- 金额转化率 = 订单金额 / 报价单金额 × 100%

#### 4.5.3 销售业绩分析

**分析维度**：
1. **销售员业绩分析**
   - 订单金额统计
   - 报价单金额统计
   - 数量转化率
   - 金额转化率
   - 平均毛利率

2. **客户订单分析**
   - 客户转化率统计
   - 订单金额排名
   - 客户价值分析

3. **时间趋势分析**
   - 按月/按周销售趋势
   - 转化率变化趋势
   - 业绩对比分析

#### 4.5.4 数据可视化

**图表类型**：
1. **订单金额转化率分析**
   - 主Y轴：订单金额、总报价金额（实线）
   - 副Y轴：金额转化率（虚线）

2. **订单数量转化率分析**
   - 主Y轴：订单数、总报价数量（实线）
   - 副Y轴：数量转化率（虚线）

3. **销售人员对比图表**
   - 数量对比图
   - 金额对比图
   - 转化率对比图

**交互功能**：
- 按销售人员过滤
- 时间周期选择（月/周）
- 金额区间过滤（≤1000、1000-5000、5000-10000、≥10000、全部金额）
- 图表最大化显示
- 数据导出功能

#### 4.5.5 多语言支持系统

**完整国际化支持**：
```python
# 翻译系统示例
TRANSLATIONS = {
    'zh': {
        'system_name': 'OCCW报价与销售分析系统',
        'count_conversion_rate': '数量转化率',
        'amount_conversion_rate': '金额转化率',
        'start_date': '开始日期',
        'end_date': '结束日期',
        'amount_range': '金额区间',
        'update_analysis_table': '更新分析表格'
    },
    'en': {
        'system_name': 'OCCW Quote & Sales Analysis System',
        'count_conversion_rate': 'Count Conversion Rate',
        'amount_conversion_rate': 'Amount Conversion Rate',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'amount_range': 'Amount Range',
        'update_analysis_table': 'Update Analysis Table'
    },
    'fr': {
        'system_name': 'Système OCCW de Devis et d\'Analyse des Ventes',
        'count_conversion_rate': 'Taux de Conversion Quantité',
        'amount_conversion_rate': 'Taux de Conversion Montant',
        'start_date': 'Date de Début',
        'end_date': 'Date de Fin',
        'amount_range': 'Plage de Montant',
        'update_analysis_table': 'Mettre à Jour le Tableau d\'Analyse'
    }
}
```

**语言切换功能**：
- 实时语言切换，无需重新登录
- 保持用户语言偏好在会话中
- 所有界面元素完整翻译

#### 4.5.6 数据存储策略

**临时文件存储**：
```python
# 导入数据临时存储
imported_data_file = f"imported_data_{uuid}.json"
converted_data_file = f"converted_data_{uuid}.json"

# Session管理
session = {
    'imported_data_file': file_path,
    'converted_data_file': converted_file_path,
    'imported_data_count': record_count,
    'converted_data_count': converted_count,
    'imported_data_timestamp': datetime.now()
}
```

**数据清理机制**：
- 自动清理超过1小时的临时文件
- 防止磁盘空间占用过多
- 支持手动清理功能

---

## 数据结构设计

### 5.1 核心数据结构

#### 5.1.1 产品信息结构

```python
ProductInfo = {
    "seq_num": int,           # 序列号
    "user_code": str,         # 用户代码
    "manufacturer_code": str, # 制造商代码
    "size": str,             # 尺寸
    "quantity": int,         # 数量
    "description": str,      # 描述
    "original_line": str     # 原始行文本
}
```

#### 5.1.2 OCCW价格结构

```python
OCCWPrice = {
    "product_name": str,     # 产品名称
    "door_variant": str,     # 门板变体
    "box_variant": str,      # 柜身变体
    "category": str,         # 产品类别
    "unit_price": float,     # 单价
    "updated_at": str        # 更新时间
}
```

#### 5.1.3 SKU映射结构

```python
SKUMapping = {
    "original_sku": str,     # 原始SKU
    "mapped_sku": str,       # 映射后的SKU
    "mapping_type": str,     # 映射类型
    "created_at": str,       # 创建时间
    "updated_at": str        # 更新时间
}
```

### 5.2 配置数据结构

#### 5.2.1 系统配置

```python
SystemConfig = {
    "version": str,          # 系统版本
    "company_info": {        # 公司信息
        "name_zh": str,
        "name_en": str,
        "name_fr": str
    },
    "system_name": {         # 系统名称
        "zh": str,
        "en": str,
        "fr": str
    },
    "default_language": str  # 默认语言
}
```

#### 5.2.2 转换规则配置

```python
ConversionRules = {
    "category_mapping": {    # 类别映射
        "原始类别": "OCCW类别"
    },
    "variant_patterns": {    # 变体模式
        "door_pattern": str,
        "box_pattern": str
    },
    "sku_patterns": {        # SKU模式
        "pattern": str,
        "replacement": str
    }
}
```

---

## 转换规则详解

### 6.0 配置化规则系统

#### 6.0.1 系统概述

从v2.1版本开始，OCCW报价系统采用配置化的SKU规则管理，所有规则都可以通过可视化界面实时修改，无需重新部署系统。

**🔧 三种应用场景**：
1. **PDF解析规则** - 用于2020软件导出的PDF识别
2. **OCCW导入规则** - 用于Excel价格表导入时的SKU生成  
3. **手动创建规则** - 用于报价单手动创建时的SKU组合

#### 6.0.2 配置文件结构

**文件位置**：
- **默认配置**：`sku_rules.json` (系统默认规则)
- **运行配置**：`data/sku_rules.json` (实际使用的规则)
- **管理界面**：`/rules` (可视化配置管理)

**配置结构**：
```json
{
  "version": "1.0",
  "pdf_parsing_rules": {
    "rules": [
      {
        "id": "cabinet_rule",
        "pattern": "CABINET",
        "format": "{occw_code}-PLY-{door_color}",
        "enabled": true
      }
    ]
  },
  "occw_import_rules": {
    "category_rules": [
      {
        "id": "assembly_rule", 
        "category": ["组合件"],
        "sku_format": "{product_name}-{box_variant}-{door_variant}",
        "enabled": true
      }
    ]
  },
  "manual_quote_rules": {
    "rules": [
      {
        "id": "box_open_manual",
        "category": "BOX",
        "condition": "door_variant && !box_variant",
        "sku_format": "{door_variant}-{product}-OPEN",
        "enabled": true
      }
    ]
  }
}
```

#### 6.0.3 规则管理功能

**📋 管理界面功能**：
- ✅ 可视化规则编辑
- ✅ 实时规则验证
- ✅ JSON格式编辑器
- ✅ 规则启用/禁用
- ✅ 导入/导出配置
- ✅ 恢复默认设置

**🔄 规则应用顺序**：
1. 加载配置文件中的规则
2. 按启用状态过滤规则
3. 按条件匹配应用规则
4. 回退到硬编码规则（兼容性）

### 6.1 产品类别转换规则

#### 6.1.1 类别映射表

| 原始类别 | OCCW类别 | 描述 |
|---------|----------|------|
| RTA Assm.组合件 | Assm.组合件 | 成品组合柜 |
| Door | Door | 门板产品 |
| BOX | BOX | 柜体产品 |
| Ending Panel | Ending Panel | 结束面板 |
| Molding | Molding | 装饰条 |
| Toe Kick | Toe Kick | 踢脚板 |
| Filler | Filler | 填充条 |
| 其他 | HARDWARE | 五金配件 |

#### 6.1.2 类别识别规则

```python
def identify_category(product_name, description):
    """产品类别识别规则"""
    if "组合件" in description or "Assm" in description:
        return "Assm.组合件"
    elif "Door" in product_name or "门板" in description:
        return "Door"
    elif "BOX" in product_name or "柜体" in description:
        return "BOX"
    elif "Panel" in product_name:
        return "Ending Panel"
    elif "Molding" in product_name or "装饰条" in description:
        return "Molding"
    elif "Kick" in product_name or "踢脚" in description:
        return "Toe Kick"
    elif "Filler" in product_name or "填充" in description:
        return "Filler"
    else:
        return "HARDWARE"
```

### 6.2 变体识别转换规则

#### 6.2.1 门板变体规则

**门板变体格式**：`门板: XXX`（XXX为2-3个字符的变体代码）

**常见门板变体**：
- `BSS` - 巧克力色
- `GSS` - 灰色
- `MNW` - 自然色
- `MWM` - 白色哑光
- `PGW` - 纯白色
- `SSW` - 软白色
- `WSS` - 白色

```python
def extract_door_variant(variant_value):
    """门板变体提取规则"""
    if variant_value.startswith("门板: "):
        variant = variant_value.replace("门板: ", "")
        if 2 <= len(variant) <= 3:
            return variant
    return ""
```

#### 6.2.2 柜身变体规则

**柜身变体格式**：`柜身: XXX`（XXX为变体代码）

**常见柜身变体**：
- `PLY` - 胶合板
- `PB` - 刨花板

```python
def extract_box_variant(variant_value):
    """柜身变体提取规则"""
    if variant_value.startswith("柜身: "):
        variant = variant_value.replace("柜身: ", "")
        if 2 <= len(variant) <= 3:
            return variant
    return ""
```

### 6.3 SKU生成转换规则

#### 6.3.1 组合件SKU规则

**格式**：`产品名-柜身变体-门板变体`
**示例**：`2DB30-PLY-BSS`

```python
def generate_assembly_sku(product_name, door_variant, box_variant):
    """组合件SKU生成规则"""
    return f"{product_name}-{box_variant}-{door_variant}"
```

#### 6.3.2 门板SKU规则

**格式**：`门板变体-产品名称-"Door"`
**示例**：`MNW-DOOR-Door`

```python
def generate_door_sku(product_name, variant):
    """门板SKU生成规则"""
    return f"{variant}-{product_name}-Door"
```

#### 6.3.3 柜体SKU规则

**标准柜体格式**：`柜身变体-产品名称-"BOX"`
**开放式柜体格式**：`门板变体-产品名称-"OPEN"`

**判断规则**：
- 如果选择了门板变体但没有选择柜身变体 → 开放式柜体
- 如果选择了柜身变体 → 标准柜体
- 如果产品名称已经包含"-OPEN"，则不重复添加"-OPEN"后缀

```python
def generate_box_sku(product_name, door_variant, box_variant):
    """柜体SKU生成规则"""
    # 判断是开放式柜体还是标准柜体
    if door_variant and not box_variant:
        # 开放式柜体：有门板变体但没有柜身变体
        if product_name.upper().endswith("-OPEN"):
            return f"{door_variant}-{product_name}"  # 不重复添加-OPEN
        else:
            return f"{door_variant}-{product_name}-OPEN"
    elif box_variant:
        # 标准柜体：有柜身变体
        return f"{box_variant}-{product_name}-BOX"
    else:
        return None  # 无法生成SKU
```

**使用示例**：

| 选择情况 | 门板变体 | 柜身变体 | 产品名称 | 生成SKU | 类型 |
|---------|---------|---------|----------|---------|------|
| 情况1 | BSS | PLY | B36FH | `PLY-B36FH-BOX` | 标准柜体 |
| 情况2 | BSS | (无) | WMC2418 | `BSS-WMC2418-OPEN` | 开放式柜体 |
| 情况3 | GSS | (无) | WOC3015 | `GSS-WOC3015-OPEN` | 开放式柜体 |
| 情况4 | MNW | (无) | WMC2418-OPEN | `MNW-WMC2418-OPEN` | 开放式柜体(避免重复) |

#### 6.3.4 五金件SKU规则

**格式**：`HW-产品名`
**示例**：`HW-HINGE`

```python
def generate_hardware_sku(product_name):
    """五金件SKU生成规则"""
    return f"HW-{product_name}"
```

### 6.4 特殊转换规则

#### 6.4.1 尺寸标准化规则

```python
def standardize_size(size_str):
    """尺寸标准化规则"""
    # 移除多余空格和特殊字符
    size = re.sub(r'[^\d.x×]', '', size_str)
    # 统一使用 x 作为分隔符
    size = size.replace('×', 'x')
    return size
```

#### 6.4.2 产品名称清理规则

```python
def clean_product_name(name):
    """产品名称清理规则"""
    # 移除前后空格
    name = name.strip()
    # 移除特殊前缀
    prefixes = ['PLY-', 'PB-', 'OCCW-']
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name
```

#### 6.4.3 数量处理规则

```python
def parse_quantity(qty_str):
    """数量解析规则"""
    # 提取数字部分
    qty_match = re.search(r'(\d+)', str(qty_str))
    if qty_match:
        return int(qty_match.group(1))
    return 1  # 默认数量
```

### 6.5 映射优先级规则

#### 6.5.1 映射查找顺序

1. **精确匹配**：在映射表中查找完全匹配的原始SKU
2. **模式匹配**：使用正则表达式模式匹配
3. **相似度匹配**：基于字符串相似度的模糊匹配
4. **默认规则**：使用系统默认的转换规则

#### 6.5.2 冲突解决规则

```python
def resolve_mapping_conflict(original_sku, candidates):
    """映射冲突解决规则"""
    # 1. 优先选择用户自定义映射
    user_defined = [c for c in candidates if c['type'] == 'user_defined']
    if user_defined:
        return user_defined[0]
    
    # 2. 选择最新的系统映射
    system_mappings = [c for c in candidates if c['type'] == 'system']
    if system_mappings:
        return max(system_mappings, key=lambda x: x['updated_at'])
    
    # 3. 使用默认规则
    return candidates[0] if candidates else None
```

---

## API设计

### 7.1 RESTful API规范

#### 7.1.1 通用响应格式

```json
{
  "success": boolean,
  "message": string,
  "data": object,
  "error": string,
  "timestamp": string
}
```

#### 7.1.2 HTTP状态码规范

| 状态码 | 描述 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 请求成功处理 |
| 400 | 客户端错误 | 参数错误、格式错误 |
| 401 | 未授权 | 需要管理员权限 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器错误 | 内部处理错误 |

### 7.2 核心API接口

#### 7.2.1 报价单处理API

```http
POST /upload_quote
Content-Type: multipart/form-data

Parameters:
- file: PDF文件
- language: 语言设置(可选)

Response:
{
  "success": true,
  "data": {
    "products": [...],
    "total_items": 10,
    "processed_at": "2024-01-01T00:00:00"
  }
}
```

#### 7.2.2 SKU映射API

```http
# 获取所有映射
GET /get_sku_mappings

# 保存映射
POST /save_sku_mapping
Content-Type: application/json
{
  "original_sku": "string",
  "mapped_sku": "string"
}

# 删除映射
POST /delete_sku_mapping
Content-Type: application/json
{
  "original_sku": "string"
}

# 批量清空映射
POST /clear_all_sku_mappings

# 导出映射
GET /export_sku_mappings
```

#### 7.2.3 价格管理API

```http
# 获取价格表
GET /get_occw_price_table
Parameters:
- page: 页码
- per_page: 每页数量
- search: 搜索关键词

# 上传价格表
POST /upload_occw_prices
Content-Type: multipart/form-data
- file: Excel文件
- import_mode: 导入模式(create/append)

# 获取单个SKU价格
GET /get_occw_price
Parameters:
- sku: SKU代码

# 获取统计信息
GET /get_occw_stats
```

#### 7.2.4 系统管理API

```http
# 管理员登录
POST /admin_login
Content-Type: application/x-www-form-urlencoded
- password: 管理员密码

# 获取SKU列表
GET /get_occw_skus
Parameters:
- filter_user_code: 过滤条件(可选)

# 搜索SKU价格
GET /search_sku_price
Parameters:
- category: 产品类别
- product: 产品名称
- box_variant: 柜身变体
- door_variant: 门板变体
```

### 7.3 API安全设计

#### 7.3.1 身份验证

```python
@admin_required
def protected_endpoint():
    """需要管理员权限的端点装饰器"""
    if ADMIN_SESSION_KEY not in session:
        return redirect(url_for('admin_login'))
    return function()
```

#### 7.3.2 请求验证

```python
def validate_file_upload(file):
    """文件上传验证"""
    if not file or file.filename == '':
        raise ValueError("没有选择文件")
    
    if not file.filename.endswith(('.pdf', '.xlsx', '.xls')):
        raise ValueError("文件格式不支持")
    
    if file.content_length > MAX_FILE_SIZE:
        raise ValueError("文件过大")
```

---

## 界面设计

### 8.1 设计原则

#### 8.1.1 用户体验原则

- **简洁性**：界面简洁清晰，操作流程直观
- **一致性**：统一的设计语言和交互模式
- **响应性**：支持各种设备屏幕尺寸
- **可访问性**：支持键盘导航和屏幕阅读器

#### 8.1.2 视觉设计原则

- **层次性**：清晰的信息层次结构
- **对比性**：适当的颜色对比和字体大小
- **平衡性**：页面元素的平衡布局
- **统一性**：一致的颜色方案和组件样式

### 8.2 页面结构设计

#### 8.2.1 主导航结构

```
导航栏
├── 首页 (报价单上传)
├── 价格表管理 [管理员]
├── SKU映射管理 [管理员]
├── 帮助文档
├── 登录/登出
└── 语言切换
```

**说明**：
- 系统已简化，移除了复杂的规则配置功能
- 价格表管理和SKU映射管理需要管理员权限
- 系统配置功能已移除，简化了管理界面

#### 8.2.2 页面布局模板

```html
<!DOCTYPE html>
<html>
<head>
  <!-- Meta标签、CSS引用 -->
</head>
<body>
  <!-- 导航栏 -->
  <nav class="navbar">...</nav>
  
  <!-- 主内容区 -->
  <main class="container">
    <!-- 页面头部 -->
    <header>...</header>
    
    <!-- 内容区域 -->
    <section>...</section>
    
    <!-- 页脚 -->
    <footer>...</footer>
  </main>
  
  <!-- JavaScript引用 -->
</body>
</html>
```

### 8.3 组件设计规范

#### 8.3.1 按钮组件

| 类型 | 样式类 | 用途 |
|------|--------|------|
| 主要按钮 | `.btn-primary` | 主要操作 |
| 次要按钮 | `.btn-secondary` | 次要操作 |
| 成功按钮 | `.btn-success` | 确认操作 |
| 危险按钮 | `.btn-danger` | 删除操作 |
| 警告按钮 | `.btn-warning` | 警告操作 |

#### 8.3.2 表单组件

```html
<!-- 标准表单组 -->
<div class="mb-3">
  <label for="input" class="form-label">标签</label>
  <input type="text" class="form-control" id="input">
  <div class="form-text">帮助文本</div>
</div>

<!-- 选择框 -->
<select class="form-select">
  <option>选项1</option>
  <option>选项2</option>
</select>

<!-- 文件上传 -->
<input type="file" class="form-control" accept=".pdf,.xlsx,.xls">
```

#### 8.3.3 表格组件

```html
<div class="table-responsive">
  <table class="table table-striped table-hover">
    <thead class="table-dark">
      <tr>
        <th>列1</th>
        <th>列2</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <!-- 数据行 -->
    </tbody>
  </table>
</div>
```

### 8.4 响应式设计

#### 8.4.1 断点设置

| 设备类型 | 断点 | 容器宽度 |
|---------|------|----------|
| 超小设备 | <576px | 100% |
| 小设备 | ≥576px | 540px |
| 中等设备 | ≥768px | 720px |
| 大设备 | ≥992px | 960px |
| 超大设备 | ≥1200px | 1140px |

#### 8.4.2 响应式布局

```css
/* 移动端优先的响应式设计 */
.container {
  padding: 1rem;
}

@media (min-width: 768px) {
  .container {
    padding: 2rem;
  }
}

@media (min-width: 1200px) {
  .container {
    max-width: 1140px;
  }
}
```

### 8.5 多语言界面设计

#### 8.5.1 语言切换组件

```html
<div class="dropdown">
  <button class="btn btn-outline-secondary dropdown-toggle" 
          data-bs-toggle="dropdown">
    <i class="fas fa-globe"></i> 中文
  </button>
  <ul class="dropdown-menu">
    <li><a class="dropdown-item" href="?lang=zh">中文</a></li>
    <li><a class="dropdown-item" href="?lang=en">English</a></li>
    <li><a class="dropdown-item" href="?lang=fr">Français</a></li>
  </ul>
</div>
```

#### 8.5.2 文本国际化

```python
# 翻译字典结构
TRANSLATIONS = {
    'zh': {
        'upload_quote': '上传报价单',
        'sku_mapping': 'SKU映射管理',
        'price_management': '价格表管理'
    },
    'en': {
        'upload_quote': 'Upload Quote',
        'sku_mapping': 'SKU Mapping',
        'price_management': 'Price Management'
    },
    'fr': {
        'upload_quote': 'Télécharger Devis',
        'sku_mapping': 'Mappage SKU',
        'price_management': 'Gestion des Prix'
    }
}
```

---

## 部署说明

### 9.1 环境要求

#### 9.1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Linux/Windows/macOS | Ubuntu 20.04+ |
| Python | 3.8+ | 3.10+ |
| 内存 | 512MB | 2GB+ |
| 存储 | 1GB | 10GB+ |
| 网络 | 10Mbps | 100Mbps+ |

#### 9.1.2 依赖包要求

```txt
Flask>=2.0.0
PyPDF2>=3.0.0
pandas>=1.5.0
reportlab>=3.6.0
gunicorn>=20.0.0
requests>=2.28.0
```

### 9.2 部署方式

#### 9.2.1 开发环境部署

```bash
# 1. 克隆代码
git clone <repository>
cd 2020-OCCW-convertor

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python app.py
```

#### 9.2.2 生产环境部署

```bash
# 1. 使用Gunicorn部署
gunicorn -c gunicorn.conf.py app:app

# 2. 使用Docker部署
docker build -t occw-converter .
docker run -p 5000:5000 occw-converter

# 3. 使用Railway部署
# 直接推送到Railway平台
```

#### 9.2.3 反向代理配置(Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    client_max_body_size 20M;
}
```

### 9.3 配置说明

#### 9.3.1 环境变量配置

```bash
# .env 文件
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=your-admin-password
FLASK_ENV=production
MAX_CONTENT_LENGTH=16777216
```

#### 9.3.2 应用配置

```python
# config.py
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
```

### 9.4 数据备份策略

#### 9.4.1 备份内容

- OCCW价格表 (`data/occw_prices.json`)
- SKU映射关系 (`data/sku_mappings.json`)
- 系统配置文件
- 上传的文件

#### 9.4.2 备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据文件
cp -r data/ $BACKUP_DIR/
cp -r uploads/ $BACKUP_DIR/

# 压缩备份
tar -czf "${BACKUP_DIR}.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: ${BACKUP_DIR}.tar.gz"
```

### 9.5 监控和维护

#### 9.5.1 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

#### 9.5.2 健康检查

```python
@app.route('/health')
def health_check():
    """系统健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'version': VERSION,
        'timestamp': datetime.now().isoformat()
    })
```

---

## 附录

### A.1 错误代码表

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| E001 | PDF文件格式错误 | 检查文件格式，重新上传 |
| E002 | 文件大小超限 | 压缩文件或分批处理 |
| E003 | SKU映射失败 | 检查映射规则配置 |
| E004 | 价格查询失败 | 检查价格表完整性 |
| E005 | 权限验证失败 | 重新登录管理员账户 |

### A.2 常见问题FAQ

**Q: PDF解析失败怎么办？**
A: 检查PDF文件是否包含可提取的文本，避免扫描版PDF。

**Q: SKU映射不准确如何调整？**
A: 使用SKU映射管理功能手动添加或修改映射关系。

**Q: 如何更新价格表？**
A: 使用价格表管理功能上传新的Excel文件。

## 版本更新记录

### v3.0.0 (2024-08-03) - 销售分析系统重大升级

#### 新增功能
- **全面销售数据分析系统**：完整的Excel数据导入、转换、分析功能
- **智能过滤系统**：支持金额阈值、销售人员、客户、日期范围、订单状态多维度过滤
- **金额区间分析**：新增报价单金额区间过滤（≤1000、1000-5000、5000-10000、≥10000、全部金额）
- **数据转换逻辑**：标准化的订单状态转换规则（订单、报价单、已取消、已发送报价单）
- **数据可视化增强**：Chart.js双Y轴图表，支持销售人员对比分析
- **销售业绩统计**：销售员和客户转化率分析，支持汇总行显示

#### 数据处理优化
- **Excel导入优化**：自动处理毛利率百分比转换，日期格式标准化
- **过滤器修复**：修复金额区间过滤器，使用报价单金额而非总计金额过滤
- **数据完整性**：实现严格的导入时序逻辑，确保过滤条件正确应用
- **临时文件管理**：自动清理过期临时文件，防止磁盘空间占用

#### 界面体验提升
- **完整多语言化**：系统名称更新为"OCCW报价与销售分析系统"，所有界面元素支持中英法三语言
- **用户界面优化**：移除区间转化率按钮，简化界面操作
- **交互响应改进**：修复销售人员过滤器同步问题，图表实时更新
- **数据显示修复**：解决客户订单分析表显示"未知客户"问题

#### Bug修复
- 修复金额转化率图表副Y轴显示为零的问题
- 修复导入过滤条件时序问题，确保过滤在数据生成前应用
- 修复销售人员过滤器不生效的问题
- 修复转换后数据页面"总计"列显示问题
- 修复多语言翻译缺失问题

#### 技术改进
- 优化后端数据处理性能
- 增强前端表格排序和搜索功能
- 改进AJAX请求错误处理
- 完善日志记录和调试信息

### 历史版本记录

| 版本 | 发布日期 | 主要更新 |
|------|---------|----------|
| v1.0.0 | 2024-01-01 | 初始版本发布 |
| v1.1.0 | 2024-02-01 | 新增多语言支持 |
| v1.2.0 | 2024-03-01 | 优化SKU映射功能 |
| v2.0.0 | 2024-07-27 | 重写SKU映射管理页面 |
| v2.5.0 | 2024-07-29 | 统一页面样式，简化系统功能 |
| v2.6.0 | 2024-07-29 | 修复PDF上传错误，重写SKU生成逻辑 |
| v2.7.0 | 2024-07-29 | 优化价格表导入后的自动刷新功能 |
| **v3.0.0** | **2024-08-03** | **销售分析系统重大升级** |

### 系统架构演进

**v3.0版本架构特点**：

1. **模块化设计**
   - 报价管理模块与销售分析模块分离
   - 独立的数据转换和过滤引擎
   - 可扩展的多语言支持框架

2. **数据驱动架构**
   - 基于临时文件的数据流管理
   - 实时数据转换和分析
   - 智能缓存机制

3. **用户体验优化**
   - 响应式设计适配各种设备
   - 直观的数据可视化界面
   - 完整的错误处理和用户反馈

4. **技术栈现代化**
   - Flask 2.3.3 + Pandas 2.1.4 后端
   - Bootstrap 5 + Chart.js 前端
   - 完整的REST API设计

---

**文档版本**: v3.0  
**最后更新**: 2024-08-03  
**维护者**: OCCW系统开发团队 