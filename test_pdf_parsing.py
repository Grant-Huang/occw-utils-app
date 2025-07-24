#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_content, parse_quotation_pdf

def test_pdf_parsing():
    """测试PDF解析功能"""
    pdf_path = 'upload/sample.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("=== 测试PDF内容提取 ===")
    pdf_content = extract_pdf_content(pdf_path)
    print(f"PDF内容长度: {len(pdf_content)} 字符")
    
    # 显示前500个字符
    print("\n前500个字符:")
    print(pdf_content[:500])
    
    # 显示包含页面分隔符的部分
    page_markers = pdf_content.split('=== PAGE')
    print(f"\n找到 {len(page_markers)} 个页面")
    
    for i, page in enumerate(page_markers[1:3]):  # 只显示前2页
        print(f"\n=== 页面 {i+1} 内容 ===")
        print(page[:300] + "..." if len(page) > 300 else page)
    
    print("\n=== 测试产品解析 ===")
    products = parse_quotation_pdf(pdf_content)
    
    print(f"\n总共解析到 {len(products)} 个产品")
    
    # 显示所有产品的序号
    seq_nums = [p['seq_num'] for p in products]
    print(f"序号列表: {seq_nums}")
    
    # 检查缺失的序号
    if seq_nums:
        seq_nums_int = [int(s) for s in seq_nums if s.isdigit()]
        if seq_nums_int:
            min_seq = min(seq_nums_int)
            max_seq = max(seq_nums_int)
            missing = [i for i in range(min_seq, max_seq + 1) if i not in seq_nums_int]
            if missing:
                print(f"缺失的序号: {missing}")
            else:
                print("序号连续，无缺失")
    
    # 显示前5个产品的详细信息
    print("\n前5个产品详情:")
    for i, product in enumerate(products[:5]):
        print(f"{i+1}. {product}")

if __name__ == "__main__":
    test_pdf_parsing() 