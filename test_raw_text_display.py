#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import extract_pdf_content

def test_raw_text_display():
    """测试原始PDF文本显示功能"""
    pdf_path = 'upload/sample.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("=== 测试原始PDF文本显示 ===")
    
    # 测试1：提取原始文本（不添加页面分隔符）
    print("\n1. 提取原始PDF文本（无页面分隔符）：")
    raw_text = extract_pdf_content(pdf_path, add_page_markers=False)
    print(f"原始文本长度: {len(raw_text)} 字符")
    print("前500个字符:")
    print(raw_text[:500])
    
    # 测试2：提取带页面分隔符的文本（用于解析）
    print("\n2. 提取带页面分隔符的PDF文本（用于解析）：")
    parsed_text = extract_pdf_content(pdf_path, add_page_markers=True)
    print(f"解析文本长度: {len(parsed_text)} 字符")
    print("前500个字符:")
    print(parsed_text[:500])
    
    # 测试3：比较两种文本的差异
    print("\n3. 文本差异分析：")
    print(f"原始文本行数: {len(raw_text.split('\\n'))}")
    print(f"解析文本行数: {len(parsed_text.split('\\n'))}")
    
    # 检查是否包含页面分隔符
    if "=== PAGE" in parsed_text:
        print("✓ 解析文本包含页面分隔符")
    else:
        print("✗ 解析文本不包含页面分隔符")
    
    if "=== PAGE" in raw_text:
        print("✗ 原始文本不应该包含页面分隔符")
    else:
        print("✓ 原始文本不包含页面分隔符")
    
    # 测试4：显示原始文本的前几行
    print("\n4. 原始文本前20行:")
    lines = raw_text.split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:2d}: {repr(line)}")

if __name__ == "__main__":
    test_raw_text_display() 