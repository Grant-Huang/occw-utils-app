#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复HTML中的硬编码文字，替换为国际化调用
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
        'select_box_variant': '选择柜身变体',
        'select_door_variant': '选择门板变体',
        'original_sku': '(原始)',
        'summary': '汇总',
        'time_period': '时间区间',
        'showing_records': '显示 {start}-{end} 条，共 {total} 条',
        'all_sales_persons': '全部销售人员',
        'load_product_list_failed': '加载产品列表失败',
        'search_sku_failed': '搜索SKU失败',
        'enter_valid_sku': '请输入有效的SKU',
        'not_found': '未找到',
        'search': '搜索',
        'close': '关闭',
        'previous_page': '上一页',
        'next_page': '下一页',
        'enter_occw_sku': '输入OCCW SKU',
        'search_placeholder': '搜索...',
        'search_number_customer_salesperson': '搜索编号、客户或销售人员',
        'data_pagination': '数据分页',
        'customer_order_analysis_pagination': '客户订单分析分页',
        'no_matching_sku_found': '未找到匹配的SKU',
        'sales_person_monthly_data_not_found': '未找到销售员 {sales_person} 的月度数据'
    }
    
    # 英文翻译映射
    en_translations = {
        'select_box_variant': 'Select Box Variant',
        'select_door_variant': 'Select Door Variant',
        'original_sku': '(Original)',
        'summary': 'Summary',
        'time_period': 'Time Period',
        'showing_records': 'Showing {start}-{end} of {total} records',
        'all_sales_persons': 'All Sales Persons',
        'load_product_list_failed': 'Failed to load product list',
        'search_sku_failed': 'Failed to search SKU',
        'enter_valid_sku': 'Please enter a valid SKU',
        'not_found': 'Not Found',
        'search': 'Search',
        'close': 'Close',
        'previous_page': 'Previous',
        'next_page': 'Next',
        'enter_occw_sku': 'Enter OCCW SKU',
        'search_placeholder': 'Search...',
        'search_number_customer_salesperson': 'Search by number, customer or salesperson',
        'data_pagination': 'Data Pagination',
        'customer_order_analysis_pagination': 'Customer Order Analysis Pagination',
        'no_matching_sku_found': 'No matching SKU found',
        'sales_person_monthly_data_not_found': 'No monthly data found for salesperson {sales_person}'
    }
    
    # 法文翻译映射
    fr_translations = {
        'select_box_variant': 'Sélectionner la variante de boîte',
        'select_door_variant': 'Sélectionner la variante de porte',
        'original_sku': '(Original)',
        'summary': 'Résumé',
        'time_period': 'Période',
        'showing_records': 'Affichage de {start}-{end} sur {total} enregistrements',
        'all_sales_persons': 'Tous les vendeurs',
        'load_product_list_failed': 'Échec du chargement de la liste des produits',
        'search_sku_failed': 'Échec de la recherche SKU',
        'enter_valid_sku': 'Veuillez entrer un SKU valide',
        'not_found': 'Non trouvé',
        'search': 'Rechercher',
        'close': 'Fermer',
        'previous_page': 'Précédent',
        'next_page': 'Suivant',
        'enter_occw_sku': 'Entrer SKU OCCW',
        'search_placeholder': 'Rechercher...',
        'search_number_customer_salesperson': 'Rechercher par numéro, client ou vendeur',
        'data_pagination': 'Pagination des données',
        'customer_order_analysis_pagination': 'Pagination de l\'analyse des commandes clients',
        'no_matching_sku_found': 'Aucun SKU correspondant trouvé',
        'sales_person_monthly_data_not_found': 'Aucune donnée mensuelle trouvée pour le vendeur {sales_person}'
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

def fix_html_files():
    """修复HTML文件中的硬编码文字"""
    html_files = [
        'templates/index.html',
        'templates/admin.html',
        'templates/converted_data.html',
        'templates/imported_data.html',
        'templates/prices.html',
        'templates/sku_mappings.html'
    ]
    
    # 定义替换规则
    replacements = [
        # 选择变体
        (r'选择柜身变体', '{{ _("select_box_variant") }}'),
        (r'选择门板变体', '{{ _("select_door_variant") }}'),
        
        # 原始SKU
        (r'\(原始\)', '{{ _("original_sku") }}'),
        
        # 汇总和时间区间
        (r'汇总', '{{ _("summary") }}'),
        (r'时间区间', '{{ _("time_period") }}'),
        
        # 显示记录信息
        (r'显示 (\d+)-(\d+) 条，共 (\d+) 条', r'{{ _("showing_records").format(start="\1", end="\2", total="\3") }}'),
        (r'显示第 (\d+) 到 (\d+) 条，共 (\d+) 条记录', r'{{ _("showing_records").format(start="\1", end="\2", total="\3") }}'),
        (r'显示 (\d+)-(\d+) 条，共 (\d+) 条记录', r'{{ _("showing_records").format(start="\1", end="\2", total="\3") }}'),
        
        # 全部销售人员
        (r'全部销售人员', '{{ _("all_sales_persons") }}'),
        
        # showAlert消息
        (r'showAlert\(\'加载产品列表失败\', \'warning\'\);', 'showAlert(\'{{ _("load_product_list_failed") }}\', \'warning\');'),
        (r'showAlert\(\'搜索SKU失败\', \'warning\'\);', 'showAlert(\'{{ _("search_sku_failed") }}\', \'warning\');'),
        (r'showAlert\(\'请输入有效的SKU\', \'warning\'\);', 'showAlert(\'{{ _("enter_valid_sku") }}\', \'warning\');'),
        
        # 未找到
        (r'textContent = \'未找到\';', 'textContent = \'{{ _("not_found") }}\';'),
        (r'未找到匹配的SKU', '{{ _("no_matching_sku_found") }}'),
        (r'未找到销售员 (\w+) 的月度数据', r'{{ _("sales_person_monthly_data_not_found").format(sales_person="\1") }}'),
        
        # 按钮和标签
        (r'>搜索<', '>{{ _("search") }}<'),
        (r'>关闭<', '>{{ _("close") }}<'),
        (r'>上一页<', '>{{ _("previous_page") }}<'),
        (r'>下一页<', '>{{ _("next_page") }}<'),
        
        # placeholder属性
        (r'placeholder="输入OCCW SKU"', 'placeholder="{{ _("enter_occw_sku") }}"'),
        (r'placeholder="搜索\.\.\."', 'placeholder="{{ _("search_placeholder") }}"'),
        (r'placeholder="搜索编号、客户或销售人员"', 'placeholder="{{ _("search_number_customer_salesperson") }}"'),
        
        # aria-label属性
        (r'aria-label="数据分页"', 'aria-label="{{ _("data_pagination") }}"'),
        (r'aria-label="客户订单分析分页"', 'aria-label="{{ _("customer_order_analysis_pagination") }}"'),
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
    print("开始修复HTML中的硬编码文字...")
    
    # 修复HTML文件
    new_keys = fix_html_files()
    
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
