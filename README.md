# OCCW报价系统

一个基于Flask的报价单处理系统，支持PDF导入、手动创建报价单、SKU映射管理等功能。

## 功能特性

### 用户功能
- **PDF报价单导入**：自动解析PDF文件并提取产品信息
- **手动创建报价单**：手动添加产品信息创建报价单
- **报价单管理**：查看、编辑、删除个人报价单
- **多格式导出**：支持Excel、PDF格式导出
- **多语言支持**：中文、英文、法文界面
- **个人设置**：密码修改、语言偏好设置

### 管理员功能
- **系统管理**：查看所有用户的报价单
- **价格管理**：上传和管理OCCW价格表
- **SKU映射管理**：管理SKU映射规则
- **销售人员管理**：管理系统销售人员信息

## 技术栈

- **后端**：Flask 2.3.2
- **前端**：Bootstrap 5.1.3, jQuery 3.6.0
- **数据处理**：Pandas 1.5.3, OpenPyXL 3.1.2
- **PDF处理**：PyPDF2 3.0.1, ReportLab 4.0.4
- **部署**：Gunicorn 20.1.0

## 安装和运行

### 环境要求
- Python 3.8+
- pip

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd 2020-OCCW-convertor
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python app.py
```

或者使用生产环境：
```bash
gunicorn -c gunicorn.conf.py app:app
```

4. **访问系统**
打开浏览器访问：http://localhost:5000

## 项目结构

```
2020-OCCW-convertor/
├── app.py                 # 主应用文件
├── translations.py        # 多语言翻译文件
├── version.py            # 版本信息
├── requirements.txt      # 依赖包列表
├── gunicorn.conf.py      # Gunicorn配置
├── start.py              # 启动脚本
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 主页
│   ├── admin.html        # 管理员仪表板
│   ├── settings.html     # 用户设置
│   ├── help.html         # 帮助页面
│   └── ...              # 其他页面模板
├── data/                 # 数据文件
│   ├── users.json        # 用户数据
│   ├── quotations.json   # 报价单数据
│   ├── occw_prices.json  # OCCW价格数据
│   ├── sku_mappings.json # SKU映射数据
│   └── system_settings.json # 系统设置
├── upload/               # 上传文件目录
└── uploads/              # 临时上传目录
```

## 使用说明

### 普通用户
1. 注册/登录账户
2. 在主页选择功能：
   - PDF导入：上传PDF报价单文件
   - 手动创建：手动添加产品信息
   - 我的报价单：查看个人报价单
3. 在设定页面修改个人信息和语言偏好

### 管理员
1. 使用管理员密码登录
2. 在管理员仪表板管理：
   - 查看所有报价单
   - 管理价格表
   - 配置SKU映射
   - 管理销售人员

## 部署

### 本地部署
```bash
python app.py
```

### 生产环境部署
```bash
gunicorn -c gunicorn.conf.py app:app
```

### 云平台部署
项目包含以下部署配置文件：
- `render.yaml` - Render平台部署配置
- `railway.toml` - Railway平台部署配置
- `Procfile` - Heroku平台部署配置

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 支持

如有问题，请查看帮助页面或联系技术支持。 