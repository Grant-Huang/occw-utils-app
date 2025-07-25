#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')
from app import extract_pdf_content, parse_quotation_pdf, load_occw_prices, load_sku_mappings
from collections import Counter

def test_seq_num_issue():
    """测试seq_num重复导致前端ID冲突的问题"""
    
    # 加载数据
    load_occw_prices()
    load_sku_mappings()
    
    # 解析sample02.pdf
    pdf_path = 'upload/sample02.pdf'
    pdf_content = extract_pdf_content(pdf_path, add_page_markers=True)
    products, compare_result, compare_message = parse_quotation_pdf(pdf_content)
    
    print('=== 检查产品序号问题 ===')
    
    wf330_products = []
    all_seq_nums = []
    
    for product in products:
        seq_num = product.get('seq_num', '')
        all_seq_nums.append(seq_num)
        
        if ('WF330' in str(product.get('user_code', '')) or 
            'WF330' in str(product.get('manuf_code', '')) or 
            'WF330' in str(product.get('sku', ''))):
            wf330_products.append(product)
    
    print(f'所有产品的序号: {all_seq_nums}')
    print(f'\n找到 {len(wf330_products)} 个WF330产品:')
    
    for i, product in enumerate(wf330_products, 1):
        seq_num = product.get('seq_num', '')
        sku = product.get('sku', '')
        manuf_code = product.get('manuf_code', '')
        print(f'  第{i}个WF330产品: seq_num="{seq_num}", sku="{sku}", manuf_code="{manuf_code}"')
    
    # 检查seq_num重复情况
    seq_counter = Counter(all_seq_nums)
    duplicates = {seq: count for seq, count in seq_counter.items() if count > 1}
    
    if duplicates:
        print(f'\n❌ 发现重复的序号:')
        for seq, count in duplicates.items():
            print(f'  序号 "{seq}" 出现了 {count} 次')
            
        print(f'\n📝 这会导致前端ID冲突:')
        for seq, count in duplicates.items():
            print(f'  ID sku-cell-{seq}, occw-price-{seq}, occw-total-{seq} 被 {count} 个产品共享')
            print(f'  结果：只有第一个产品能正确更新OCCW价格，其他产品显示为$0.00')
    else:
        print(f'\n✅ 没有重复的序号')
    
    print(f'\n=== 前端ID分析 ===')
    for i, product in enumerate(wf330_products, 1):
        seq_num = product.get('seq_num', '')
        print(f'第{i}个WF330产品的前端ID:')
        print(f'  SKU单元格ID: sku-cell-{seq_num}')
        print(f'  OCCW价格ID: occw-price-{seq_num}')
        print(f'  OCCW总价ID: occw-total-{seq_num}')

def check_correct_seq_nums():
    """从PDF原始内容中提取正确的序号"""
    
    print(f'\n=== 从PDF原始内容中提取正确的序号 ===')
    
    # 直接从PDF中提取WF330相关行
    import PyPDF2
    with open('upload/sample02.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        content = ''
        for page in reader.pages:
            content += page.extract_text()
    
    lines = content.split('\n')
    wf330_lines = []
    for i, line in enumerate(lines):
        if 'WF330' in line and 'BASE' in line and '30.00' in line:
            wf330_lines.append((i, line.strip()))
    
    print('PDF中的WF330相关行:')
    for line_num, line in wf330_lines:
        print(f'  行 {line_num}: {line}')
        
        # 尝试提取正确的序号
        import re
        seq_match = re.search(r'BASE(\d+)', line)
        if seq_match:
            correct_seq = seq_match.group(1)
            print(f'    正确序号应该是: {correct_seq}')

if __name__ == "__main__":
    test_seq_num_issue()
    check_correct_seq_nums() 