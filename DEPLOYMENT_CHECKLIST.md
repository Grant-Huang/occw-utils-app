# Render部署检查清单

## 🚀 部署前准备

### 1. 环境变量配置
确保在Render控制台中设置以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `FLASK_ENV` | `production` | Flask环境 |
| `SECRET_KEY` | `[自动生成]` | Flask密钥 |
| `ADMIN_PASSWORD` | `admin123` | 管理员密码 |
| `PYTHONPATH` | `.` | Python路径 |
| `WEB_CONCURRENCY` | `1` | 工作进程数 |

### 2. 文件检查
- ✅ `requirements.txt` - 依赖包列表
- ✅ `runtime.txt` - Python版本
- ✅ `render.yaml` - 部署配置
- ✅ `gunicorn.conf.py` - Gunicorn配置
- ✅ `start.py` - 启动脚本（备用）

### 3. 代码检查
- ✅ 移除所有调试代码
- ✅ 环境变量正确配置
- ✅ 文件路径使用相对路径
- ✅ 目录自动创建逻辑

### 4. 安全检查
- ✅ SECRET_KEY使用环境变量
- ✅ ADMIN_PASSWORD使用环境变量
- ✅ 调试模式仅在开发环境启用
- ✅ 文件上传大小限制

## 📋 部署步骤

### GitHub同步
```bash
git add .
git commit -m "v2.0: 配置化SKU规则系统"
git push origin main
```

### Render部署
1. 登录 [Render.com](https://render.com)
2. 选择 "New Web Service"
3. 连接GitHub仓库
4. 选择分支：`main`
5. 确认配置：
   - **Name**: `occw-quote-system`
   - **Environment**: `Python`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Build Command**: `pip install --upgrade pip setuptools wheel && pip install --prefer-binary --no-cache-dir -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`

### 备选构建方案
如果主requirements.txt构建失败，可尝试：

**方案A**: 修改构建命令使用保守版本
```bash
pip install --upgrade pip setuptools wheel && pip install --prefer-binary --no-cache-dir -r requirements-render.txt
```

**方案B**: 强制使用二进制包
```bash
pip install --upgrade pip setuptools wheel && pip install --only-binary=:all: --no-cache-dir -r requirements.txt
```

### 环境变量设置
在Render控制台的Environment Variables中添加上述变量。

## 🔧 故障排除

### 常见问题

1. **setuptools导入错误**：
   - 错误：`Cannot import 'setuptools.build_meta'`
   - 解决：在requirements.txt顶部添加 `setuptools>=65.0.0` 和 `wheel>=0.40.0`
   - 备选：在构建命令中先安装 `pip install setuptools wheel`

2. **pandas编译错误**：
   - 错误：`error: request for member 'real' in something not a structure or union`
   - 解决：使用 `--prefer-binary` 或 `--only-binary=:all:` 强制使用预编译包
   - 备选：降低pandas版本到 1.4.4, numpy到 1.23.5

3. **Python版本不匹配**：
   - 确保 `runtime.txt` 指定支持的Python版本 (3.11.9)
   - Render支持的版本列表：https://render.com/docs/python-version

4. **构建超时**：
   - 添加 `--no-cache-dir` 减少缓存开销
   - 使用更保守的包版本 (见 requirements-render.txt)

5. **启动失败**：检查`gunicorn.conf.py`配置
6. **文件权限**：确保目录创建逻辑正确
7. **内存不足**：减少工作进程数或升级套餐

### 日志查看
- Render控制台 > Logs
- 关注启动过程和错误信息

### 性能优化
- 免费套餐限制：512MB RAM, 1 CPU
- 工作进程设置为1
- 启用预加载应用

## �� 联系信息
如遇问题，请联系技术支持。 