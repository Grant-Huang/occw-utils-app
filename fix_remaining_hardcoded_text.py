#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复剩余的硬编码文字，特别是showAlert消息和其他遗漏的内容
"""

import os
import re

def escape_po_string(text):
    """转义.po文件中的字符串"""
    if not isinstance(text, str):
        text = str(text)
    # 转义双引号和反斜杠
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    return text

def update_translation_files(new_keys):
    """更新翻译文件"""
    # 读取现有的翻译文件
    translation_files = {
        'zh': 'translations/zh/LC_MESSAGES/messages.po',
        'en': 'translations/en/LC_MESSAGES/messages.po',
        'fr': 'translations/fr/LC_MESSAGES/messages.po'
    }
    
    # 中文翻译映射
    zh_translations = {
        # showAlert消息
        'upload_failed_retry': '上传失败，请重试',
        'get_pdf_text_failed': '获取PDF文本失败',
        'copy_failed_manual': '复制失败，请手动选择文本复制',
        'save_sku_mapping_failed': '保存SKU映射失败',
        'load_product_category_failed': '加载产品类别失败',
        'load_product_failed': '加载产品失败',
        'load_variant_failed': '加载变体失败',
        'get_data_failed': '获取数据失败',
        'chart_download_success': '图表下载成功',
        'import_failed_with_errors': '导入失败：发现 {count} 个错误，请查看详情',
        'import_failed': '导入失败',
        'load_price_table_failed': '加载价格表失败',
        'load_mapping_data_failed': '加载映射数据失败',
        'unknown_error': '未知错误',
        'sku_mapping_save_success': 'SKU映射保存成功',
        'save_failed': '保存失败',
        'sku_mapping_delete_success': 'SKU映射删除成功',
        'delete_failed': '删除失败',
        'clear_failed': '清空失败',
        'export_sku_mapping_success': '成功导出 {count} 个SKU映射关系',
        'export_failed': '导出失败',
        'export_sku_mapping_failed': '导出SKU映射失败',
        'filter_settings_save_success': '过滤设置保存成功',
        'save_filter_settings_failed': '保存过滤设置失败',
        'start_date_after_end_date': '开始日期不能晚于结束日期',
        
        # 其他硬编码文字
        'total': '总计',
        'average': '平均',
        'maximum': '最大值',
        'minimum': '最小值',
        'quantity': '数量',
        'amount': '金额',
        'order': '订单',
        'quotation': '报价',
        'customer': '客户',
        'sales_person': '销售员',
        'product': '产品',
        'category': '类别',
        'status': '状态',
        'date': '日期',
        'time': '时间',
        'remark': '备注',
        'description': '说明',
        'tip': '提示',
        'warning': '警告',
        'error': '错误',
        'success': '成功',
        'failed': '失败',
        'all_quotations': '全部报价单',
        'quotation_table': '报价单表格',
        'quotation_data_will_load_here': '报价单数据将在这里动态加载',
        'import_description': '导入说明',
        'sales_order_import_filter_settings': '销售订单导入过滤设置',
        'filter_settings_description': '过滤设置说明',
        'filter_settings_help': '这些设置将在销售订单数据导入时自动应用，过滤掉不符合条件的数据。所有过滤条件为可选，留空表示不限制该条件。',
        'amount_filter': '金额过滤',
        'min_import_amount_threshold': '最小导入金额阈值',
        'min_amount_help': '只导入总计金额大于等于此值的数据',
        'date_filter': '日期过滤',
        'start_date': '开始日期',
        'start_date_help': '只导入此日期之后的数据',
        'end_date': '结束日期',
        'end_date_help': '只导入此日期之前的数据',
        'person_customer_filter': '人员和客户过滤',
        'customer_filter': '客户过滤',
        'customer_filter_help': '多个客户用逗号分隔，留空表示不过滤',
        'status_filter': '状态过滤',
        'order_status_filter': '订单状态过滤',
        'sales_order': '销售订单',
        'quotation_order': '报价单',
        'sent_quotation': '已发送报价单',
        'status_filter_help': '选择要导入的订单状态类型',
        'permission_description': '权限说明',
        'toast_system': 'Toast 提示系统',
        'toast_system_styles': 'Toast 提示系统样式',
        'warning_box_styles': '警告框样式',
        'tooltip_styles': '工具提示样式',
        'warning_tip_color_adjustment': '警告和提示颜色调整',
        'toast_container': 'Toast 提示容器',
        'view_recent_imported_sales_data': '查看最近导入的销售订单数据',
        'error_message': '错误消息',
        'current_filter_settings_tip': '当前过滤设定提示',
        'min_amount_threshold': '最小金额阈值',
        'customer_count': '客户数',
        'date_range': '日期范围',
        'order_date': '订单日期'
    }
    
    # 英文翻译映射
    en_translations = {
        # showAlert消息
        'upload_failed_retry': 'Upload failed, please try again',
        'get_pdf_text_failed': 'Failed to get PDF text',
        'copy_failed_manual': 'Copy failed, please select text manually',
        'save_sku_mapping_failed': 'Failed to save SKU mapping',
        'load_product_category_failed': 'Failed to load product category',
        'load_product_failed': 'Failed to load product',
        'load_variant_failed': 'Failed to load variant',
        'get_data_failed': 'Failed to get data',
        'chart_download_success': 'Chart download successful',
        'import_failed_with_errors': 'Import failed: found {count} errors, please check details',
        'import_failed': 'Import failed',
        'load_price_table_failed': 'Failed to load price table',
        'load_mapping_data_failed': 'Failed to load mapping data',
        'unknown_error': 'Unknown error',
        'sku_mapping_save_success': 'SKU mapping saved successfully',
        'save_failed': 'Save failed',
        'sku_mapping_delete_success': 'SKU mapping deleted successfully',
        'delete_failed': 'Delete failed',
        'clear_failed': 'Clear failed',
        'export_sku_mapping_success': 'Successfully exported {count} SKU mappings',
        'export_failed': 'Export failed',
        'export_sku_mapping_failed': 'Failed to export SKU mapping',
        'filter_settings_save_success': 'Filter settings saved successfully',
        'save_filter_settings_failed': 'Failed to save filter settings',
        'start_date_after_end_date': 'Start date cannot be later than end date',
        
        # 其他硬编码文字
        'total': 'Total',
        'average': 'Average',
        'maximum': 'Maximum',
        'minimum': 'Minimum',
        'quantity': 'Quantity',
        'amount': 'Amount',
        'order': 'Order',
        'quotation': 'Quotation',
        'customer': 'Customer',
        'sales_person': 'Sales Person',
        'product': 'Product',
        'category': 'Category',
        'status': 'Status',
        'date': 'Date',
        'time': 'Time',
        'remark': 'Remark',
        'description': 'Description',
        'tip': 'Tip',
        'warning': 'Warning',
        'error': 'Error',
        'success': 'Success',
        'failed': 'Failed',
        'all_quotations': 'All Quotations',
        'quotation_table': 'Quotation Table',
        'quotation_data_will_load_here': 'Quotation data will load here dynamically',
        'import_description': 'Import Description',
        'sales_order_import_filter_settings': 'Sales Order Import Filter Settings',
        'filter_settings_description': 'Filter Settings Description',
        'filter_settings_help': 'These settings will be automatically applied when importing sales order data, filtering out data that does not meet the conditions. All filter conditions are optional, leaving blank means no restriction on that condition.',
        'amount_filter': 'Amount Filter',
        'min_import_amount_threshold': 'Minimum Import Amount Threshold',
        'min_amount_help': 'Only import data with total amount greater than or equal to this value',
        'date_filter': 'Date Filter',
        'start_date': 'Start Date',
        'start_date_help': 'Only import data after this date',
        'end_date': 'End Date',
        'end_date_help': 'Only import data before this date',
        'person_customer_filter': 'Person and Customer Filter',
        'customer_filter': 'Customer Filter',
        'customer_filter_help': 'Multiple customers separated by commas, leave blank for no filter',
        'status_filter': 'Status Filter',
        'order_status_filter': 'Order Status Filter',
        'sales_order': 'Sales Order',
        'quotation_order': 'Quotation',
        'sent_quotation': 'Sent Quotation',
        'status_filter_help': 'Select the order status types to import',
        'permission_description': 'Permission Description',
        'toast_system': 'Toast System',
        'toast_system_styles': 'Toast System Styles',
        'warning_box_styles': 'Warning Box Styles',
        'tooltip_styles': 'Tooltip Styles',
        'warning_tip_color_adjustment': 'Warning and Tip Color Adjustment',
        'toast_container': 'Toast Container',
        'view_recent_imported_sales_data': 'View Recently Imported Sales Data',
        'error_message': 'Error Message',
        'current_filter_settings_tip': 'Current Filter Settings Tip',
        'min_amount_threshold': 'Minimum Amount Threshold',
        'customer_count': 'Customer Count',
        'date_range': 'Date Range',
        'order_date': 'Order Date'
    }
    
    # 法文翻译映射
    fr_translations = {
        # showAlert消息
        'upload_failed_retry': 'Échec du téléchargement, veuillez réessayer',
        'get_pdf_text_failed': 'Échec de l\'obtention du texte PDF',
        'copy_failed_manual': 'Échec de la copie, veuillez sélectionner le texte manuellement',
        'save_sku_mapping_failed': 'Échec de la sauvegarde du mapping SKU',
        'load_product_category_failed': 'Échec du chargement de la catégorie de produit',
        'load_product_failed': 'Échec du chargement du produit',
        'load_variant_failed': 'Échec du chargement de la variante',
        'get_data_failed': 'Échec de l\'obtention des données',
        'chart_download_success': 'Téléchargement du graphique réussi',
        'import_failed_with_errors': 'Échec de l\'importation : {count} erreurs trouvées, veuillez vérifier les détails',
        'import_failed': 'Échec de l\'importation',
        'load_price_table_failed': 'Échec du chargement de la table des prix',
        'load_mapping_data_failed': 'Échec du chargement des données de mapping',
        'unknown_error': 'Erreur inconnue',
        'sku_mapping_save_success': 'Mapping SKU sauvegardé avec succès',
        'save_failed': 'Échec de la sauvegarde',
        'sku_mapping_delete_success': 'Mapping SKU supprimé avec succès',
        'delete_failed': 'Échec de la suppression',
        'clear_failed': 'Échec de l\'effacement',
        'export_sku_mapping_success': 'Exportation réussie de {count} mappings SKU',
        'export_failed': 'Échec de l\'exportation',
        'export_sku_mapping_failed': 'Échec de l\'exportation du mapping SKU',
        'filter_settings_save_success': 'Paramètres de filtre sauvegardés avec succès',
        'save_filter_settings_failed': 'Échec de la sauvegarde des paramètres de filtre',
        'start_date_after_end_date': 'La date de début ne peut pas être postérieure à la date de fin',
        
        # 其他硬编码文字
        'total': 'Total',
        'average': 'Moyenne',
        'maximum': 'Maximum',
        'minimum': 'Minimum',
        'quantity': 'Quantité',
        'amount': 'Montant',
        'order': 'Commande',
        'quotation': 'Devis',
        'customer': 'Client',
        'sales_person': 'Vendeur',
        'product': 'Produit',
        'category': 'Catégorie',
        'status': 'Statut',
        'date': 'Date',
        'time': 'Heure',
        'remark': 'Remarque',
        'description': 'Description',
        'tip': 'Conseil',
        'warning': 'Avertissement',
        'error': 'Erreur',
        'success': 'Succès',
        'failed': 'Échec',
        'all_quotations': 'Tous les devis',
        'quotation_table': 'Tableau des devis',
        'quotation_data_will_load_here': 'Les données de devis se chargeront ici dynamiquement',
        'import_description': 'Description de l\'importation',
        'sales_order_import_filter_settings': 'Paramètres de filtre d\'importation des commandes',
        'filter_settings_description': 'Description des paramètres de filtre',
        'filter_settings_help': 'Ces paramètres seront automatiquement appliqués lors de l\'importation des données de commande, filtrant les données qui ne répondent pas aux conditions. Toutes les conditions de filtre sont optionnelles, laisser vide signifie aucune restriction sur cette condition.',
        'amount_filter': 'Filtre de montant',
        'min_import_amount_threshold': 'Seuil de montant minimum d\'importation',
        'min_amount_help': 'Importer uniquement les données avec un montant total supérieur ou égal à cette valeur',
        'date_filter': 'Filtre de date',
        'start_date': 'Date de début',
        'start_date_help': 'Importer uniquement les données après cette date',
        'end_date': 'Date de fin',
        'end_date_help': 'Importer uniquement les données avant cette date',
        'person_customer_filter': 'Filtre de personne et client',
        'customer_filter': 'Filtre de client',
        'customer_filter_help': 'Plusieurs clients séparés par des virgules, laisser vide pour aucun filtre',
        'status_filter': 'Filtre de statut',
        'order_status_filter': 'Filtre de statut de commande',
        'sales_order': 'Commande de vente',
        'quotation_order': 'Devis',
        'sent_quotation': 'Devis envoyé',
        'status_filter_help': 'Sélectionner les types de statut de commande à importer',
        'permission_description': 'Description des permissions',
        'toast_system': 'Système de toast',
        'toast_system_styles': 'Styles du système de toast',
        'warning_box_styles': 'Styles de boîte d\'avertissement',
        'tooltip_styles': 'Styles de tooltip',
        'warning_tip_color_adjustment': 'Ajustement des couleurs d\'avertissement et de conseil',
        'toast_container': 'Conteneur de toast',
        'view_recent_imported_sales_data': 'Voir les données de vente récemment importées',
        'error_message': 'Message d\'erreur',
        'current_filter_settings_tip': 'Conseil sur les paramètres de filtre actuels',
        'min_amount_threshold': 'Seuil de montant minimum',
        'customer_count': 'Nombre de clients',
        'date_range': 'Plage de dates',
        'order_date': 'Date de commande'
    }
    
    for lang, file_path in translation_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加新的翻译条目
            for key in new_keys:
                if key not in content:
                    if lang == 'zh':
                        translation = zh_translations.get(key, f'TODO: {key}')
                    elif lang == 'en':
                        translation = en_translations.get(key, f'TODO: {key}')
                    elif lang == 'fr':
                        translation = fr_translations.get(key, f'TODO: {key}')
                    
                    # 在文件末尾添加新的翻译条目
                    content += f'\nmsgid "{escape_po_string(key)}"\n'
                    content += f'msgstr "{escape_po_string(translation)}"\n'
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"已更新 {lang} 翻译文件: {file_path}")

def fix_remaining_hardcoded_text():
    """修复剩余的硬编码文字"""
    html_files = [
        'templates/index.html',
        'templates/admin.html',
        'templates/converted_data.html',
        'templates/imported_data.html',
        'templates/prices.html',
        'templates/sku_mappings.html',
        'templates/admin_login.html',
        'templates/base.html'
    ]
    
    # 定义替换规则
    replacements = [
        # showAlert消息
        (r'showAlert\(\'上传失败，请重试\', \'danger\'\);', 'showAlert(\'{{ _("upload_failed_retry") }}\', \'danger\');'),
        (r'showAlert\(\'获取PDF文本失败\', \'danger\'\);', 'showAlert(\'{{ _("get_pdf_text_failed") }}\', \'danger\');'),
        (r'showAlert\(\'复制失败，请手动选择文本复制\', \'warning\'\);', 'showAlert(\'{{ _("copy_failed_manual") }}\', \'warning\');'),
        (r'showAlert\(\'保存SKU映射失败\', \'danger\'\);', 'showAlert(\'{{ _("save_sku_mapping_failed") }}\', \'danger\');'),
        (r'showAlert\(\'加载产品类别失败\', \'warning\'\);', 'showAlert(\'{{ _("load_product_category_failed") }}\', \'warning\');'),
        (r'showAlert\(\'加载产品失败\', \'warning\'\);', 'showAlert(\'{{ _("load_product_failed") }}\', \'warning\');'),
        (r'showAlert\(\'加载变体失败\', \'warning\'\);', 'showAlert(\'{{ _("load_variant_failed") }}\', \'warning\');'),
        (r'showAlert\(\'获取数据失败\', \'danger\'\);', 'showAlert(\'{{ _("get_data_failed") }}\', \'danger\');'),
        (r'showAlert\(\'图表下载成功\', \'success\'\);', 'showAlert(\'{{ _("chart_download_success") }}\', \'success\');'),
        (r'showAlert\(\`导入失败：发现 \$\{response\.error_details\.length\} 个错误，请查看详情\`, \'danger\'\);', 'showAlert(\'{{ _("import_failed_with_errors").format(count="${response.error_details.length}") }}\', \'danger\');'),
        (r'showAlert\(\'导入失败\', \'danger\'\);', 'showAlert(\'{{ _("import_failed") }}\', \'danger\');'),
        (r'showAlert\(\'加载价格表失败\', \'danger\'\);', 'showAlert(\'{{ _("load_price_table_failed") }}\', \'danger\');'),
        (r'showAlert\(\'加载映射数据失败: \' \+ \(response\.error \|\| \'未知错误\'\), \'danger\'\);', 'showAlert(\'{{ _("load_mapping_data_failed") }}: \' + (response.error || \'{{ _("unknown_error") }}\'), \'danger\');'),
        (r'showAlert\(\'加载映射数据失败\', \'danger\'\);', 'showAlert(\'{{ _("load_mapping_data_failed") }}\', \'danger\');'),
        (r'showAlert\(\'SKU映射保存成功\', \'success\'\);', 'showAlert(\'{{ _("sku_mapping_save_success") }}\', \'success\');'),
        (r'showAlert\(response\.error \|\| \'保存失败\', \'danger\'\);', 'showAlert(response.error || \'{{ _("save_failed") }}\', \'danger\');'),
        (r'showAlert\(\'保存SKU映射失败\', \'danger\'\);', 'showAlert(\'{{ _("save_sku_mapping_failed") }}\', \'danger\');'),
        (r'showAlert\(\'SKU映射删除成功\', \'success\'\);', 'showAlert(\'{{ _("sku_mapping_delete_success") }}\', \'success\');'),
        (r'showAlert\(response\.error \|\| \'删除失败\', \'danger\'\);', 'showAlert(response.error || \'{{ _("delete_failed") }}\', \'danger\');'),
        (r'showAlert\(\'删除SKU映射失败\', \'danger\'\);', 'showAlert(\'{{ _("delete_sku_mapping_failed") }}\', \'danger\');'),
        (r'showAlert\(response\.error \|\| \'清空失败\', \'danger\'\);', 'showAlert(response.error || \'{{ _("clear_failed") }}\', \'danger\');'),
        (r'showAlert\(\'清空SKU映射失败\', \'danger\'\);', 'showAlert(\'{{ _("clear_sku_mapping_failed") }}\', \'danger\');'),
        (r'showAlert\(\`成功导出 \$\{response\.count\} 个SKU映射关系\`, \'success\'\);', 'showAlert(\'{{ _("export_sku_mapping_success").format(count="${response.count}") }}\', \'success\');'),
        (r'showAlert\(response\.error \|\| \'导出失败\', \'danger\'\);', 'showAlert(response.error || \'{{ _("export_failed") }}\', \'danger\');'),
        (r'showAlert\(\'导出SKU映射失败\', \'danger\'\);', 'showAlert(\'{{ _("export_sku_mapping_failed") }}\', \'danger\');'),
        (r'showAlert\(\'过滤设置保存成功\', \'success\'\);', 'showAlert(\'{{ _("filter_settings_save_success") }}\', \'success\');'),
        (r'showAlert\(\'保存过滤设置失败\', \'danger\'\);', 'showAlert(\'{{ _("save_filter_settings_failed") }}\', \'danger\');'),
        (r'showAlert\(\'开始日期不能晚于结束日期\', \'warning\'\);', 'showAlert(\'{{ _("start_date_after_end_date") }}\', \'warning\');'),
        
        # 其他硬编码文字
        (r'<!-- 全部报价单 -->', '<!-- {{ _("all_quotations") }} -->'),
        (r'<!-- 报价单表格 -->', '<!-- {{ _("quotation_table") }} -->'),
        (r'<!-- 报价单数据将在这里动态加载 -->', '<!-- {{ _("quotation_data_will_load_here") }} -->'),
        (r'<!-- 导入说明 -->', '<!-- {{ _("import_description") }} -->'),
        (r'<!-- 销售订单导入过滤设置 -->', '<!-- {{ _("sales_order_import_filter_settings") }} -->'),
        (r'过滤设置说明', '{{ _("filter_settings_description") }}'),
        (r'这些设置将在销售订单数据导入时自动应用，过滤掉不符合条件的数据。所有过滤条件为可选，留空表示不限制该条件。', '{{ _("filter_settings_help") }}'),
        (r'金额过滤', '{{ _("amount_filter") }}'),
        (r'最小导入金额阈值', '{{ _("min_import_amount_threshold") }}'),
        (r'只导入总计金额大于等于此值的数据', '{{ _("min_amount_help") }}'),
        (r'日期过滤', '{{ _("date_filter") }}'),
        (r'开始日期', '{{ _("start_date") }}'),
        (r'只导入此日期之后的数据', '{{ _("start_date_help") }}'),
        (r'结束日期', '{{ _("end_date") }}'),
        (r'只导入此日期之前的数据', '{{ _("end_date_help") }}'),
        (r'人员和客户过滤', '{{ _("person_customer_filter") }}'),
        (r'客户过滤', '{{ _("customer_filter") }}'),
        (r'多个客户用逗号分隔，留空表示不过滤', '{{ _("customer_filter_help") }}'),
        (r'状态过滤', '{{ _("status_filter") }}'),
        (r'订单状态过滤', '{{ _("order_status_filter") }}'),
        (r'销售订单', '{{ _("sales_order") }}'),
        (r'报价单', '{{ _("quotation_order") }}'),
        (r'已发送报价单', '{{ _("sent_quotation") }}'),
        (r'选择要导入的订单状态类型', '{{ _("status_filter_help") }}'),
        (r'<!-- 权限说明 -->', '<!-- {{ _("permission_description") }} -->'),
        (r'Toast 提示系统', '{{ _("toast_system") }}'),
        (r'Toast 提示系统样式', '{{ _("toast_system_styles") }}'),
        (r'警告框样式', '{{ _("warning_box_styles") }}'),
        (r'工具提示样式', '{{ _("tooltip_styles") }}'),
        (r'警告和提示颜色调整', '{{ _("warning_tip_color_adjustment") }}'),
        (r'Toast 提示容器', '{{ _("toast_container") }}'),
        (r'查看最近导入的销售订单数据', '{{ _("view_recent_imported_sales_data") }}'),
        (r'<!-- 错误消息 -->', '<!-- {{ _("error_message") }} -->'),
        (r'<!-- 当前过滤设定提示 -->', '<!-- {{ _("current_filter_settings_tip") }} -->'),
        (r'最小金额阈值:', '{{ _("min_amount_threshold") }}:'),
        (r'客户数', '{{ _("customer_count") }}'),
        (r'日期范围', '{{ _("date_range") }}'),
        (r'订单日期', '{{ _("order_date") }}'),
        
        # 成功、错误、警告、提示
        (r'\'success\': \'成功\',', '\'success\': \'{{ _("success") }}\','),
        (r'\'error\': \'错误\',', '\'error\': \'{{ _("error") }}\','),
        (r'\'warning\': \'警告\',', '\'warning\': \'{{ _("warning") }}\','),
        (r'\'info\': \'提示\'', '\'info\': \'{{ _("tip") }}\''),
        (r'提示', '{{ _("tip") }}'),
    ]
    
    new_keys = set()
    
    for html_file in html_files:
        if not os.path.exists(html_file):
            continue
            
        print(f"处理文件: {html_file}")
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用替换规则
        for pattern, replacement in replacements:
            matches = re.findall(pattern, content)
            if matches:
                print(f"  找到匹配: {pattern}")
                content = re.sub(pattern, replacement, content)
                
                # 提取新的翻译键
                if '{{ _(' in replacement:
                    key_match = re.search(r'{{ _\("([^"]+)"\)', replacement)
                    if key_match:
                        new_keys.add(key_match.group(1))
        
        # 写回文件
        if content != original_content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  已更新: {html_file}")
        else:
            print(f"  无需更新: {html_file}")
    
    return new_keys

def main():
    print("开始修复剩余的硬编码文字...")
    
    # 修复HTML文件
    new_keys = fix_remaining_hardcoded_text()
    
    # 更新翻译文件
    if new_keys:
        print(f"\n发现 {len(new_keys)} 个新的翻译键:")
        for key in sorted(new_keys):
            print(f"  - {key}")
        
        update_translation_files(new_keys)
        
        print("\n请运行以下命令编译翻译文件:")
        print("python manage_translations.py compile")
    else:
        print("\n没有发现新的翻译键")

if __name__ == '__main__':
    main()
