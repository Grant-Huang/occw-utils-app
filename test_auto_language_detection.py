#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动语言检测功能
"""

import requests
import json

def test_auto_language_detection():
    """测试自动语言检测功能"""
    base_url = "http://127.0.0.1:5000"
    
    print("🌐 测试自动语言检测功能")
    print("=" * 50)
    
    # 测试不同的Accept-Language头
    test_cases = [
        {
            'name': '中文用户',
            'headers': {'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'},
            'expected': 'zh'
        },
        {
            'name': '英文用户',
            'headers': {'Accept-Language': 'en-US,en;q=0.9'},
            'expected': 'en'
        },
        {
            'name': '法文用户',
            'headers': {'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'},
            'expected': 'fr'
        },
        {
            'name': '混合语言用户（英文优先）',
            'headers': {'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8'},
            'expected': 'en'
        },
        {
            'name': '无语言偏好',
            'headers': {},
            'expected': 'zh'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 测试: {test_case['name']}")
        print(f"   Headers: {test_case['headers']}")
        
        try:
            # 创建新的session来避免缓存
            session = requests.Session()
            
            # 发送请求
            response = session.get(f"{base_url}/", headers=test_case['headers'])
            
            if response.status_code == 200:
                print(f"   ✅ 请求成功")
                
                # 检查页面内容来判断语言
                content = response.text
                if test_case['expected'] == 'en':
                    if 'PDF Import Quote' in content:
                        print(f"   ✅ 语言检测正确: 英文")
                    else:
                        print(f"   ⚠️  语言检测可能有问题: 期望英文，但页面内容不匹配")
                elif test_case['expected'] == 'fr':
                    if 'Import PDF Devis' in content:
                        print(f"   ✅ 语言检测正确: 法文")
                    else:
                        print(f"   ⚠️  语言检测可能有问题: 期望法文，但页面内容不匹配")
                else:
                    if 'PDF导入报价单' in content:
                        print(f"   ✅ 语言检测正确: 中文")
                    else:
                        print(f"   ⚠️  语言检测可能有问题: 期望中文，但页面内容不匹配")
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")

def test_language_switching():
    """测试语言切换功能"""
    base_url = "http://127.0.0.1:5000"
    
    print(f"\n🔄 测试语言切换功能")
    print("=" * 50)
    
    session = requests.Session()
    
    # 测试切换到英文
    try:
        response = session.get(f"{base_url}/set_language/en")
        if response.status_code == 200:
            print("✅ 切换到英文成功")
            
            # 检查主页是否显示英文
            response = session.get(f"{base_url}/")
            if 'PDF Import Quote' in response.text:
                print("✅ 英文界面显示正确")
            else:
                print("⚠️  英文界面可能有问题")
        else:
            print(f"❌ 切换到英文失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 语言切换测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试自动语言检测功能")
    print("请确保Flask应用正在运行 (python app.py)")
    print("=" * 60)
    
    test_auto_language_detection()
    test_language_switching()
    
    print("\n🎯 测试完成！")
    print("如果看到✅，说明自动语言检测工作正常")
    print("如果看到⚠️，说明可能需要进一步检查配置") 