import requests
import json

def test_upload():
    """测试上传PDF文件"""
    
    # 上传PDF文件
    with open('upload/sample.pdf', 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:5000/upload_quotation', files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            products = data['products']
            print(f"成功解析 {len(products)} 个产品")
            
            # 检查序号1是否存在
            seq_1_found = False
            for product in products:
                if product['seq_num'] == '1':
                    seq_1_found = True
                    print(f"找到序号1: {product}")
                    break
            
            if not seq_1_found:
                print("警告：没有找到序号1的产品")
            
            # 检查序号连续性
            seq_nums = []
            for product in products:
                seq_str = product['seq_num']
                if seq_str.startswith('*'):
                    seq_str = seq_str[1:]
                try:
                    seq_nums.append(int(seq_str))
                except ValueError:
                    print(f"无法解析序号: {seq_str}")
            
            seq_nums.sort()
            print(f"序号范围: {min(seq_nums)} - {max(seq_nums)}")
            
            # 检查缺失的序号
            missing_seqs = []
            for i in range(min(seq_nums), max(seq_nums) + 1):
                if i not in seq_nums:
                    missing_seqs.append(i)
            
            if missing_seqs:
                print(f"缺失的序号: {missing_seqs}")
            else:
                print("序号连续")
            
            # 显示前5个产品
            print("\n前5个产品:")
            for i, product in enumerate(products[:5]):
                print(f"{i+1}. 序号:{product['seq_num']}, SKU:{product['sku']}, 用户编码:{product['user_code']}, 描述:{product['description']}")
            
            # 检查SKU生成规则
            print("\nSKU生成规则检查:")
            cabinet_count = 0
            accessory_count = 0
            other_count = 0
            
            for product in products:
                sku = product['sku']
                if '-PLY-' in sku:
                    cabinet_count += 1
                elif product['door_color'] in sku and not '-PLY-' in sku:
                    accessory_count += 1
                else:
                    other_count += 1
            
            print(f"Cabinet产品 (包含-PLY-): {cabinet_count}")
            print(f"Accessory产品 (花色-用户编码): {accessory_count}")
            print(f"其他产品: {other_count}")
            
        else:
            print(f"解析失败: {data.get('error')}")
    else:
        print(f"请求失败: {response.status_code}")

if __name__ == "__main__":
    test_upload() 