#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PyPDF2

def test_pdf_raw_extraction():
    """测试PDF原始文本提取，特别关注换行"""
    pdf_path = 'upload/sample.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("=== 测试PDF原始文本提取 ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"PDF页数: {len(pdf_reader.pages)}")
            
            for page_num, page in enumerate(pdf_reader.pages):
                print(f"\n=== 第 {page_num + 1} 页原始文本 ===")
                page_text = page.extract_text()
                
                # 显示原始文本（包含换行符）
                print("原始文本（显示换行符）:")
                print(repr(page_text))
                
                print("\n格式化文本:")
                print(page_text)
                
                # 按行分割并显示
                lines = page_text.split('\n')
                print(f"\n按换行符分割后的行数: {len(lines)}")
                print("前10行:")
                for i, line in enumerate(lines[:10]):
                    print(f"{i+1:2d}: '{line}'")
                
                # 只显示前2页
                if page_num >= 1:
                    break
                    
    except Exception as e:
        print(f"PDF解析失败: {e}")

def test_improved_extraction():
    """测试改进的PDF文本提取方法"""
    pdf_path = 'upload/sample.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print("\n=== 测试改进的PDF文本提取 ===")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                print(f"\n=== 第 {page_num + 1} 页改进提取 ===")
                
                # 尝试不同的文本提取方法
                page_text = page.extract_text()
                
                # 方法1：保持原始换行
                print("方法1 - 保持原始换行:")
                print(page_text)
                
                # 方法2：规范化换行
                normalized_text = page_text.replace('\r\n', '\n').replace('\r', '\n')
                print("\n方法2 - 规范化换行:")
                print(normalized_text)
                
                # 方法3：按空格分割，然后重新组合
                words = page_text.split()
                print("\n方法3 - 按单词分割:")
                print("单词列表:", words[:20])  # 只显示前20个单词
                
                # 只显示前2页
                if page_num >= 1:
                    break
                    
    except Exception as e:
        print(f"PDF解析失败: {e}")

if __name__ == "__main__":
    test_pdf_raw_extraction()
    test_improved_extraction() 