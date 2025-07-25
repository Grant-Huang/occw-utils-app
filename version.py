# -*- coding: utf-8 -*-
"""
版本信息配置
"""

VERSION = "1.1"
VERSION_NAME = "OCCW报价单转换系统 v1.1"
COMPANY_NAME_ZH = "加西欧派"
COMPANY_NAME_EN = "Oppein Cabinet Canada West Ltd."
SYSTEM_NAME_ZH = "OCCW报价单转换系统"
SYSTEM_NAME_EN = "OCCW Quote Conversion System"
SYSTEM_NAME_FR = "Système de Conversion de Devis OCCW"

# 版本历史
VERSION_HISTORY = {
    "1.1": {
        "date": "2025-01-25",
        "features": [
            "系统品牌重塑为OCCW报价单转换系统",
            "修复SKU映射页面加载性能问题",
            "增强PDF解析支持多行产品格式",
            "添加多语言支持（中文、英语、法语）",
            "优化用户权限管理",
            "改进部署配置和兼容性"
        ]
    },
    "1.0": {
        "date": "2024-12-01", 
        "features": [
            "初始版本发布",
            "PDF报价单解析功能",
            "SKU生成和映射功能",
            "OCCW价格表管理",
            "多格式导出功能"
        ]
    }
} 