#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_content, parse_quotation_pdf

def test_simple_parsing():
    """简单测试PDF解析功能"""
    pdf_path = 'upload/sample.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("=== 简单PDF解析测试 ===")
    
    # 提取PDF内容
    pdf_content = extract_pdf_content(pdf_path)
    print(f"PDF内容长度: {len(pdf_content)} 字符")
    
    # 解析产品
    products = parse_quotation_pdf(pdf_content)
    
    print(f"\n总共解析到 {len(products)} 个产品")
    
    # 显示所有产品的序号
    if products:
        seq_nums = [p['seq_num'] for p in products]
        print(f"序号列表: {seq_nums}")
        
        # 检查缺失的序号
        seq_nums_int = [int(s) for s in seq_nums if s.isdigit()]
        if seq_nums_int:
            min_seq = min(seq_nums_int)
            max_seq = max(seq_nums_int)
            missing = [i for i in range(min_seq, max_seq + 1) if i not in seq_nums_int]
            if missing:
                print(f"缺失的序号: {missing}")
            else:
                print("序号连续，无缺失")
        
        # 显示前10个产品的基本信息
        print("\n前10个产品:")
        for i, product in enumerate(products[:10]):
            print(f"{i+1}. 序号:{product['seq_num']} SKU:{product['sku']} 数量:{product['qty']} 价格:{product['unit_price']}")
    else:
        print("未解析到任何产品")

if __name__ == "__main__":
    test_simple_parsing() 