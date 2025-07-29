# -*- coding: utf-8 -*-
"""
版本信息配置
"""

VERSION = "2.0"
VERSION_NAME = "OCCW报价系统 v2.0"
COMPANY_NAME_ZH = "加西欧派"
COMPANY_NAME_EN = "Oppein Cabinet Canada West Ltd."
SYSTEM_NAME_ZH = "OCCW报价系统"
SYSTEM_NAME_EN = "OCCW Quote System"
SYSTEM_NAME_FR = "Système de Devis OCCW"

# 版本历史
VERSION_HISTORY = {
    "2.0": {
        "date": "2025-01-26",
        "features": [
            "🆕 配置化SKU规则系统：可视化规则管理界面",
            "🔧 支持PDF解析、OCCW导入、手动创建三种场景的规则配置",
            "⚙️ 实时规则验证和JSON编辑器",
            "🔄 规则启用/禁用和恢复默认功能",
            "📁 配置文件导入/导出功能",
            "🚀 无需重新部署即可修改SKU生成规则",
            "✨ 开放式柜体SKU生成规则优化：避免重复-OPEN后缀"
        ],
        "changes": [
            "将硬编码的SKU规则迁移到配置文件",
            "新增 /rules 管理页面和相关API接口",
            "导航栏添加SKU规则配置入口",
            "完善条件评估和模板处理引擎"
        ]
    },
    "1.15": {
        "date": "2025-01-26",
        "features": [
            "系统名称更新为OCCW报价系统",
            "完善Excel价格表导入功能，支持新的5列格式",
            "修复产品名称混入变体信息问题",
            "新增价格表内容显示和管理功能",
            "重写映射关系表加载逻辑，提升稳定性",
            "支持门板变体2-3字符格式",
            "添加手动创建报价单功能",
            "优化错误处理和用户体验"
        ]
    },
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