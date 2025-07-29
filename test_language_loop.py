#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语言检测循环问题是否已修复
"""

import requests
import time

def test_language_detection():
    """测试语言检测是否会导致无限循环"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 测试语言检测循环问题")
    print("=" * 50)
    
    # 测试1: 英文用户访问
    print("📝 测试1: 英文用户访问")
    session = requests.Session()
    
    # 设置英文Accept-Language头
    headers = {'Accept-Language': 'en-US,en;q=0.9,zh;q=0.8'}
    
    start_time = time.time()
    max_requests = 5  # 最多允许5次请求
    
    for i in range(max_requests):
        try:
            response = session.get(f"{base_url}/", headers=headers, timeout=10)
            print(f"   请求 {i+1}: 状态码 {response.status_code}")
            
            if response.status_code == 200:
                # 检查页面内容是否包含英文
                if 'PDF Import Quote' in response.text or 'Manual Create Quote' in response.text:
                    print("   ✅ 页面正确显示英文内容")
                    break
                elif 'PDF导入报价单' in response.text or '手动创建报价单' in response.text:
                    print("   ⚠️  页面仍显示中文内容")
                else:
                    print("   ❓ 页面内容不明确")
            
            # 等待一下再发送下一个请求
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
            break
    
    elapsed_time = time.time() - start_time
    print(f"   总耗时: {elapsed_time:.2f}秒")
    
    if elapsed_time > 10:
        print("   ⚠️  响应时间较长，可能存在性能问题")
    else:
        print("   ✅ 响应时间正常")
    
    print()
    
    # 测试2: 法文用户访问
    print("📝 测试2: 法文用户访问")
    session2 = requests.Session()
    
    # 设置法文Accept-Language头
    headers2 = {'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'}
    
    start_time2 = time.time()
    
    for i in range(max_requests):
        try:
            response = session2.get(f"{base_url}/", headers=headers2, timeout=10)
            print(f"   请求 {i+1}: 状态码 {response.status_code}")
            
            if response.status_code == 200:
                # 检查页面内容是否包含法文
                if 'Importation PDF' in response.text or 'Création Manuelle' in response.text:
                    print("   ✅ 页面正确显示法文内容")
                    break
                elif 'PDF导入报价单' in response.text or '手动创建报价单' in response.text:
                    print("   ⚠️  页面仍显示中文内容")
                else:
                    print("   ❓ 页面内容不明确")
            
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
            break
    
    elapsed_time2 = time.time() - start_time2
    print(f"   总耗时: {elapsed_time2:.2f}秒")
    
    print()
    
    # 测试3: 检查是否有无限重定向
    print("📝 测试3: 检查无限重定向")
    
    try:
        response = requests.get(f"{base_url}/", headers=headers, allow_redirects=False, timeout=5)
        if response.status_code in [301, 302, 303, 307, 308]:
            print("   ⚠️  检测到重定向，需要进一步检查")
        else:
            print("   ✅ 没有检测到重定向")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print()
    print("🎯 测试完成！")
    print("如果看到✅，说明语言检测工作正常")
    print("如果看到⚠️，说明可能需要进一步优化")
    print("如果看到❌，说明存在问题需要修复")

if __name__ == "__main__":
    test_language_detection() 