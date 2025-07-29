#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语言切换功能
"""

import requests
import json

def test_language_switch():
    """测试语言切换功能"""
    base_url = "http://127.0.0.1:5000"
    
    # 测试不同语言
    languages = ['zh', 'en', 'fr']
    
    for lang in languages:
        print(f"\n=== 测试语言: {lang} ===")
        
        # 设置语言
        session = requests.Session()
        session.get(f"{base_url}/set_language/{lang}")
        
        # 测试主页
        try:
            response = session.get(f"{base_url}/")
            if response.status_code == 200:
                print(f"✅ 主页加载成功")
                
                # 检查是否包含英文内容（如果设置为英文）
                if lang == 'en':
                    if 'PDF Import Quote' in response.text:
                        print("✅ 英文翻译正确显示")
                    else:
                        print("⚠️  英文翻译可能有问题")
                elif lang == 'fr':
                    if 'Import PDF Devis' in response.text:
                        print("✅ 法文翻译正确显示")
                    else:
                        print("⚠️  法文翻译可能有问题")
                else:
                    if 'PDF导入报价单' in response.text:
                        print("✅ 中文内容正确显示")
                    else:
                        print("⚠️  中文内容可能有问题")
            else:
                print(f"❌ 主页加载失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🌐 测试语言切换功能")
    print("请确保Flask应用正在运行 (python app.py)")
    print("=" * 50)
    
    test_language_switch()
    
    print("\n🎯 测试完成！")
    print("如果看到✅，说明多语言化工作正常")
    print("如果看到⚠️，说明可能需要进一步检查翻译配置") 