#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from requests.sessions import Session
import time

def debug_mapping_page():
    """调试映射页面加载问题"""
    base_url = 'http://localhost:5000'
    session = Session()
    
    print("=== 调试SKU映射页面加载问题 ===")
    
    # 1. 先尝试访问SKU映射页面（应该重定向到登录）
    print("\n1. 未登录访问SKU映射页面")
    response = session.get(f'{base_url}/sku_mappings', allow_redirects=False)
    print(f"状态码: {response.status_code}")
    if response.status_code == 302:
        print(f"重定向到: {response.headers.get('Location')}")
    
    # 2. 管理员登录
    print("\n2. 管理员登录")
    login_data = {'password': 'admin123'}
    response = session.post(f'{base_url}/admin_login', data=login_data)
    print(f"登录状态码: {response.status_code}")
    
    if "密码错误" in response.text:
        print("❌ 密码错误")
        return
    elif response.status_code == 200 and "主页" in response.text:
        print("✅ 登录成功")
    
    # 3. 登录后访问SKU映射页面
    print("\n3. 登录后访问SKU映射页面")
    response = session.get(f'{base_url}/sku_mappings')
    print(f"页面状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ 页面访问成功")
        # 检查页面内容
        if "正在加载映射数据" in response.text:
            print("✅ 页面包含加载提示")
        if "loadMappingsData" in response.text:
            print("✅ 页面包含JavaScript函数")
    else:
        print("❌ 页面访问失败")
        return
    
    # 4. 模拟jQuery Ajax请求获取映射数据
    print("\n4. 模拟Ajax请求获取映射数据")
    
    # 模拟jQuery发送的Ajax请求头
    ajax_headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json',
        'Referer': f'{base_url}/sku_mappings'
    }
    
    print("发送Ajax请求...")
    start_time = time.time()
    
    try:
        response = session.get(f'{base_url}/get_sku_mappings', headers=ajax_headers, timeout=15)
        end_time = time.time()
        
        print(f"Ajax状态码: {response.status_code}")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ JSON解析成功: {data}")
                
                if data.get('success') and data.get('mappings'):
                    mapping_count = len(data['mappings'])
                    print(f"✅ 找到 {mapping_count} 个映射关系")
                    
                    # 显示前3个映射
                    for i, (orig, mapped) in enumerate(list(data['mappings'].items())[:3]):
                        print(f"  {i+1}. {orig} -> {mapped}")
                else:
                    print("ℹ️ 返回空映射数据")
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
        else:
            print(f"❌ Ajax请求失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Ajax请求超时")
    except Exception as e:
        print(f"❌ Ajax请求异常: {e}")
    
    # 5. 检查是否有其他依赖的API
    print("\n5. 检查OCCW SKUs API")
    try:
        response = session.get(f'{base_url}/get_occw_skus', timeout=10)
        print(f"OCCW SKUs状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"OCCW SKUs数量: {len(data.get('skus', []))}")
        else:
            print(f"OCCW SKUs失败: {response.text}")
    except Exception as e:
        print(f"OCCW SKUs异常: {e}")

if __name__ == '__main__':
    debug_mapping_page() 