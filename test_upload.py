#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os

def test_sales_upload():
    """测试销售数据上传"""
    try:
        # 检查文件是否存在
        filepath = 'upload/销售订单.xlsx'
        if not os.path.exists(filepath):
            print(f"错误: 找不到文件 {filepath}")
            return
        
        print("正在测试销售数据上传...")
        
        # 准备文件上传
        with open(filepath, 'rb') as f:
            files = {'file': ('销售订单.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            # 发送POST请求
            response = requests.post('http://localhost:5000/upload_sales_data', files=files)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ 上传成功!")
                print(f"分析数据包含:")
                analysis_data = data['data']
                print(f"- 销售员数量: {len(analysis_data['sales_person_analysis'])}")
                print(f"- 客户数量: {len(analysis_data['customer_analysis'])}")
                print(f"- 时间趋势数据点: {len(analysis_data['trend_data']['labels'])}")
                print(f"- 转化率数据点: {len(analysis_data['conversion_data']['labels'])}")
            else:
                print(f"❌ 上传失败: {data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sales_upload() 