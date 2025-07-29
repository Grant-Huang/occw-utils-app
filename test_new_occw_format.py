#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
import sys
sys.path.append('.')

from app import OCCWPriceTransformer

def create_test_excel():
    """创建测试Excel文件"""
    
    test_data = [
        {
            'SKU': 'PLY-2DB36-BSS',
            '销售价（单价）': 150.0,
            '变体值': '门板: BSS',
            '名称': 'PLY-2DB36',
            '产品类别': 'RTA Assm.组合件'
        },
        {
            'SKU': 'B18-DOOR-GSS',
            '销售价（单价）': 80.0,
            '变体值': '门板: GSS',
            '名称': 'B18-DOOR',
            '产品类别': 'Door'
        },
        {
            'SKU': 'WOC3015-OPEN-BSS',
            '销售价（单价）': 120.0,
            '变体值': '门板: BSS',
            '名称': 'WOC3015-OPEN',
            '产品类别': 'BOX'
        },
        {
            'SKU': 'B33-BOX-PLY',
            '销售价（单价）': 100.0,
            '变体值': '柜身: PLY',
            '名称': 'B33-BOX',
            '产品类别': 'BOX'
        },
        {
            'SKU': 'EP24-BSS',
            '销售价（单价）': 60.0,
            '变体值': '门板: BSS',
            '名称': 'EP24',
            '产品类别': 'Ending Panel'
        },
        {
            'SKU': 'HW-BSR06-SPICERACK',
            '销售价（单价）': 25.0,
            '变体值': '',
            '名称': 'HW-BSR06-SPICERACK',
            '产品类别': 'Hardware'
        },
        # 添加一些错误案例
        {
            'SKU': 'ERROR-SKU-1',
            '销售价（单价）': 50.0,
            '变体值': '门板: XX',  # 错误：应该是3个字符
            '名称': 'ERROR-ITEM',
            '产品类别': 'Door'
        },
        {
            'SKU': 'ERROR-SKU-2',
            '销售价（单价）': 75.0,
            '变体值': '',  # 错误：标准BOX变体值不能为空
            '名称': 'ERROR-BOX',
            '产品类别': 'BOX'
        }
    ]
    
    df = pd.DataFrame(test_data)
    test_file = 'test_occw_prices.xlsx'
    df.to_excel(test_file, index=False)
    
    print(f"✅ 创建测试Excel文件: {test_file}")
    return test_file

def test_transformer():
    """测试转换器"""
    
    print("=== 测试新的OCCW价格表转换功能 ===\n")
    
    # 创建测试文件
    test_file = create_test_excel()
    
    try:
        # 使用转换器处理文件
        transformer = OCCWPriceTransformer()
        transformed_data, errors = transformer.transform_excel_file(test_file)
        
        print(f"📊 转换结果统计:")
        print(f"  - 成功转换: {len(transformed_data)} 条数据")
        print(f"  - 发现错误: {len(errors)} 个")
        
        if transformed_data:
            print(f"\n✅ 成功转换的数据:")
            for i, item in enumerate(transformed_data, 1):
                print(f"  {i}. SKU: {item['SKU']}")
                print(f"     产品名称: {item['product_name']}")
                print(f"     门板变体: {item['door_variant']}")
                print(f"     柜身变体: {item['box_variant']}")
                print(f"     类别: {item['category']}")
                print(f"     销售单价: {item['unit_price']}")
                print()
        
        if errors:
            print(f"❌ 发现的错误:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            print()
        
        # 验证规则实现
        print("🔍 验证转换规则:")
        
        # 检查RTA组合件
        assm_items = [item for item in transformed_data if item['category'] == 'Assm.组合件']
        if assm_items:
            item = assm_items[0]
            print(f"  ✅ RTA组合件: {item['SKU']} -> 门板变体:{item['door_variant']}, 柜身变体:{item['box_variant']}, 产品名称:{item['product_name']}")
        
        # 检查Door
        door_items = [item for item in transformed_data if item['category'] == 'Door']
        if door_items:
            item = door_items[0]
            print(f"  ✅ Door: {item['SKU']} -> 门板变体:{item['door_variant']}, 产品名称:{item['product_name']}")
        
        # 检查开放BOX
        open_box_items = [item for item in transformed_data if item['category'] == 'BOX' and 'OPEN' in item['SKU']]
        if open_box_items:
            item = open_box_items[0]
            print(f"  ✅ 开放BOX: {item['SKU']} -> 门板变体:{item['door_variant']}, 产品名称:{item['product_name']}")
        
        # 检查标准BOX
        standard_box_items = [item for item in transformed_data if item['category'] == 'BOX' and 'OPEN' not in item['SKU']]
        if standard_box_items:
            item = standard_box_items[0]
            print(f"  ✅ 标准BOX: {item['SKU']} -> 柜身变体:{item['box_variant']}, 产品名称:{item['product_name']}")
        
        # 检查配件
        accessory_items = [item for item in transformed_data if item['category'] in ['Ending Panel', 'Molding', 'Toe Kick', 'Filler']]
        if accessory_items:
            item = accessory_items[0]
            print(f"  ✅ 配件: {item['SKU']} -> 门板变体:{item['door_variant']}, 产品名称:{item['product_name']}")
        
        # 检查五金件
        hardware_items = [item for item in transformed_data if item['category'] == 'HARDWARE']
        if hardware_items:
            item = hardware_items[0]
            print(f"  ✅ 五金件: {item['SKU']} -> 产品名称:{item['product_name']} (已去除HW-前缀)")
        
        print(f"\n🎉 测试完成！")
        
        if len(errors) == 2:  # 我们故意添加了2个错误案例
            print("✅ 错误检测功能正常工作")
        else:
            print(f"⚠️ 错误检测可能有问题，预期2个错误，实际{len(errors)}个")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️ 清理测试文件: {test_file}")

if __name__ == "__main__":
    test_transformer() 