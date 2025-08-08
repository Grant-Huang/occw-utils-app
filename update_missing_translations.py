#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加遗漏的翻译键
"""

import os

def escape_po_string(text):
    """转义.po文件中的字符串"""
    if not isinstance(text, str):
        text = str(text)
    # 转义双引号和反斜杠
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    return text

def add_missing_translations():
    """添加遗漏的翻译键"""
    # 读取现有的翻译文件
    translation_files = {
        'zh': 'translations/zh/LC_MESSAGES/messages.po',
        'en': 'translations/en/LC_MESSAGES/messages.po',
        'fr': 'translations/fr/LC_MESSAGES/messages.po'
    }
    
    # 遗漏的翻译键
    missing_keys = {
        'no_monthly_data_found': {
            'zh': '没有找到月度数据',
            'en': 'No monthly data found',
            'fr': 'Aucune donnée mensuelle trouvée'
        },
        'chart_data_incomplete_skip_display': {
            'zh': '图表数据不完整，跳过图表显示',
            'en': 'Chart data incomplete, skipping chart display',
            'fr': 'Données de graphique incomplètes, saut de l\'affichage du graphique'
        }
    }
    
    for lang, file_path in translation_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加遗漏的翻译条目
            for key, translations in missing_keys.items():
                if key not in content:
                    translation = translations.get(lang, f'TODO: {key}')
                    
                    # 在文件末尾添加新的翻译条目
                    content += f'\nmsgid "{escape_po_string(key)}"\n'
                    content += f'msgstr "{escape_po_string(translation)}"\n'
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"已更新 {lang} 翻译文件: {file_path}")

def main():
    print("添加遗漏的翻译键...")
    add_missing_translations()
    print("完成！请运行以下命令编译翻译文件:")
    print("python manage_translations.py compile")

if __name__ == '__main__':
    main()
