#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import time

def test_sku_mapping_apis():
    """测试重写后的SKU映射管理页面相关API"""
    
    print("=== 测试重写后的SKU映射管理页面 ===\n")
    
    base_url = "http://localhost:5000"
    
    # 创建session以保持登录状态
    session = requests.Session()
    
    # 1. 测试管理员登录
    print("1. 测试管理员登录...")
    login_data = {"password": "admin123"}
    
    try:
        response = session.post(f"{base_url}/admin_login", data=login_data, timeout=10)
        if response.status_code == 200 or "admin" in response.text.lower():
            print("✅ 管理员登录成功")
        else:
            print("❌ 管理员登录失败")
            return
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 2. 测试获取SKU映射关系
    print("\n2. 测试获取SKU映射关系...")
    try:
        response = session.get(f"{base_url}/get_sku_mappings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                mappings = data.get('mappings', {})
                print(f"✅ 获取映射关系成功，共 {len(mappings)} 个")
                if mappings:
                    print(f"📋 示例映射: {list(mappings.items())[:3]}")
            else:
                print(f"❌ 获取映射关系失败: {data.get('error')}")
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取映射关系异常: {e}")
    
    # 3. 测试获取OCCW SKU列表
    print("\n3. 测试获取OCCW SKU列表...")
    try:
        response = session.get(f"{base_url}/get_occw_skus", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                skus = data.get('skus', [])
                print(f"✅ 获取SKU列表成功，共 {len(skus)} 个")
                if skus:
                    print(f"📋 前5个SKU: {skus[:5]}")
            else:
                print(f"❌ 获取SKU列表失败: {data.get('error')}")
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取SKU列表异常: {e}")
    
    # 4. 测试获取单个SKU价格（使用新的API）
    print("\n4. 测试获取单个SKU价格...")
    test_skus = ["2DB30-PLY-BSS", "WF330-PLY-BSS", "TEST-SKU"]
    
    for sku in test_skus:
        try:
            response = session.get(f"{base_url}/get_occw_price", params={"sku": sku}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    price = data.get('price', 0)
                    product_info = data.get('product_info', {})
                    mapped_sku = data.get('mapped_sku')
                    
                    print(f"  🔍 SKU: {sku}")
                    print(f"     价格: ${price:.2f}")
                    if mapped_sku:
                        print(f"     映射到: {mapped_sku}")
                    if product_info:
                        print(f"     产品信息: {product_info}")
                else:
                    print(f"  ❌ SKU {sku}: {data.get('error')}")
            else:
                print(f"  ❌ SKU {sku}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ SKU {sku}: 异常 {e}")
    
    # 5. 测试新增SKU映射
    print("\n5. 测试新增SKU映射...")
    test_mapping = {
        "original_sku": "TEST-ORIGINAL-SKU", 
        "mapped_sku": "2DB30-PLY-BSS"
    }
    
    try:
        response = session.post(
            f"{base_url}/save_sku_mapping",
            json=test_mapping,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 新增SKU映射成功")
            else:
                print(f"❌ 新增SKU映射失败: {data.get('error')}")
        else:
            print(f"❌ 新增SKU映射失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 新增SKU映射异常: {e}")
    
    # 6. 测试删除SKU映射
    print("\n6. 测试删除SKU映射...")
    try:
        response = session.post(
            f"{base_url}/delete_sku_mapping",
            json={"original_sku": "TEST-ORIGINAL-SKU"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 删除SKU映射成功")
            else:
                print(f"❌ 删除SKU映射失败: {data.get('error')}")
        else:
            print(f"❌ 删除SKU映射失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 删除SKU映射异常: {e}")
    
    # 7. 测试导出SKU映射
    print("\n7. 测试导出SKU映射...")
    try:
        response = session.get(f"{base_url}/export_sku_mappings", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                export_time = data.get('export_time', '')
                print(f"✅ 导出SKU映射成功，共 {count} 个，导出时间: {export_time}")
            else:
                print(f"❌ 导出SKU映射失败: {data.get('error')}")
        else:
            print(f"❌ 导出SKU映射失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 导出SKU映射异常: {e}")
    
    # 8. 测试页面访问
    print("\n8. 测试SKU映射管理页面访问...")
    try:
        response = session.get(f"{base_url}/sku_mappings", timeout=10)
        if response.status_code == 200:
            if "SKU映射管理" in response.text:
                print("✅ SKU映射管理页面访问成功")
            else:
                print("❌ 页面内容异常")
        else:
            print(f"❌ 页面访问失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 页面访问异常: {e}")
    
    print("\n=== 测试完成 ===")

def check_app_running():
    """检查应用是否正在运行"""
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        return True
    except:
        return False

if __name__ == "__main__":
    print("检查应用是否运行中...")
    
    if not check_app_running():
        print("❌ 应用未运行，请先启动应用: python app.py")
        sys.exit(1)
    
    print("✅ 应用正在运行，开始测试...\n")
    
    # 等待一下确保应用完全启动
    time.sleep(2)
    
    test_sku_mapping_apis() 