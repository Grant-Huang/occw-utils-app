#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_ajax_without_login():
    """测试未登录状态下的Ajax请求"""
    base_url = 'http://localhost:5000'
    
    print("=== 测试未登录Ajax请求 ===")
    
    # 模拟jQuery Ajax请求的头部
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f'{base_url}/get_sku_mappings', headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 401:
            print("✅ 正确返回401状态码")
            try:
                data = response.json()
                print(f"JSON响应: {data}")
            except:
                print("❌ 无法解析JSON响应")
        else:
            print("❌ 未返回401状态码")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_normal_browser_request():
    """测试普通浏览器请求"""
    base_url = 'http://localhost:5000'
    
    print("\n=== 测试普通浏览器请求 ===")
    
    # 模拟普通浏览器请求的头部
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(f'{base_url}/get_sku_mappings', headers=headers, allow_redirects=False)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 302:
            print("✅ 正确重定向到登录页面")
            print(f"重定向到: {response.headers.get('Location', 'Unknown')}")
        else:
            print("❌ 未正确重定向")
            print(f"响应内容前200字符: {response.text[:200]}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == '__main__':
    test_ajax_without_login()
    test_normal_browser_request() 