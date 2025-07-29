#!/bin/bash

# Render构建脚本 - 分步骤安装依赖
echo "=== 开始构建 ==="

# 步骤1: 升级pip和安装基础工具
echo "步骤1: 升级pip和安装基础工具"
pip install --upgrade pip
pip install --upgrade setuptools wheel

# 步骤2: 验证setuptools安装
echo "步骤2: 验证setuptools安装"
python -c "import setuptools; print('setuptools版本:', setuptools.__version__)"

# 步骤3: 安装应用依赖
echo "步骤3: 安装应用依赖"
pip install --prefer-binary --no-cache-dir -r requirements-basic.txt

# 步骤4: 验证关键包安装
echo "步骤4: 验证关键包安装"
python -c "import flask, pandas, numpy; print('Flask版本:', flask.__version__); print('pandas版本:', pandas.__version__); print('numpy版本:', numpy.__version__)"

echo "=== 构建完成 ===" 