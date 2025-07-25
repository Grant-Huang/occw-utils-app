#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os
sys.path.append('.')

def fix_multiline_product_parsing():
    """修复多行产品解析问题"""
    
    print("=== 修复多行产品解析问题 ===")
    
    # 模拟WF330的多行格式
    multiline_examples = [
        ["WF330 FOR", "BASE19 Base Accessory 30.00 1WF330 FOR", "BASE"],
        ["WF330 FOR", "BASE24 Base Accessory 30.00 1WF330 FOR", "BASE"],
        ["WF330 FOR", "BASE25 Base Accessory 30.00 1WF330 FOR", "BASE"]
    ]
    
    print("处理的多行格式示例:")
    for i, lines in enumerate(multiline_examples, 1):
        print(f"\n例子{i}: {lines}")
        
        # 合并所有行
        merged_text = " ".join(lines)
        print(f"合并文本: '{merged_text}'")
        
        # 正确的解析逻辑
        parsed = parse_multiline_product_correctly(merged_text)
        
        if parsed:
            print("解析结果:")
            for key, value in parsed.items():
                print(f"  {key}: '{value}'")
        else:
            print("解析失败")

def parse_multiline_product_correctly(merged_text):
    """正确解析多行产品格式"""
    
    parts = merged_text.split()
    if len(parts) < 6:
        return None
    
    # 找到价格位置
    price_index = -1
    for i, part in enumerate(parts):
        if re.match(r'^\d+\.\d{2}$', part):
            price_index = i
            break
    
    if price_index == -1:
        return None
    
    price = parts[price_index]
    
    # 价格后面：数量 + 制造编码
    after_price = parts[price_index + 1:]
    if not after_price:
        return None
    
    qty_match = re.match(r'^(\d+)', after_price[0])
    if not qty_match:
        return None
    
    qty = qty_match.group(1)
    
    # 制造编码
    remaining_after_qty = after_price[0][len(qty):]
    if remaining_after_qty:
        manuf_code_parts = [remaining_after_qty] + after_price[1:]
    else:
        manuf_code_parts = after_price[1:]
    
    manuf_code = ' '.join(manuf_code_parts)
    
    # 价格前面的部分：用户编码 + 序号+描述
    before_price = parts[:price_index]
    
    # 关键修复：正确识别序号
    user_code_parts = []
    seq_num = None
    description_parts = []
    
    # 从后往前找包含数字的部分（这是序号+描述的开始）
    for i in range(len(before_price) - 1, -1, -1):
        part = before_price[i]
        
        # 如果这个部分包含数字，且符合BASExx格式
        if re.search(r'BASE\d+|[A-Z]+\d+', part):
            # 提取序号
            seq_match = re.search(r'(\d+)', part)
            if seq_match:
                seq_num = seq_match.group(1)
                
                # 分离序号前后的部分
                # 对于BASE19，序号前是BASE，序号后是空
                before_seq_match = re.search(r'^(.*)(\d+)(.*)$', part)
                if before_seq_match:
                    before_seq = before_seq_match.group(1)  # "BASE"
                    after_seq = before_seq_match.group(3)   # ""
                    
                    # 用户编码是序号前面的所有部分
                    user_code_parts = before_price[:i]
                    if before_seq:
                        # 如果序号前有内容，添加到描述中
                        description_parts = [before_seq]
                    if after_seq:
                        description_parts.append(after_seq)
                    
                    # 序号后面的部分也是描述
                    description_parts.extend(before_price[i+1:])
                    
                    break
    
    if not seq_num:
        return None
    
    # 如果制造编码和用户编码应该相同，使用制造编码作为完整的用户编码
    user_code = ' '.join(user_code_parts) if user_code_parts else manuf_code
    
    # 描述是序号后面的所有描述性词汇
    description = ' '.join(description_parts).strip()
    
    # 生成简化编码
    simplified_code = user_code.split()[0] if user_code.split() else user_code
    
    return {
        'user_code': user_code,
        'seq_num': seq_num,
        'description': description,
        'price': price,
        'qty': qty,
        'manuf_code': manuf_code,
        'simplified_code': simplified_code
    }

def test_current_vs_fixed_parsing():
    """对比当前解析与修复后解析的差异"""
    
    print("\n=== 对比当前解析与修复后解析 ===")
    
    # 从实际PDF中获取的合并文本
    test_case = "WF330 FOR BASE19 Base Accessory 30.00 1WF330 FOR BASE"
    
    print(f"测试文本: '{test_case}'")
    
    # 使用修复后的解析
    fixed_result = parse_multiline_product_correctly(test_case)
    
    if fixed_result:
        print("\n修复后的解析结果:")
        for key, value in fixed_result.items():
            print(f"  {key}: '{value}'")
            
        print(f"\n✅ 修复后seq_num: '{fixed_result['seq_num']}' (应该解决前端ID冲突)")
    else:
        print("\n❌ 修复后解析失败")

if __name__ == "__main__":
    fix_multiline_product_parsing()
    test_current_vs_fixed_parsing() 