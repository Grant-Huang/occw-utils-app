#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

def create_sample_excel():
    """创建包含2字符门板变体的Excel样例文件"""
    
    print("=== 创建Excel样例文件 ===\n")
    
    # 创建测试数据，包含2字符和3字符的门板变体
    sample_data = [
        {
            '内部参考号': '2DB30-PLY-BSS',
            '销售价': 874,
            '变体值': '门板: BSS',
            '名称': 'PLY-2DB30',
            '产品类别/名称': 'RTA Assm.组合件'
        },
        {
            '内部参考号': '3DB18-PLY-GD',
            '销售价': 650,
            '变体值': '门板: GD',  # 2字符门板变体
            '名称': 'PLY-3DB18',
            '产品类别/名称': 'RTA Assm.组合件'
        },
        {
            '内部参考号': 'B18-DOOR-WSS',
            '销售价': 80,
            '变体值': '门板: WSS',
            '名称': 'B18-DOOR',
            '产品类别/名称': 'Door'
        },
        {
            '内部参考号': 'B24-DOOR-GD',
            '销售价': 95,
            '变体值': '门板: GD',  # 2字符门板变体
            '名称': 'B24-DOOR',
            '产品类别/名称': 'Door'
        },
        {
            '内部参考号': 'B33-BOX-PLY',
            '销售价': 100,
            '变体值': '柜身: PLY',
            '名称': 'B33-BOX',
            '产品类别/名称': 'BOX'
        },
        {
            '内部参考号': 'EP24-BSS',
            '销售价': 60,
            '变体值': '门板: BSS',
            '名称': 'EP24',
            '产品类别/名称': 'Ending Panel'
        },
        {
            '内部参考号': 'HW-BSR06-SPICERACK',
            '销售价': 25,
            '变体值': '',  # 空变体值
            '名称': 'HW-BSR06-SPICERACK',
            '产品类别/名称': 'Hardware'
        }
    ]
    
    # 创建DataFrame
    df = pd.DataFrame(sample_data)
    
    # 保存为Excel文件
    output_file = 'sample_pricelist_with_2char_variants.xlsx'
    df.to_excel(output_file, index=False)
    
    print(f"✅ 创建样例文件: {output_file}")
    print(f"📊 包含 {len(sample_data)} 行测试数据")
    print("\n📋 数据内容:")
    print(df.to_string())
    
    # 测试转换器
    print(f"\n" + "="*50)
    print("🔄 测试转换器...")
    
    sys.path.append('.')
    from app import OCCWPriceTransformer
    
    transformer = OCCWPriceTransformer()
    transformed_data, errors = transformer.transform_excel_file(output_file)
    
    print(f"\n✅ 转换结果:")
    print(f"📊 成功转换: {len(transformed_data)} 条")
    print(f"❌ 错误数量: {len(errors)} 个")
    
    if errors:
        print(f"\n🚨 错误详情:")
        for error in errors:
            print(f"  - {error}")
    
    if transformed_data:
        print(f"\n📋 转换后的数据:")
        for i, item in enumerate(transformed_data, 1):
            print(f"  {i}. SKU: {item['SKU']}")
            print(f"     产品名称: {item['product_name']}")
            print(f"     门板变体: '{item['door_variant']}', 柜身变体: '{item['box_variant']}'")
            print(f"     类别: {item['category']}, 价格: ${item['unit_price']}")
            print()
    
    return output_file

if __name__ == "__main__":
    import sys
    create_sample_excel() 