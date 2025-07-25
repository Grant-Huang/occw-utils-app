#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_admin_api():
    """测试admin API是否正常工作"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("=== 测试SKU映射API ===")
    
    # 测试未登录时的访问
    print("\n1. 测试未登录时的访问:")
    try:
        response = requests.get(f"{base_url}/get_sku_mappings", 
                              headers={'Content-Type': 'application/json'})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 401:
            print("✅ 正确返回401状态码，无权限访问")
        else:
            print("❌ 应该返回401状态码")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试登录
    print("\n2. 测试管理员登录:")
    session = requests.Session()
    
    login_data = {
        'password': 'admin123'  # 默认密码
    }
    
    try:
        login_response = session.post(f"{base_url}/admin_login", 
                                    data=login_data)
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200 or login_response.status_code == 302:
            print("✅ 登录成功")
            
            # 测试登录后的访问
            print("\n3. 测试登录后的API访问:")
            mappings_response = session.get(f"{base_url}/get_sku_mappings",
                                          headers={'Content-Type': 'application/json'})
            print(f"状态码: {mappings_response.status_code}")
            
            if mappings_response.status_code == 200:
                try:
                    data = mappings_response.json()
                    print(f"✅ API正常工作")
                    print(f"映射数量: {len(data.get('mappings', {}))}")
                    print(f"映射数据示例: {list(data.get('mappings', {}).items())[:3]}")
                except Exception as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"响应内容: {mappings_response.text}")
            else:
                print(f"❌ API访问失败，状态码: {mappings_response.status_code}")
                print(f"响应内容: {mappings_response.text}")
        else:
            print(f"❌ 登录失败，状态码: {login_response.status_code}")
            print(f"响应内容: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")

def test_local_data():
    """测试本地数据文件"""
    
    print("\n=== 测试本地数据文件 ===")
    
    # 检查数据文件是否存在
    data_files = [
        'data/sku_mappings.json',
        'data/occw_prices.json',
        'data/standard_prices.json',
        'data/sku_rules.json'
    ]
    
    for file_path in data_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ {file_path}: {len(data)} 项数据")
        except FileNotFoundError:
            print(f"❌ {file_path}: 文件不存在")
        except Exception as e:
            print(f"❌ {file_path}: 读取失败 - {e}")

if __name__ == "__main__":
    print("请确保Flask应用正在运行 (python app.py)")
    print("如果应用未运行，请先启动应用再运行此测试\n")
    
    test_local_data()
    
    # 询问是否测试API
    user_input = input("\n是否测试API？(需要应用正在运行) [y/N]: ")
    if user_input.lower() in ['y', 'yes']:
        test_admin_api()
    else:
        print("跳过API测试") 