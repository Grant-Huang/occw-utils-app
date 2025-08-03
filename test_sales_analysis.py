#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

def test_sales_analysis():
    """测试销售分析功能"""
    try:
        # 读取样本数据
        filepath = 'upload/销售订单.xlsx'
        if not os.path.exists(filepath):
            print(f"错误: 找不到文件 {filepath}")
            return
        
        print("正在读取Excel文件...")
        df = pd.read_excel(filepath)
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        
        # 数据预处理
        print("\n正在预处理数据...")
        df['订单日期'] = pd.to_datetime(df['订单日期'])
        df['总计'] = pd.to_numeric(df['总计'], errors='coerce').fillna(0)
        df['毛利率（%）'] = pd.to_numeric(df['毛利率（%）'], errors='coerce').fillna(0)
        
        # 区分订单和报价单
        df['is_order'] = df['订单状态'].str.contains('销售订单', na=False)
        df['is_quotation'] = df['订单状态'].str.contains('报价单', na=False)
        
        print(f"订单数量: {df['is_order'].sum()}")
        print(f"报价单数量: {df['is_quotation'].sum()}")
        print(f"总记录数: {len(df)}")
        
        # 销售员业绩分析
        print("\n正在分析销售员业绩...")
        sales_person_stats = {}
        
        for _, row in df.iterrows():
            sales_person = row['销售人员']
            amount = row['总计']
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            profit_margin = row['毛利率（%）']
            
            if sales_person not in sales_person_stats:
                sales_person_stats[sales_person] = {
                    'total_amount': 0,
                    'order_amount': 0,
                    'quotation_amount': 0,
                    'profit_margins': []
                }
            
            sales_person_stats[sales_person]['total_amount'] += amount
            
            if is_order:
                sales_person_stats[sales_person]['order_amount'] += amount
            elif is_quotation:
                sales_person_stats[sales_person]['quotation_amount'] += amount
            
            if profit_margin > 0:
                sales_person_stats[sales_person]['profit_margins'].append(profit_margin)
        
        # 显示销售员业绩
        print("\n销售员业绩分析:")
        for sales_person, stats in sales_person_stats.items():
            total_amount = stats['total_amount']
            order_amount = stats['order_amount']
            quotation_amount = stats['quotation_amount']
            
            conversion_rate = order_amount / total_amount if total_amount > 0 else 0
            avg_profit_margin = sum(stats['profit_margins']) / len(stats['profit_margins']) if stats['profit_margins'] else 0
            
            print(f"\n{sales_person}:")
            print(f"  总金额: ${total_amount:,.2f}")
            print(f"  订单金额: ${order_amount:,.2f}")
            print(f"  报价单金额: ${quotation_amount:,.2f}")
            print(f"  转化率: {conversion_rate*100:.1f}%")
            print(f"  平均毛利率: {avg_profit_margin:.1f}%")
        
        # 客户订单分析
        print("\n正在分析客户订单...")
        customer_stats = {}
        
        for _, row in df.iterrows():
            customer = row['客户']
            amount = row['总计']
            is_order = row['is_order']
            is_quotation = row['is_quotation']
            
            if customer not in customer_stats:
                customer_stats[customer] = {
                    'order_count': 0,
                    'quotation_count': 0,
                    'order_amount': 0,
                    'quotation_amount': 0
                }
            
            if is_order:
                customer_stats[customer]['order_count'] += 1
                customer_stats[customer]['order_amount'] += amount
            elif is_quotation:
                customer_stats[customer]['quotation_count'] += 1
                customer_stats[customer]['quotation_amount'] += amount
        
        # 显示前10个客户的订单情况
        print("\n客户订单分析 (前10名):")
        sorted_customers = sorted(customer_stats.items(), 
                                key=lambda x: x[1]['order_amount'] + x[1]['quotation_amount'], 
                                reverse=True)
        
        for i, (customer, stats) in enumerate(sorted_customers[:10]):
            total_amount = stats['order_amount'] + stats['quotation_amount']
            print(f"\n{i+1}. {customer}:")
            print(f"   订单数量: {stats['order_count']}")
            print(f"   报价单数量: {stats['quotation_count']}")
            print(f"   总订单数: {stats['order_count'] + stats['quotation_count']}")
            print(f"   订单金额: ${stats['order_amount']:,.2f}")
            print(f"   报价单金额: ${stats['quotation_amount']:,.2f}")
            print(f"   总金额: ${total_amount:,.2f}")
        
        print("\n✅ 销售分析测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sales_analysis() 