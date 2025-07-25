#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import generate_sku, generate_final_sku, apply_sku_mapping, load_sku_mappings

def test_sku_mapping():
    """测试SKU映射功能"""
    
    # 加载现有的SKU映射关系
    load_sku_mappings()
    
    print("=== 测试SKU映射功能 ===")
    
    # 测试用例
    test_cases = [
        {
            'user_code': 'FS36',
            'description': 'Wall Accessory',
            'door_color': 'SSW',
            'expected_original': 'SSW-FS36',
            'expected_mapped': 'WSS-FS36'  # 根据现有映射关系
        },
        {
            'user_code': 'WSL3615',
            'description': 'Wall Stay Lift',
            'door_color': 'SSW',
            'expected_original': 'SSW-WSL3615',
            'expected_mapped': 'WSL3615-PLY-SSW'  # 根据现有映射关系
        },
        {
            'user_code': 'BEP24',
            'description': 'Base Accessory',
            'door_color': 'SSW',
            'expected_original': 'SSW-BEP24',
            'expected_mapped': 'WSS-BEP24'  # 根据现有映射关系
        },
        {
            'user_code': 'UNKNOWN',
            'description': 'Unknown Accessory',
            'door_color': 'WSS',
            'expected_original': 'WSS-UNKNOWN',
            'expected_mapped': 'WSS-UNKNOWN'  # 没有映射，应该保持原样
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"输入: user_code='{test_case['user_code']}', description='{test_case['description']}', door_color='{test_case['door_color']}'")
        
        # 生成原始SKU
        original_sku = generate_sku(
            test_case['user_code'], 
            test_case['description'], 
            test_case['door_color']
        )
        
        # 应用映射
        mapped_sku = apply_sku_mapping(original_sku)
        
        # 使用generate_final_sku（应该和mapped_sku相同）
        final_sku = generate_final_sku(
            test_case['user_code'], 
            test_case['description'], 
            test_case['door_color']
        )
        
        print(f"原始SKU: '{original_sku}'")
        print(f"映射后SKU: '{mapped_sku}'")
        print(f"最终SKU: '{final_sku}'")
        
        # 验证结果
        original_ok = original_sku == test_case['expected_original']
        mapped_ok = mapped_sku == test_case['expected_mapped']
        final_ok = final_sku == test_case['expected_mapped']
        
        print(f"验证结果:")
        print(f"  原始SKU: {'✅' if original_ok else '❌'} 期望='{test_case['expected_original']}', 实际='{original_sku}'")
        print(f"  映射SKU: {'✅' if mapped_ok else '❌'} 期望='{test_case['expected_mapped']}', 实际='{mapped_sku}'")
        print(f"  最终SKU: {'✅' if final_ok else '❌'} 期望='{test_case['expected_mapped']}', 实际='{final_sku}'")
        
        if original_ok and mapped_ok and final_ok:
            print("  ✅ 测试通过")
        else:
            print("  ❌ 测试失败")

def test_cabinet_sku_mapping():
    """测试Cabinet类型的SKU映射"""
    
    print("\n=== 测试Cabinet SKU映射 ===")
    
    # 加载映射关系
    load_sku_mappings()
    
    test_case = {
        'user_code': 'B36FH',
        'description': 'Base Full Height Cabinet 2 Door',
        'door_color': 'WSS'
    }
    
    print(f"测试Cabinet: user_code='{test_case['user_code']}', description='{test_case['description']}', door_color='{test_case['door_color']}'")
    
    # 生成原始SKU
    original_sku = generate_sku(
        test_case['user_code'], 
        test_case['description'], 
        test_case['door_color']
    )
    
    # 应用映射
    mapped_sku = apply_sku_mapping(original_sku)
    
    # 使用generate_final_sku
    final_sku = generate_final_sku(
        test_case['user_code'], 
        test_case['description'], 
        test_case['door_color']
    )
    
    print(f"原始SKU: '{original_sku}'")
    print(f"映射后SKU: '{mapped_sku}'")
    print(f"最终SKU: '{final_sku}'")
    
    # 根据现有映射关系，B36FH-PLY-WSS 映射到 B36FH-PB-WSS
    expected_original = 'B36FH-PLY-WSS'
    expected_mapped = 'B36FH-PB-WSS'
    
    original_ok = original_sku == expected_original
    mapped_ok = mapped_sku == expected_mapped
    final_ok = final_sku == expected_mapped
    
    print(f"验证结果:")
    print(f"  原始SKU: {'✅' if original_ok else '❌'} 期望='{expected_original}', 实际='{original_sku}'")
    print(f"  映射SKU: {'✅' if mapped_ok else '❌'} 期望='{expected_mapped}', 实际='{mapped_sku}'")
    print(f"  最终SKU: {'✅' if final_ok else '❌'} 期望='{expected_mapped}', 实际='{final_sku}'")

if __name__ == "__main__":
    test_sku_mapping()
    test_cabinet_sku_mapping() 