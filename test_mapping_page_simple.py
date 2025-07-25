#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from requests.sessions import Session
import time

def test_simple_mapping():
    """测试简化的映射页面功能"""
    base_url = 'http://localhost:5000'
    session = Session()
    
    print("=== 测试简化映射页面 ===")
    
    # 登录
    login_data = {'password': 'admin123'}
    session.post(f'{base_url}/admin_login', data=login_data)
    
    # 测试直接访问映射数据
    print("测试获取映射数据...")
    start_time = time.time()
    
    ajax_headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
    }
    
    response = session.get(f'{base_url}/get_sku_mappings', headers=ajax_headers)
    end_time = time.time()
    
    print(f"响应时间: {end_time - start_time:.2f}秒")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        mappings = data.get('mappings', {})
        print(f"映射数量: {len(mappings)}")
        
        # 测试单个价格查询
        if mappings:
            first_sku = list(mappings.values())[0]
            print(f"\n测试获取单个价格: {first_sku}")
            
            price_start = time.time()
            price_response = session.get(f'{base_url}/get_occw_price', params={'sku': first_sku})
            price_end = time.time()
            
            print(f"价格查询时间: {price_end - price_start:.2f}秒")
            print(f"价格响应: {price_response.text}")

if __name__ == '__main__':
    test_simple_mapping() 