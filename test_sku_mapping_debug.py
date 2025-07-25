#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from requests.sessions import Session

# 测试SKU映射功能
def test_sku_mapping():
    base_url = 'http://localhost:5000'
    
    # 创建session
    session = Session()
    
    print("=== 测试SKU映射功能 ===")
    
    # 1. 测试未登录状态访问get_sku_mappings
    print("\n1. 测试未登录状态访问get_sku_mappings")
    try:
        response = session.get(f'{base_url}/get_sku_mappings')
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试管理员登录
    print("\n2. 测试管理员登录")
    login_data = {'password': 'admin123'}
    try:
        response = session.post(f'{base_url}/admin_login', data=login_data)
        print(f"登录状态码: {response.status_code}")
        print(f"登录响应: {response.text[:200]}...")
        
        # 检查是否重定向到主页
        if response.status_code == 302:
            print("登录成功，重定向到主页")
        elif "密码错误" in response.text:
            print("密码错误")
            return
    except Exception as e:
        print(f"登录失败: {e}")
        return
    
    # 3. 登录后测试get_sku_mappings
    print("\n3. 登录后测试get_sku_mappings")
    try:
        response = session.get(f'{base_url}/get_sku_mappings')
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取映射数据: {data}")
        else:
            print(f"获取映射数据失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 4. 测试保存SKU映射
    print("\n4. 测试保存SKU映射")
    mapping_data = {
        'original_sku': 'TEST-SKU-001',
        'mapped_sku': 'MAPPED-SKU-001'
    }
    
    try:
        response = session.post(
            f'{base_url}/save_sku_mapping',
            json=mapping_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"保存状态码: {response.status_code}")
        print(f"保存响应: {response.text}")
        
        if response.status_code == 200:
            print("SKU映射保存成功")
        else:
            print(f"SKU映射保存失败: {response.text}")
    except Exception as e:
        print(f"保存请求失败: {e}")
    
    # 5. 再次获取映射数据验证保存
    print("\n5. 验证保存的映射数据")
    try:
        response = session.get(f'{base_url}/get_sku_mappings')
        if response.status_code == 200:
            data = response.json()
            print(f"验证映射数据: {data}")
            if 'TEST-SKU-001' in data.get('mappings', {}):
                print("✅ SKU映射保存验证成功")
            else:
                print("❌ SKU映射保存验证失败")
        else:
            print(f"验证失败: {response.text}")
    except Exception as e:
        print(f"验证请求失败: {e}")

if __name__ == '__main__':
    test_sku_mapping() 