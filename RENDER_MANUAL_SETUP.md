# Render手动部署指南

## 问题说明
Render可能没有正确读取`render.yaml`文件，需要手动配置服务。

## 手动配置步骤

### 1. 登录Render控制台
访问 [https://dashboard.render.com](https://dashboard.render.com)

### 2. 创建新服务
- 点击 "New +"
- 选择 "Web Service"
- 连接GitHub仓库：`Grant-Huang/2020-OCCW-convertor`

### 3. 配置服务
```
Name: occw-quote-system
Region: Oregon (US West)
Branch: main
Root Directory: (留空)
Runtime: Python 3
Build Command: pip install Flask==2.3.3
Start Command: python test-minimal.py
```

### 4. 环境变量
添加以下环境变量：
```
FLASK_ENV=production
SECRET_KEY=(自动生成)
ADMIN_PASSWORD=admin123
PYTHONPATH=.
WEB_CONCURRENCY=1
```

### 5. 高级设置
- **Auto-Deploy**: Yes
- **Health Check Path**: /health

## 验证部署

### 基础测试
1. 访问主页：`https://your-app.onrender.com`
2. 应该看到"部署成功"页面
3. 检查版本信息

### API测试
1. 访问：`https://your-app.onrender.com/api/status`
2. 应该返回JSON状态信息
3. 访问：`https://your-app.onrender.com/health`
4. 应该返回健康状态

## 逐步添加功能

### 第一步：基础Flask ✅
- 当前状态：只安装Flask
- 验证：基础Web服务正常

### 第二步：添加数据处理
修改Build Command为：
```bash
pip install Flask==2.3.3 pandas==2.0.3 numpy==1.24.3
```

### 第三步：添加PDF处理
修改Build Command为：
```bash
pip install Flask==2.3.3 pandas==2.0.3 numpy==1.24.3 PyPDF2==3.0.1
```

### 第四步：添加Excel处理
修改Build Command为：
```bash
pip install Flask==2.3.3 pandas==2.0.3 numpy==1.24.3 PyPDF2==3.0.1 openpyxl==3.1.2
```

### 第五步：完整应用
修改Build Command为：
```bash
pip install Flask==2.3.3 pandas==2.0.3 numpy==1.24.3 PyPDF2==3.0.1 openpyxl==3.1.2 reportlab==4.0.4 python-dotenv==1.0.0 gunicorn==21.2.0
```

修改Start Command为：
```bash
gunicorn --config gunicorn.conf.py app:app
```

## 故障排除

### 如果构建失败
1. 检查构建日志
2. 尝试更保守的版本
3. 逐个添加依赖包

### 如果启动失败
1. 检查Start Command
2. 验证文件路径
3. 检查环境变量

### 如果页面无法访问
1. 检查Health Check
2. 验证端口配置
3. 检查防火墙设置 