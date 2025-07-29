#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
sys.path.append('.')

from app import OCCWPriceTransformer

def test_uploaded_pricelist():
    """测试upload目录下的test-pricelist.xlsx文件"""
    
    print("=== 测试upload/test-pricelist.xlsx文件 ===\n")
    
    file_path = "upload/test-pricelist.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📁 找到文件: {file_path}")
    
    # 先检查文件的基本信息
    try:
        df = pd.read_excel(file_path, header=0)
        print(f"📊 文件包含 {len(df)} 行数据")
        print(f"📋 列名: {list(df.columns)}")
        
        # 显示前几行数据
        print("\n📖 前5行数据预览:")
        print(df.head().to_string())
        
        # 检查各列的数据类型和缺失值
        print("\n📈 数据概况:")
        print(df.info())
        
        # 检查产品类别分布
        if '产品类别/名称' in df.columns:
            print("\n📊 产品类别分布:")
            category_counts = df['产品类别/名称'].value_counts()
            for category, count in category_counts.items():
                print(f"  - {category}: {count} 条")
        
        # 检查变体值的格式
        if '变体值' in df.columns:
            print("\n🔧 变体值格式分析:")
            variant_types = {}
            for variant in df['变体值'].dropna().unique():
                if variant and isinstance(variant, str):
                    if variant.startswith('门板: '):
                        variant_types['门板变体'] = variant_types.get('门板变体', 0) + 1
                    elif variant.startswith('柜身: '):
                        variant_types['柜身变体'] = variant_types.get('柜身变体', 0) + 1
                    else:
                        variant_types['其他格式'] = variant_types.get('其他格式', 0) + 1
            
            for vtype, count in variant_types.items():
                print(f"  - {vtype}: {count} 种")
        
    except Exception as e:
        print(f"❌ 读取文件失败: {str(e)}")
        return
    
    # 使用转换器测试
    print("\n" + "="*50)
    print("🔄 开始使用转换器处理...")
    
    try:
        transformer = OCCWPriceTransformer()
        transformed_data, errors = transformer.transform_excel_file(file_path)
        
        print(f"\n✅ 转换完成!")
        print(f"📊 成功转换: {len(transformed_data)} 条记录")
        print(f"❌ 转换错误: {len(errors)} 个")
        
        if errors:
            print(f"\n🚨 错误详情 (显示前10个):")
            for i, error in enumerate(errors[:10]):
                print(f"  {i+1}. {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")
        
        if transformed_data:
            print(f"\n📋 转换结果示例 (前5条):")
            for i, item in enumerate(transformed_data[:5]):
                print(f"  {i+1}. SKU: {item['SKU']}")
                print(f"     产品名称: {item['product_name']}")
                print(f"     门板变体: '{item['door_variant']}', 柜身变体: '{item['box_variant']}'")
                print(f"     类别: {item['category']}, 价格: ${item['unit_price']}")
                print()
        
        # 分析转换后的数据分布
        if transformed_data:
            print("📈 转换后数据分布:")
            categories = {}
            for item in transformed_data:
                cat = item['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in sorted(categories.items()):
                print(f"  - {category}: {count} 条")
        
        return len(transformed_data), len(errors)
        
    except Exception as e:
        print(f"❌ 转换过程中发生错误: {str(e)}")
        return 0, 1

if __name__ == "__main__":
    test_uploaded_pricelist() 