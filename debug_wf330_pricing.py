#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')
from app import extract_pdf_content, parse_quotation_pdf, generate_sku, generate_final_sku, load_occw_prices, load_sku_mappings, occw_prices

def debug_wf330_pricing():
    """调试WF330价格问题"""
    
    # 加载数据
    load_occw_prices()
    load_sku_mappings()
    
    print("=== 调试WF330价格问题 ===")
    
    # 解析sample02.pdf
    pdf_path = 'upload/sample02.pdf'
    pdf_content = extract_pdf_content(pdf_path, add_page_markers=True)
    products, compare_result, compare_message = parse_quotation_pdf(pdf_content)
    
    # 查找所有包含WF330的产品
    wf330_products = []
    for product in products:
        if ('WF330' in str(product.get('user_code', '')) or 
            'WF330' in str(product.get('manuf_code', '')) or 
            'WF330' in str(product.get('sku', ''))):
            wf330_products.append(product)
    
    print(f"\n在sample02.pdf中找到 {len(wf330_products)} 个包含WF330的产品")
    
    for i, product in enumerate(wf330_products, 1):
        print(f"\n--- 第{i}个WF330产品 ---")
        for key, value in product.items():
            print(f"  {key}: {value}")
        
        # 检查SKU生成逻辑
        user_code = product.get('user_code', '')
        description = product.get('description', '')
        door_color = product.get('door_color', '')
        
        # 生成SKU
        original_sku = generate_sku(user_code, description, door_color)
        final_sku = generate_final_sku(user_code, description, door_color)
        
        print(f"  生成的原始SKU: {original_sku}")
        print(f"  映射后的最终SKU: {final_sku}")
        
        # 检查价格表中的价格
        occw_price = occw_prices.get(final_sku, "未找到")
        print(f"  OCCW价格表中的价格: {occw_price}")
        
        # 对比产品中的unit_price
        unit_price = product.get('unit_price', 0)
        print(f"  产品中的unit_price: {unit_price}")
        
        if occw_price != "未找到" and float(occw_price) != float(unit_price):
            print(f"  ⚠️ 价格不匹配! OCCW价格={occw_price}, 产品价格={unit_price}")
        elif unit_price == 0:
            print(f"  ❌ 产品价格为0!")
        else:
            print(f"  ✅ 价格正常")

def check_wf330_in_price_table():
    """检查价格表中所有WF330相关的SKU"""
    
    load_occw_prices()
    
    print("\n=== 价格表中所有WF330相关的SKU ===")
    wf330_skus = {}
    for sku, price in occw_prices.items():
        if 'WF330' in sku:
            wf330_skus[sku] = price
    
    print(f"找到 {len(wf330_skus)} 个WF330相关的SKU:")
    for sku, price in sorted(wf330_skus.items()):
        print(f"  {sku}: {price}")

def test_sku_generation():
    """测试不同user_code的SKU生成"""
    
    print("\n=== 测试SKU生成逻辑 ===")
    
    test_cases = [
        {
            'user_code': 'WF330',
            'description': 'Base Accessory',
            'door_color': 'PGW'
        },
        {
            'user_code': 'WF330 FOR',
            'description': 'Base Accessory', 
            'door_color': 'PGW'
        },
        {
            'user_code': 'WF330 FOR BASE',
            'description': 'Base Accessory',
            'door_color': 'PGW'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例{i}:")
        print(f"  user_code: {case['user_code']}")
        print(f"  description: {case['description']}")
        print(f"  door_color: {case['door_color']}")
        
        original_sku = generate_sku(case['user_code'], case['description'], case['door_color'])
        final_sku = generate_final_sku(case['user_code'], case['description'], case['door_color'])
        
        print(f"  生成的原始SKU: {original_sku}")
        print(f"  映射后的最终SKU: {final_sku}")
        
        occw_price = occw_prices.get(final_sku, "未找到")
        print(f"  OCCW价格: {occw_price}")

if __name__ == "__main__":
    debug_wf330_pricing()
    check_wf330_in_price_table()
    test_sku_generation() 