#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复模板文件中剩余的硬编码中文文字
"""

import os
import re
from pathlib import Path

def fix_hardcoded_text():
    """修复模板文件中的硬编码中文文字"""
    
    # 模板文件路径
    templates_dir = Path("templates")
    
    # 需要修复的硬编码文字映射
    replacements = {
        # admin.html
        "<!-- 页面标题 -->": "<!-- Page Title -->",
        "<!-- 功能卡片 -->": "<!-- Function Cards -->",
        "<!-- 功能内容区域 -->": "<!-- Function Content Area -->",
        "<!-- 分页控件 -->": "<!-- Pagination Controls -->",
        "<!-- 分页按钮将在这里动态生成 -->": "<!-- Pagination buttons will be dynamically generated here -->",
        "<!-- 销售人员设置 -->": "<!-- Sales Person Settings -->",
        "<!-- 销售人员列表将在这里动态加载 -->": "<!-- Sales person list will be dynamically loaded here -->",
        "<!-- SKU映射 -->": "<!-- SKU Mappings -->",
        "<!-- SKU映射列表将在这里动态加载 -->": "<!-- SKU mappings list will be dynamically loaded here -->",
        "<!-- 系统设置 -->": "<!-- System Settings -->",
        "<!-- 价格管理 -->": "<!-- Price Management -->",
        "<!-- 文件上传区域 -->": "<!-- File Upload Area -->",
        "<!-- 价格表显示区域 -->": "<!-- Price Table Display Area -->",
        "<!-- 价格数据将在这里动态加载 -->": "<!-- Price data will be dynamically loaded here -->",
        
        # base.html (CSS注释)
        "/* 全局变量定义 */": "/* Global Variable Definitions */",
        "/* 全局样式重置 */": "/* Global Style Reset */",
        "/* 导航栏样式 */": "/* Navigation Bar Styles */",
        "/* 卡片样式 */": "/* Card Styles */",
        "/* 排序表头样式 */": "/* Sortable Header Styles */",
        "/* 按钮样式统一 */": "/* Unified Button Styles */",
        "/* 表单样式 */": "/* Form Styles */",
        "/* 页面标题样式 */": "/* Page Title Styles */",
        "/* 表格样式 */": "/* Table Styles */",
        "/* 分页样式 */": "/* Pagination Styles */",
        "/* 浮动信息条样式 */": "/* Floating Info Bar Styles */",
        "/* 徽章样式 */": "/* Badge Styles */",
        "/* 模态框样式 */": "/* Modal Styles */",
        "/* 进度条样式 */": "/* Progress Bar Styles */",
        "/* 自定义滚动条 */": "/* Custom Scrollbar */",
        "/* 响应式设计 */": "/* Responsive Design */",
        "/* 动画效果 */": "/* Animation Effects */",
        "/* 特殊元素样式 */": "/* Special Element Styles */",
        "/* Odoo风格组件颜色调整 */": "/* Odoo Style Component Color Adjustments */",
        
        # index.html
        "<!-- 功能卡片导航 -->": "<!-- Function Card Navigation -->",
        "<!-- APP内容区域 -->": "<!-- APP Content Area -->",
        "<!-- PDF导入APP -->": "<!-- PDF Import APP -->",
        "<!-- 我的[[ _(\"quotation_order\") ]]APP -->": "<!-- My [[ _(\"quotation_order\") ]] APP -->",
        "<!-- 分页按钮将在这里动态生成 -->": "<!-- Pagination buttons will be dynamically generated here -->",
        "<!-- 所有[[ _(\"quotation_order\") ]]APP（管理员专用） -->": "<!-- All [[ _(\"quotation_order\") ]] APP (Admin Only) -->",
        "<!-- 所有[[ _(\"quotation_order\") ]]列表将在这里动态加载 -->": "<!-- All [[ _(\"quotation_order\") ]] list will be dynamically loaded here -->",
        "<!-- 销售分析APP -->": "<!-- Sales Analysis APP -->",
        "<!-- 数据导入公共服务 -->": "<!-- Data Import Public Service -->",
        "<!-- 导航按钮 -->": "<!-- Navigation Buttons -->",
        "<!-- 第一部分：数据[[ t(\"summary\") ]] -->": "<!-- Part 1: Data [[ t(\"summary\") ]] -->",
        "<!-- 表格查询控制区域 -->": "<!-- Table Query Control Area -->",
        "<!-- 销售员业绩分析 -->": "<!-- Salesperson Performance Analysis -->",
        "<!-- 销售员数据将在这里动态加载 -->": "<!-- Salesperson data will be dynamically loaded here -->",
        
        # prices.html
        "<!-- 文件上传区域 -->": "<!-- File Upload Area -->",
        "<!-- 统计信息 -->": "<!-- Statistics Information -->",
        "<!-- 价格表统计 -->": "<!-- Price Table Statistics -->",
        "<!-- 加载中... -->": "<!-- Loading... -->",
        "<!-- 正在加载统计信息... -->": "<!-- Loading statistics... -->",
        "<!-- 价格表显示 -->": "<!-- Price Table Display -->",
        "<!-- 当前价格表 -->": "<!-- Current Price Table -->",
        "<!-- 刷新 -->": "<!-- Refresh -->",
        "<!-- 导出 -->": "<!-- Export -->",
        "<!-- 查询过滤 -->": "<!-- Query Filter -->",
        "<!-- 高级过滤 -->": "<!-- Advanced Filter -->",
        "<!-- 清空 -->": "<!-- Clear -->",
        "<!-- 准备显示价格表... -->": "<!-- Preparing to display price table... -->",
        "<!-- 高级过滤选项 -->": "<!-- Advanced Filter Options -->",
        "<!-- 门板变体 -->": "<!-- Door Panel Variant -->",
        "<!-- 全部 -->": "<!-- All -->",
        "<!-- 柜身变体 -->": "<!-- Cabinet Body Variant -->",
        "<!-- 产品类别 -->": "<!-- Product Category -->",
        "<!-- 应用过滤 -->": "<!-- Apply Filter -->",
        "<!-- 清空所有过滤 -->": "<!-- Clear All Filters -->",
        "<!-- 价格表内容 -->": "<!-- Price Table Content -->",
        
        # settings.html
        "<!-- 用户信息设置 -->": "<!-- User Information Settings -->",
        "// 用户信息表单提交处理": "// User information form submission handling",
        "// showAlert 函数已在 base.html 中统一实现为 toast 系统": "// showAlert function has been unified in base.html as toast system",
        
        # sku_mappings.html
        "SKU映射管理 - OCCW报价系统": "SKU Mapping Management - OCCW Quotation System",
        "<!-- 页面标题 -->": "<!-- Page Title -->",
        "<!-- 操作工具栏 -->": "<!-- Operation Toolbar -->",
        "<!-- 所有状态 -->": "<!-- All Status -->",
        "<!-- 有价格 -->": "<!-- Has Price -->",
        "<!-- 无价格 -->": "<!-- No Price -->",
        "<!-- 刷新 -->": "<!-- Refresh -->",
        "<!-- 新增映射 -->": "<!-- Add New Mapping -->",
        "<!-- 导出 -->": "<!-- Export -->",
        "<!-- 清空全部 -->": "<!-- Clear All -->",
        "<!-- 统计信息 -->": "<!-- Statistics Information -->",
        "<!-- 正在加载映射统计... -->": "<!-- Loading mapping statistics... -->",
        "<!-- SKU映射表 -->": "<!-- SKU Mapping Table -->",
        "<!-- 加载中... -->": "<!-- Loading... -->",
        "<!-- 正在加载SKU映射数据... -->": "<!-- Loading SKU mapping data... -->",
        "<!-- 原始SKU -->": "<!-- Original SKU -->",
        "<!-- 映射SKU -->": "<!-- Mapped SKU -->",
        "<!-- 价格 -->": "<!-- Price -->",
        "<!-- 状态 -->": "<!-- Status -->",
        "<!-- 操作 -->": "<!-- Actions -->",
        "<!-- 动态内容 -->": "<!-- Dynamic Content -->",
        "<!-- 分页 -->": "<!-- Pagination -->",
        "<!-- 动态分页 -->": "<!-- Dynamic Pagination -->",
        "<!-- 暂无SKU映射数据 -->": "<!-- No SKU mapping data available -->",
        "<!-- 映射关系会在上传PDF[[ _(\"quotation_order\") ]]后自动生成 -->": "<!-- Mapping relationships will be automatically generated after uploading PDF [[ _(\"quotation_order\") ]] -->",
        
        # quotation_detail.html
        "<!-- 报价单信息 -->": "<!-- Quotation Information -->",
        "<!-- 添加新产品区域 -->": "<!-- Add New Product Area -->",
        "<!-- 添加产品按钮 -->": "<!-- Add Product Button -->",
        "<!-- 按钮已移除 -->": "<!-- Button has been removed -->",
        "<!-- 动态添加的产品行将在这里显示 -->": "<!-- Dynamically added product rows will be displayed here -->",
        "<!-- 产品列表 -->": "<!-- Product List -->",
        "<!-- 导出信息 -->": "<!-- Export Information -->",
        "<!-- Toast提示容器 -->": "<!-- Toast Notification Container -->",
        "/* Toast提示系统样式 */": "/* Toast Notification System Styles */",
        "// Toast提示系统": "// Toast notification system",
        "// 点击关闭": "// Click to close",
        "// 15秒后自动关闭": "// Auto close after 15 seconds",
        "// 此函数已不再需要，保留以避免错误": "// This function is no longer needed, kept to avoid errors",
        "// 添加新产品": "// Add new product",
        "// 添加产品行到添加产品表格": "// Add product row to add product table",
        
        # user_login.html
        "// showAlert 函数已在 base.html 中统一实现为 toast 系统": "// showAlert function has been unified in base.html as toast system",
        
        # user_register.html
        "// showAlert 函数已在 base.html 中统一实现为 toast 系统": "// showAlert function has been unified in base.html as toast system",
        
        # imported_data.html
        "导入的销售数据": "Imported Sales Data",
        "<!-- 页面标题 -->": "<!-- Page Title -->",
        "<!-- 查看最近导入的[[ _(\"sales_order\") ]]数据 -->": "<!-- View recently imported [[ _(\"sales_order\") ]] data -->",
        "<!-- 关闭 -->": "<!-- Close -->",
        "<!-- 返回主页 -->": "<!-- Return to Home -->",
        "<!-- 当前应用的导入过滤条件 -->": "<!-- Currently applied import filter conditions -->",
        "<!-- 销售人员: -->": "<!-- Sales Person: -->",
        "<!-- 销售人员: -->": "<!-- Sales Person: -->",
        "<!-- 客户: -->": "<!-- Customer: -->",
        "<!-- 订单状态: -->": "<!-- Order Status: -->",
        "<!-- 显示的数据已根据上述过滤条件筛选。要修改过滤设定，请前往 -->": "<!-- The displayed data has been filtered according to the above filter conditions. To modify filter settings, please go to -->",
        "<!-- 管理员仪表板 → 订单导入过滤设置 -->": "<!-- Admin Dashboard → Order Import Filter Settings -->",
        "<!-- 数据统计信息 -->": "<!-- Data Statistics Information -->",
        
        # converted_data.html
        "转换后的销售数据": "Converted Sales Data",
        "<!-- 查看包含订单金额、[[ _(\"quotation_order\") ]]金额、转化率等字段的转换后数据 -->": "<!-- View converted data including order amount, [[ _(\"quotation_order\") ]] amount, conversion rate and other fields -->",
        "<!-- 查看原始数据 -->": "<!-- View Original Data -->",
        "<!-- 关闭 -->": "<!-- Close -->",
        "<!-- 返回主页 -->": "<!-- Return to Home -->",
        "<!-- 当前应用的导入过滤条件 -->": "<!-- Currently applied import filter conditions -->",
        "<!-- 销售人员: -->": "<!-- Sales Person: -->",
        "<!-- 客户: -->": "<!-- Customer: -->",
        "<!-- 订单状态: -->": "<!-- Order Status: -->",
        "<!-- 显示的数据已根据上述过滤条件筛选。要修改过滤设定，请前往 -->": "<!-- The displayed data has been filtered according to the above filter conditions. To modify filter settings, please go to -->",
        
        # 特殊处理：RTA Assm.组合件
        "RTA Assm.组合件": "RTA Assm. Assembly Component",
        
        # admin.html 新增的硬编码文字
        "价格表分页": "Price Table Pagination",
        "例如：1000": "e.g.: 1000",
        "例如：张三,李四,王五": "e.g.: Zhang San, Li Si, Wang Wu",
        "多个销售人员用逗号分隔，留空表示不过滤": "Multiple sales persons separated by commas, leave empty for no filter",
        "例如：客户A,客户B": "e.g.: Customer A, Customer B",
        "订单[[ t('status_filter') ]]": "Order [[ t('status_filter') ]]",
        "/* 管理员卡片样式 */": "/* Admin Card Styles */",
        "/* 功能卡片网格 */": "/* Function Card Grid */",
        "/* 管理员仪表板特殊样式 */": "/* Admin Dashboard Special Styles */",
        "/* 统计卡片样式 */": "/* Statistics Card Styles */",
        "/* 价格管理特殊样式 */": "/* Price Management Special Styles */",
        "/* 系统设置特殊样式 */": "/* System Settings Special Styles */",
        "/* 表单开关样式 */": "/* Form Switch Styles */",
        "/* 响应式调整 */": "/* Responsive Adjustments */",
        "// 翻译文本变量": "// Translation text variables",
        
        # admin.html JavaScript注释
        "// 页面初始化": "// Page initialization",
        "// 添加点击事件监听器": "// Add click event listeners",
        "// 根据data-action属性调用相应的函数": "// Call corresponding functions based on data-action attribute",
        "// 显示管理员仪表板": "// Show admin dashboard",
        "// 显示全部[[ _(\"quotation_order\") ]]": "// Show all [[ _(\"quotation_order\") ]]",
        "// 显示销售人员设置": "// Show sales person settings",
        "// 显示价格表管理": "// Show price table management",
        "// 从第一页开始加载，这会同时初始化过滤器": "// Load from first page, this will also initialize filters",
        "// 显示SKU映射": "// Show SKU mappings",
        "// 显示系统设置": "// Show system settings",
        "// 显示导入过滤设置": "// Show import filter settings",
        "// 保存系统设置": "// Save system settings",
        "// 更新系统状态显示": "// Update system status display",
        
        # converted_data.html 和 imported_data.html
        "查看包含订单金额、[[ _(\"quotation_order\") ]]金额、转化率等字段的转换后数据": "View converted data including order amount, [[ _(\"quotation_order\") ]] amount, conversion rate and other fields",
        "查看原始数据": "View Original Data",
        "关闭": "Close",
        "返回主页": "Return to Home",
        "当前应用的导入过滤条件": "Currently applied import filter conditions",
        "销售人员:": "Sales Person:",
        "客户:": "Customer:",
        "订单状态:": "Order Status:",
        "显示的数据已根据上述过滤条件筛选。要修改过滤设定，请前往": "The displayed data has been filtered according to the above filter conditions. To modify filter settings, please go to",
        "管理员仪表板 → 订单导入过滤设置": "Admin Dashboard → Order Import Filter Settings",
        "数据概览": "Data Overview",
        "总记录数": "Total Records",
        
        # quotation_detail.html JavaScript注释
        "// 加载产品类别": "// Load product categories",
        "// 类型选择改变时的处理": "// Handle type selection change",
        "// 清空后续选择": "// Clear subsequent selections",
        "// 重置SKU和价格": "// Reset SKU and price",
        "// 禁用后续选择": "// Disable subsequent selections",
        "// 加载产品": "// Load products",
        "// 填充产品选择": "// Populate product selection",
        "// 填充柜身变体选择": "// Populate cabinet body variant selection",
        "// 填充门板变体选择": "// Populate door panel variant selection",
        "// 根据类别启用/禁用变体选择": "// Enable/disable variant selection based on category",
        "Assm.组合件": "Assm. Assembly Component",
        "// 加载产品失败": "// Failed to load products",
        "// 产品选择改变时的处理": "// Handle product selection change",
        "加载产品类别失败": "Failed to load product categories",
        "加载产品失败": "Failed to load products",
        
        # admin.html 更多JavaScript注释
        "// 加载全部[[ _(\"quotation_order\") ]]": "// Load all [[ _(\"quotation_order\") ]]",
        "// 全局变量存储所有[[ _(\"quotation_order\") ]]数据": "// Global variable to store all [[ _(\"quotation_order\") ]] data",
        "// Show all [[ _(\"quotation_order\") ]]列表": "// Show all [[ _(\"quotation_order\") ]] list",
        "// 转换数据格式为扁平化数组": "// Convert data format to flattened array",
        "// 初始化过滤器和显示": "// Initialize filters and display",
        "// 初始化过滤器": "// Initialize filters",
        "// 填充用户过滤器": "// Populate user filters",
        "// 过滤[[ _(\"quotation_order\") ]]": "// Filter [[ _(\"quotation_order\") ]]",
        "// [[ _(\"search\") ]]过滤": "// [[ _(\"search\") ]] filter",
        "// 用户过滤": "// User filter",
        "// 清除过滤器": "// Clear filters",
        "// 显示[[ _(\"quotation_order\") ]]表格": "// Show [[ _(\"quotation_order\") ]] table",
        "// 更新计数和分页": "// Update count and pagination",
        "// 查看[[ _(\"quotation_order\") ]]详情": "// View [[ _(\"quotation_order\") ]] details",
        "// 编辑[[ _(\"quotation_order\") ]]": "// Edit [[ _(\"quotation_order\") ]]",
        "// 直接打开[[ _(\"quotation_order\") ]]详情页面": "// Directly open [[ _(\"quotation_order\") ]] details page",
        "// 删除[[ _(\"quotation_order\") ]]": "// Delete [[ _(\"quotation_order\") ]]",
        "// 重新加载[[ _(\"quotation_order\") ]]列表": "// Reload [[ _(\"quotation_order\") ]] list",
        "// 显示分页": "// Show pagination",
        
        # admin.html 更多JavaScript注释
        "// 上一页": "// Previous page",
        "// 页码": "// Page number",
        "// 下一页": "// Next page",
        "// 切换页面": "// Switch page",
        "// 加载销售人员列表": "// Load sales person list",
        "// 显示销售人员列表": "// Show sales person list",
        "// 添加销售人员": "// Add sales person",
        "// 删除销售人员": "// Delete sales person",
        "// 加载SKU映射": "// Load SKU mappings",
        "// Show SKU mappings列表": "// Show SKU mappings list",
        "// 添加SKU映射": "// Add SKU mapping",
        "// 删除SKU映射": "// Delete SKU mapping",
        "// 清空所有SKU映射": "// Clear all SKU mappings",
        "// 导出SKU映射": "// Export SKU mappings",
        "// 导出[[ _(\"quotation_order\") ]]": "// Export [[ _(\"quotation_order\") ]]",
        "// 价格管理相关函数": "// Price management related functions",
        "// 价格上传表单提交处理": "// Price upload form submission handling",
        "// 管理员密码修改表单提交处理": "// Admin password change form submission handling",
        "// 验证输入": "// Validate input",
        
        # base.html CSS注释和JavaScript注释
        "/* [[ _(\"toast_system\") ]]样式 */": "/* [[ _(\"toast_system\") ]] Styles */",
        "/* 按钮颜色调整 */": "/* Button Color Adjustments */",
        "/* 表单元素颜色调整 */": "/* Form Element Color Adjustments */",
        "/* 表格颜色调整 */": "/* Table Color Adjustments */",
        "/* 卡片和面板颜色调整 */": "/* Card and Panel Color Adjustments */",
        "/* 导航和菜单颜色调整 */": "/* Navigation and Menu Color Adjustments */",
        "/* 进度条颜色调整 */": "/* Progress Bar Color Adjustments */",
        "/* 分页颜色调整 */": "/* Pagination Color Adjustments */",
        "/* 文本颜色调整 */": "/* Text Color Adjustments */",
        "中文": "Chinese",
        "<!-- 浮动信息条容器 -->": "<!-- Floating Info Bar Container -->",
        "// 显示动画": "// Show animation",
        "// 设置进度条": "// Set progress bar",
        "// 自动隐藏": "// Auto hide",
        "// 全局 toast 管理器": "// Global toast manager",
        "// 统一的 showAlert 函数（替换原有的）": "// Unified showAlert function (replaces the original)",
        "// 将 Bootstrap 的 alert 类型映射到 toast 类型": "// Map Bootstrap alert types to toast types",
        
        # admin.html 更多JavaScript注释
        "// 提交密码修改请求": "// Submit password change request",
        "// 清空表单": "// Clear form",
        "// 加载价格统计": "// Load price statistics",
        "// 显示价格统计": "// Show price statistics",
        "// 检查stats是否存在": "// Check if stats exists",
        "// 全局分页变量": "// Global pagination variables",
        "// 加载OCCW价格表": "// Load OCCW price table",
        "// 更新分页信息": "// Update pagination information",
        "// 显示OCCW价格表": "// Show OCCW price table",
        "// 更新分页信息显示": "// Update pagination information display",
        "// 更新分页控件": "// Update pagination controls",
        "// Previous page按钮": "// Previous page button",
        "// Page number按钮": "// Page number button",
        "// 第一页": "// First page",
        "// 中间页码": "// Middle page numbers",
        "// 最后一页": "// Last page",
        "// Next page按钮": "// Next page button",
        "// 改变每页显示数量": "// Change items per page",
        "// 重置到第一页": "// Reset to first page",
        "// 初始化价格过滤器": "// Initialize price filters",
        
        # admin.html 更多JavaScript注释
        "// Update pagination information显示": "// Update pagination information display",
        "// 如果prices为空，尝试从所有数据中获取过滤器选项": "// If prices is empty, try to get filter options from all data",
        "// 加载所有价格数据用于初始化过滤器": "// Load all price data for filter initialization",
        "// 获取所有数据": "// Get all data",
        "// 填充过滤器选项": "// Populate filter options",
        "// 过滤价格": "// Filter prices",
        "// 带过滤条件的加载价格表": "// Load price table with filter conditions",
        "// 清空价格过滤器": "// Clear price filters",
        "// 导入过滤设置相关函数": "// Import filter settings related functions",
        "// 加载当前过滤设置": "// Load current filter settings",
        "// 如果加载失败，设置默认值": "// If loading fails, set default values",
        
        # base.html JavaScript注释
        "// 兼容原有的 showFloatingNotification 函数": "// Compatible with the original showFloatingNotification function",
        "// 语言切换函数": "// Language switching function",
        "// 页面加载完成后处理 flash 消息": "// Handle flash messages after page load",
        "// 检查是否有 flash 消息需要显示": "// Check if there are flash messages to display",
        
        # admin.html 更多JavaScript注释
        "// 填充过滤表单": "// Populate filter form",
        "// 设置订单状态复选框": "// Set order status checkboxes",
        "// 重置所有复选框": "// Reset all checkboxes",
        "// 设置选中的状态": "// Set selected status",
        "// 设置默认过滤设置": "// Set default filter settings",
        "// 默认选中常用状态": "// Default select common status",
        "$('#status_已取消').prop('checked', false);": "$('#status_cancelled').prop('checked', false);",
        "// 重置过滤设置": "// Reset filter settings",
        "// 导入过滤表单提交处理": "// Import filter form submission handling",
        "// 收集表单数据": "// Collect form data",
        "// 验证日期": "// Validate date",
        "// 保存过滤设置": "// Save filter settings",
        "// 获取选中的订单状态": "// Get selected order status",
        
        # sku_mappings.html 剩余的硬编码文字
        "原始SKU或映射SKU...": "Original SKU or Mapped SKU...",
        "所有状态": "All Status",
        "有价格": "Has Price",
        "无价格": "No Price",
        "刷新": "Refresh",
        "新增映射": "Add New Mapping",
        "导出": "Export",
        "清空全部": "Clear All",
        "正在加载映射统计...": "Loading mapping statistics...",
        "加载中...": "Loading...",
        "正在加载SKU映射数据...": "Loading SKU mapping data...",
        "原始SKU": "Original SKU",
        "映射SKU": "Mapped SKU",
        "价格": "Price",
        "状态": "Status",
        "操作": "Actions",
        "暂无SKU映射数据": "No SKU mapping data available",
        "映射关系会在上传PDF[[ _(\"quotation_order\") ]]后自动生成": "Mapping relationships will be automatically generated after uploading PDF [[ _(\"quotation_order\") ]]",
        "去上传[[ _(\"quotation_order\") ]]": "Go to upload [[ _(\"quotation_order\") ]]",
        "<!-- 编辑映射模态框 -->": "<!-- Edit Mapping Modal -->",
        "编辑SKU映射": "Edit SKU Mapping",
        "输入原始SKU": "Enter original SKU",
        "来自PDF[[ _(\"quotation_order\") ]]的SKU": "SKU from PDF [[ _(\"quotation_order\") ]]",
        
        # converted_data.html 剩余的硬编码文字
        "[[ _(\"sales_order\") ]]数": "[[ _(\"sales_order\") ]] Count",
        "[[ _(\"quotation_order\") ]]数": "[[ _(\"quotation_order\") ]] Count",
        "整体转化率": "Overall Conversion Rate",
        "订单金额": "Order Amount",
        
        # converted_data.html 更多硬编码文字
        "订单数量": "Order Quantity",
        "[[ _(\"quotation_order\") ]] Count量": "[[ _(\"quotation_order\") ]] Count",
        "<!-- 数据将通过JavaScript填充 -->": "<!-- Data will be populated via JavaScript -->",
        "每页显示:": "Items per page:",
        "<!-- 无数据[[ _(\"tip\") ]] -->": "<!-- No data [[ _(\"tip\") ]] -->",
        "暂无数据，请先导入销售数据。": "No data available, please import sales data first.",
        "// 初始化": "// Initialize",
        "// 填充Sales Person过滤器": "// Populate Sales Person filter",
        "// 填充订单[[ _(\"status_filter\") ]]器 - 从转换后数据动态获取": "// Populate order [[ _(\"status_filter\") ]] filter - dynamically get from converted data",
        "// 只有在有数据且表格存在时才显示数据": "// Only show data when data exists and table exists",
        "// Sales Person过滤": "// Sales Person filter",
        "// 排序功能": "// Sorting functionality",
        "// 更新排序图标": "// Update sort icons",
        "// 排序数据": "// Sort data",
        "// 处理不同数据类型": "// Handle different data types",
        
        # converted_data.html 更多硬编码文字
        "毛利率（%）": "Gross Profit Margin (%)",
        "// 显示数据": "// Show data",
        "// 更新记录计数": "// Update record count",
        "// 更新分页": "// Update pagination",
        "// 更新页面信息": "// Update page information",
        "// 更新分页按钮": "// Update pagination buttons",
        "// Export到Excel": "// Export to Excel",
        "// 创建并下载文件": "// Create and download file",
        "转换后销售数据_": "Converted Sales Data_",
        
        # imported_data.html 剩余的硬编码文字
        "[[ _(\"sales_order\") ]] Count据": "[[ _(\"sales_order\") ]] Data",
        "Sales Person数": "Sales Person Count",
        "无数据": "No Data",
        "销售数据详情": "Sales Data Details",
        "总计": "Total",
        "毛利率（%）": "Gross Profit Margin (%)",
        "其他信息": "Other Information",
        "详情": "Details",
        "每页显示：": "Items per page:",
        "<!-- 记录详情模态框 -->": "<!-- Record Details Modal -->",
        
        # converted_data.html 更多硬编码文字
        "// Update pagination按钮": "// Update pagination buttons",
        
        # imported_data.html 更多硬编码文字
        "查看最近导入的[[ _(\"sales_order\") ]] Data": "View recently imported [[ _(\"sales_order\") ]] Data",
        "至": "to",
        "<!-- 记录Details模态框 -->": "<!-- Record Details Modal -->",
        "记录Details": "Record Details",
        "<!-- Details内容将在这里动态加载 -->": "<!-- Details content will be dynamically loaded here -->",
        "// 检查日期是否有效": "// Check if date is valid",
        "// 确保日期对象有效": "// Ensure date object is valid",
        "// 无效日期，根据需要决定是否匹配": "// Invalid date, decide whether to match based on requirements",
        "// 没有日期数据，根据需要决定是否匹配": "// No date data, decide whether to match based on requirements",
        "// 如果表格不存在（比如显示错误页面时），直接返回": "// If table doesn't exist (e.g., when showing error page), return directly",
        "// 不需要分页": "// No pagination needed",
        "// 改变页面": "// Change page"
    }
    
    # 遍历所有模板文件
    for template_file in templates_dir.glob("*.html"):
        if template_file.name == "help.html":
            continue
            
        print(f"处理文件: {template_file}")
        
        # 读取文件内容
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应用替换
        original_content = content
        for old_text, new_text in replacements.items():
            content = content.replace(old_text, new_text)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ 已修复 {template_file}")
        else:
            print(f"  - 无需修复 {template_file}")
    
    print("\n硬编码文字修复完成！")

if __name__ == "__main__":
    fix_hardcoded_text()
