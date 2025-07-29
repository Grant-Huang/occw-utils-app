#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
sys.path.append('.')

from app import OCCWPriceTransformer

def test_complete_rewrite():
    """测试完全重写后的OCCW价格表导入功能"""
    
    print("=" * 60)
    print("🔄 测试完全重写后的OCCW价格表导入功能")
    print("=" * 60)
    
    # 1. 测试转换器类
    print("\n📊 1. 测试OCCWPriceTransformer类")
    print("-" * 40)
    
    transformer = OCCWPriceTransformer()
    print(f"✅ 转换器初始化成功")
    
    # 2. 测试upload目录中的test-pricelist.xlsx文件
    test_file = "upload/test-pricelist.xlsx"
    if os.path.exists(test_file):
        print(f"\n📂 2. 测试文件: {test_file}")
        print("-" * 40)
        
        try:
            # 使用重写后的转换器
            transformed_data, errors = transformer.transform_excel_file(test_file)
            
            print(f"📊 转换结果:")
            print(f"   ✅ 成功转换: {len(transformed_data)} 条记录")
            print(f"   ❌ 转换错误: {len(errors)} 个")
            
            if errors:
                print(f"\n🚨 错误详情（前10个）:")
                for i, error in enumerate(errors[:10]):
                    print(f"   {i+1}. {error}")
                if len(errors) > 10:
                    print(f"   ... 还有 {len(errors) - 10} 个错误")
            
            if transformed_data:
                print(f"\n📋 转换成功的数据示例（前5条）:")
                for i, item in enumerate(transformed_data[:5]):
                    print(f"   {i+1}. SKU: {item['SKU']}")
                    print(f"      产品名称: {item['product_name']}")
                    print(f"      门板变体: '{item['door_variant']}', 柜身变体: '{item['box_variant']}'")
                    print(f"      类别: {item['category']}, 价格: ${item['unit_price']}")
                    print()
                
                # 分析产品类别分布
                categories = {}
                for item in transformed_data:
                    cat = item['category']
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"📈 产品类别分布:")
                for category, count in sorted(categories.items()):
                    print(f"   - {category}: {count} 条")
            
            print(f"\n✅ 文件测试完成")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ 测试文件不存在: {test_file}")
    
    # 3. 测试各种产品类别的转换规则
    print(f"\n🔧 3. 测试转换规则")
    print("-" * 40)
    
    test_rules_data = [
        {
            '内部参考号': '2DB30-PLY-BSS',
            '销售价': 874,
            '变体值': '门板: BSS',
            '名称': 'PLY-2DB30',
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
            '内部参考号': 'WOC3015-OPEN-BSS',
            '销售价': 120,
            '变体值': '门板: BSS',
            '名称': 'WOC3015-OPEN',
            '产品类别/名称': 'BOX'
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
            '变体值': '',
            '名称': 'HW-BSR06-SPICERACK',
            '产品类别/名称': 'Hardware'
        },
        {
            '内部参考号': 'TEST-GD-VARIANT',
            '销售价': 50,
            '变体值': '门板: GD',  # 2字符门板变体
            '名称': 'PLY-TEST',
            '产品类别/名称': 'RTA Assm.组合件'
        }
    ]
    
    print(f"测试 {len(test_rules_data)} 种产品类别的转换规则:")
    
    transformer = OCCWPriceTransformer()
    success_count = 0
    
    for i, data in enumerate(test_rules_data, 1):
        print(f"\n{i}. 测试：{data['产品类别/名称']} - {data['名称']}")
        
        # 模拟pandas Series
        series = pd.Series(data)
        result = transformer.transform_single_row(series, i)
        
        if result:
            print(f"   ✅ 转换成功")
            print(f"   SKU: {result['SKU']}")
            print(f"   产品名称: '{result['product_name']}'")
            print(f"   门板变体: '{result['door_variant']}', 柜身变体: '{result['box_variant']}'")
            print(f"   类别: {result['category']}, 价格: ${result['unit_price']}")
            success_count += 1
        else:
            print(f"   ❌ 转换失败")
    
    # 显示测试规则的错误
    error_summary = transformer.get_error_summary()
    if error_summary['has_errors']:
        print(f"\n🚨 转换规则测试中的错误:")
        for error in error_summary['error_details']:
            print(f"   - {error}")
    
    print(f"\n📊 转换规则测试总结:")
    print(f"   成功: {success_count}/{len(test_rules_data)}")
    print(f"   错误: {error_summary['total_errors']} 个")
    
    print("\n" + "=" * 60)
    print("🎉 完全重写后的OCCW价格表导入功能测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_rewrite() 