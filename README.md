# 2020软件报价单转换系统

一个专门用于处理2020软件生成的报价单PDF文件的Web应用程序，能够自动解析PDF内容，生成标准化的报价单表格，并支持与OCCW价格体系的对接。

## 🌟 主要功能

### 普通用户功能（无需登录）
- ✅ **PDF解析**：自动解析2020软件生成的报价单PDF
- ✅ **智能识别**：自动提取产品信息、数量、价格和门板颜色
- ✅ **SKU生成**：根据规则自动生成OCCW SKU编码
- ✅ **价格对比**：显示2020价格与OCCW价格的对比
- ✅ **多格式导出**：支持Excel、CSV、PDF格式导出
- ✅ **实时计算**：自动计算总价并与原PDF核对

### 管理员功能（需要登录）
- 🔐 **价格管理**：上传和管理OCCW价格表
- 🔐 **配置管理**：自定义SKU生成规则
- 🔐 **映射管理**：管理SKU映射关系
- 🔐 **数据维护**：价格表的增删改查

## 🚀 快速开始

### 环境要求
- Python 3.7+
- Flask 2.3+
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/2020-OCCW-convertor.git
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

4. **访问系统**
打开浏览器访问：http://localhost:5000

## 📋 使用流程

### 普通用户使用
1. 直接访问主页
2. 上传2020软件生成的PDF报价单
3. 系统自动解析并生成报价表
4. 确认SKU映射关系
5. 导出所需格式的报价单

### 管理员使用
1. 点击"管理员"登录（默认密码：admin123）
2. 在"价格管理"上传OCCW价格表
3. 在"配置"页面调整SKU生成规则
4. 在"SKU映射"页面管理映射关系

## 🏗️ 系统架构

### 技术栈
- **后端**：Flask + Python
- **前端**：Bootstrap 5 + jQuery
- **PDF处理**：PyPDF2
- **数据处理**：pandas
- **文件导出**：openpyxl, reportlab

### 文件结构
```
2020-OCCW-convertor/
├── app.py                 # 主应用文件
├── requirements.txt       # 依赖包列表
├── templates/            # HTML模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 主页
│   ├── admin_login.html  # 管理员登录
│   ├── prices.html       # 价格管理
│   ├── config.html       # 配置页面
│   ├── sku_mappings.html # SKU映射管理
│   └── help.html         # 帮助文档
├── uploads/              # PDF上传目录
├── data/                 # 数据存储目录
└── static/               # 静态文件（如有）
```

## ⚙️ 配置说明

### SKU生成规则
系统根据产品描述自动生成SKU：

| 产品类型 | 判断条件 | SKU规则 | 示例 |
|---------|---------|---------|------|
| Cabinet | 包含"Cabinet" | `OCCW编码-PLY-花色` | `W3036-PLY-SSW` |
| Hardware | 包含"Hardware" | `HW-用户编码` | `HW-H123` |
| Accessory | 包含"Accessory" | `花色-用户编码` | `SSW-ACC001` |
| 其他 | 其他情况 | `花色-用户编码` | `SSW-MISC001` |

### 管理员配置
- 默认密码：`admin123`
- 可通过环境变量 `ADMIN_PASSWORD` 修改
- Session密钥：`your-secret-key-here`（生产环境请修改）

## 📊 数据格式

### OCCW价格表格式
Excel文件，包含两列：
- 第一列：SKU编码
- 第二列：单价（数字）

### PDF解析支持
- 2020软件标准报价单格式
- 支持多页PDF文档
- 自动识别产品列表和价格信息

## 🔧 部署说明

### 开发环境
```bash
python app.py
```
应用将在 http://localhost:5000 启动

### 生产环境
推荐使用 Gunicorn 部署：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker部署
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-24)
- ✨ 初始版本发布
- ✨ PDF解析和SKU生成功能
- ✨ 价格管理和映射功能
- ✨ 管理员权限控制
- ✨ 多格式导出支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持与反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 查看[帮助文档](http://localhost:5000/help)
2. 提交 [Issue](https://github.com/your-username/2020-OCCW-convertor/issues)
3. 发送邮件到：support@example.com

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！ 