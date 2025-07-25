#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import PyPDF2
import os

def parse_multiline_product(merged_text):
    """
    解析多行合并的产品信息
    基于制造编码和用户编码通常相同的特点来分割产品信息
    
    例如：'WF330 FOR BASE19 Base Accessory 30.00 1WF330 FOR BASE'
    应解析为：
    - 用户编码: WF330 FOR BASE
    - 序号: 19
    - 描述: Base Accessory  
    - 总价: 30.00
    - 数量: 1
    - 制造编码: WF330 FOR BASE
    """
    
    parts = merged_text.split()
    if len(parts) < 4:
        return None
    
    # 寻找价格位置
    price_index = -1
    for i, part in enumerate(parts):
        if re.match(r'^\d+\.\d{2}$', part):
            price_index = i
            break
    
    if price_index == -1:
        return None
    
    price = parts[price_index]
    
    # 价格后面的部分应该包含：数量 + 制造编码
    after_price = parts[price_index + 1:]
    if not after_price:
        return None
    
    # 提取数量（通常是第一个数字）
    qty_match = re.match(r'^(\d+)', after_price[0])
    if not qty_match:
        return None
    
    qty = qty_match.group(1)
    
    # 剩余部分是制造编码
    remaining_after_qty = after_price[0][len(qty):]
    if remaining_after_qty:
        manuf_code_parts = [remaining_after_qty] + after_price[1:]
    else:
        manuf_code_parts = after_price[1:]
    
    manuf_code = ' '.join(manuf_code_parts)
    
    # 价格前面的部分
    before_price = parts[:price_index]
    
    # 新的策略：从后往前寻找序号
    # 序号通常在最后几个词中，可能与其他文字连在一起
    user_code = None
    seq_num = None
    description_parts = []
    
    # 从后往前检查，寻找包含数字的部分（序号）
    for i in range(len(before_price) - 1, -1, -1):
        part = before_price[i]
        
        # 如果这个部分包含数字，可能包含序号
        if re.search(r'\d+', part):
            # 提取数字作为序号
            seq_match = re.search(r'(\d+)', part)
            if seq_match:
                seq_num = seq_match.group(1)
                
                # 分离序号前后的部分
                seq_start = seq_match.start()
                seq_end = seq_match.end()
                
                before_seq = part[:seq_start]
                after_seq = part[seq_end:]
                
                # 用户编码是序号前面的所有部分
                user_code_parts = before_price[:i]
                if before_seq:
                    user_code_parts.append(before_seq)
                
                # 检查用户编码是否与制造编码匹配
                potential_user_code = ' '.join(user_code_parts).strip()
                
                # 如果用户编码与制造编码相似，则使用制造编码作为完整的用户编码
                if are_codes_similar(potential_user_code, manuf_code):
                    user_code = manuf_code
                else:
                    user_code = potential_user_code
                
                # 描述是序号后面的部分
                description_parts = []
                if after_seq:
                    description_parts.append(after_seq)
                description_parts.extend(before_price[i+1:])
                
                break
    
    if not user_code or not seq_num:
        return None
    
    description = ' '.join(description_parts).strip()
    
    # 生成简化编码（第一个词）
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

def are_codes_similar(code1, code2):
    """判断两个编码是否相似（考虑到可能的小差异）"""
    # 简单的相似性检查
    if code1 == code2:
        return True
    
    # 移除空格后比较
    if code1.replace(' ', '') == code2.replace(' ', ''):
        return True
    
    # 可以根据需要添加更多相似性规则
    return False

def detect_and_parse_multiline_products(pdf_content):
    """
    检测并解析PDF中的多行产品格式
    """
    lines = pdf_content.split('\n')
    multiline_products = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # 检查是否是多行产品的开始
        # 特征：短行，包含字母数字，不包含价格
        if (len(line) < 30 and 
            re.search(r'[A-Z]+\d+|FOR|BASE', line) and 
            not re.search(r'\d+\.\d{2}', line)):
            
            # 收集接下来的几行，直到找到完整的产品信息
            candidate_lines = [line]
            j = i + 1
            
            # 最多向前看3行
            while j < len(lines) and j < i + 4:
                next_line = lines[j].strip()
                if next_line:
                    candidate_lines.append(next_line)
                    
                    # 如果这一行包含价格，可能是完整的产品信息
                    if re.search(r'\d+\.\d{2}', next_line):
                        merged_text = ' '.join(candidate_lines)
                        parsed = parse_multiline_product(merged_text)
                        
                        if parsed:
                            multiline_products.append({
                                'original_lines': candidate_lines.copy(),
                                'line_numbers': list(range(i, j+1)),
                                'parsed_product': parsed
                            })
                            # 跳过已处理的行
                            i = j + 1
                            break
                j += 1
            else:
                i += 1
        else:
            i += 1
    
    return multiline_products

def test_multiline_parsing():
    """测试多行解析功能"""
    
    print("=== 测试用户提供的例子 ===")
    
    # 用户的例子 - 更新为实际PDF中的两行格式
    test_cases = [
        {
            'lines': ['WF330 FOR', 'BASE19 Base Accessory 30.00 1WF330 FOR'],
            'expected': {
                'user_code': 'WF330 FOR',
                'seq_num': '19',
                'description': 'Base Accessory',
                'price': '30.00',
                'qty': '1',
                'manuf_code': 'WF330 FOR'
            }
        },
        {
            'lines': ['WF330 FOR', 'BASE19 Base Accessory 30.00 1WF330 FOR', 'BASE'],
            'expected': {
                'user_code': 'WF330 FOR BASE',
                'seq_num': '19', 
                'description': 'Base Accessory',
                'price': '30.00',
                'qty': '1',
                'manuf_code': 'WF330 FOR BASE'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1} ---")
        print(f"原始行: {test_case['lines']}")
        
        merged = ' '.join(test_case['lines'])
        print(f"合并文本: '{merged}'")
        
        result = parse_multiline_product(merged)
        
        if result:
            print(f"解析结果:")
            for key, value in result.items():
                print(f"  {key}: '{value}'")
            
            # 验证结果
            expected = test_case['expected']
            print(f"\n验证结果:")
            for key, expected_value in expected.items():
                actual_value = result.get(key)
                status = "✅" if actual_value == expected_value else "❌"
                print(f"  {key}: {status} 期望='{expected_value}', 实际='{actual_value}'")
        else:
            print("❌ 解析失败")

def analyze_real_pdf_multiline():
    """分析真实PDF中的多行格式"""
    
    pdf_files = ['upload/sample01.pdf', 'upload/sample02.pdf']
    
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            continue
            
        print(f"\n=== 分析 {pdf_file} 中的多行产品 ===")
        
        with open(pdf_file, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            content = ""
            for page in reader.pages:
                content += page.extract_text()
        
        multiline_products = detect_and_parse_multiline_products(content)
        
        print(f"发现 {len(multiline_products)} 个多行产品:")
        
        for product in multiline_products:
            print(f"\n原始行 ({product['line_numbers']}):")
            for line in product['original_lines']:
                print(f"  '{line}'")
            
            parsed = product['parsed_product']
            print(f"解析结果:")
            for key, value in parsed.items():
                print(f"  {key}: '{value}'")

if __name__ == "__main__":
    test_multiline_parsing()
    analyze_real_pdf_multiline() 