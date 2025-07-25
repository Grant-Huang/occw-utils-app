#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PyPDF2
import re
import os

def analyze_pdf_multiline_format():
    """分析PDF中的多行产品格式"""
    
    pdf_files = ['upload/sample01.pdf', 'upload/sample02.pdf']
    
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            print(f"文件不存在: {pdf_file}")
            continue
            
        print(f"\n=== 分析 {pdf_file} ===")
        
        with open(pdf_file, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text()
        
        lines = full_text.split('\n')
        
        # 寻找可能的多行产品格式
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 寻找包含"FOR"且较短的行（可能是分割后的产品编码）
            if 'FOR' in line and len(line) < 30:
                print(f"\n可能的多行格式 (行 {i}):")
                print(f"  当前行: '{line}'")
                
                # 检查前后几行
                context_start = max(0, i-2)
                context_end = min(len(lines), i+3)
                
                for j in range(context_start, context_end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}行 {j}: '{lines[j].strip()}'")
                    
            # 寻找以字母开头但包含数字的行（可能是分割后的产品信息）
            elif re.match(r'^[A-Z]+\d+', line) and len(line) < 50:
                # 检查下一行是否包含价格
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.search(r'\d+\.\d{2}', next_line):
                        print(f"\n可能的多行格式 (行 {i}):")
                        print(f"  产品编码行: '{line}'")
                        print(f"  价格行: '{next_line}'")
                        
                        # 显示更多上下文
                        context_start = max(0, i-1)
                        context_end = min(len(lines), i+3)
                        
                        for j in range(context_start, context_end):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}行 {j}: '{lines[j].strip()}'")

def simulate_multiline_case():
    """模拟用户描述的三行情况"""
    print("\n=== 模拟用户描述的情况 ===")
    
    # 用户描述的例子
    test_lines = [
        "WF330 FOR",
        "BASE19 Base Accessory 30.00 1WF330 FOR", 
        "BASE"
    ]
    
    print("原始三行:")
    for i, line in enumerate(test_lines):
        print(f"  行 {i+1}: '{line}'")
    
    # 尝试解析这三行
    print("\n解析结果:")
    
    # 合并三行
    merged_line = " ".join(test_lines)
    print(f"合并后: '{merged_line}'")
    
    # 尝试提取信息
    # WF330 FOR BASE19 Base Accessory 30.00 1WF330 FOR BASE
    parts = merged_line.split()
    print(f"分割后: {parts}")
    
    # 根据用户描述的格式解析
    if len(parts) >= 6:
        # 寻找价格位置
        price_index = -1
        for i, part in enumerate(parts):
            if re.match(r'^\d+\.\d{2}$', part):
                price_index = i
                break
        
        if price_index > 0:
            # 重构产品信息
            # WF330 FOR BASE (前面部分) + 19 (序号) + Base Accessory (描述) + 30.00 (价格) + 1 (数量) + WF330 FOR BASE (制造编码)
            
            # 找到序号位置 (应该在第一个用户编码后)
            user_code_parts = []
            seq_num = None
            description_parts = []
            
            # 重新分析
            # 从开头找到数字，那就是序号的开始
            for i, part in enumerate(parts):
                if re.match(r'^\d+', part):  # 找到第一个以数字开头的部分
                    # 提取序号
                    seq_match = re.match(r'^(\d+)(.*)$', part)
                    if seq_match:
                        seq_num = seq_match.group(1)
                        remaining = seq_match.group(2)
                        
                        # 用户编码是前面的部分
                        user_code_parts = parts[:i]
                        if remaining:
                            description_parts = [remaining] + parts[i+1:price_index]
                        else:
                            description_parts = parts[i+1:price_index]
                        break
            
            if seq_num and user_code_parts:
                user_code = " ".join(user_code_parts)
                description = " ".join(description_parts)
                price = parts[price_index]
                
                # 后面的部分应该包含数量和制造编码
                after_price = parts[price_index+1:]
                qty = "1"
                manuf_code = user_code  # 默认和用户编码相同
                
                if after_price:
                    # 寻找数量
                    qty_match = re.match(r'^(\d+)', after_price[0])
                    if qty_match:
                        qty = qty_match.group(1)
                        # 剩余部分是制造编码
                        remaining_after_qty = after_price[0][len(qty):]
                        if remaining_after_qty:
                            manuf_code = remaining_after_qty + " " + " ".join(after_price[1:])
                        else:
                            manuf_code = " ".join(after_price[1:])
                
                print(f"\n解析出的产品信息:")
                print(f"  用户编码: '{user_code}'")
                print(f"  序号: '{seq_num}'")
                print(f"  描述: '{description}'")
                print(f"  总价: '{price}'")
                print(f"  数量: '{qty}'")
                print(f"  制造编码: '{manuf_code}'")
                
                # 按用户建议，提取第一个词作为简化编码
                first_word = user_code.split()[0] if user_code.split() else user_code
                print(f"  简化编码 (第一个词): '{first_word}'")

if __name__ == "__main__":
    analyze_pdf_multiline_format()
    simulate_multiline_case() 