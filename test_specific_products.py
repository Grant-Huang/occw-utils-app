import requests
import json

def test_specific_products():
    """测试序号30和31的产品"""
    
    # 上传PDF文件
    with open('upload/sample.pdf', 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:5000/upload_quotation', files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            products = data['products']
            print(f"成功解析 {len(products)} 个产品")
            
            # 查找序号30和31的产品
            seq_30_found = False
            seq_31_found = False
            
            for product in products:
                if product['seq_num'] == '30':
                    seq_30_found = True
                    print(f"找到序号30: {product}")
                elif product['seq_num'] == '31':
                    seq_31_found = True
                    print(f"找到序号31: {product}")
            
            if not seq_30_found:
                print("警告：没有找到序号30的产品")
            if not seq_31_found:
                print("警告：没有找到序号31的产品")
            
            # 显示所有3DB30相关的产品
            print("\n所有3DB30相关的产品:")
            for product in products:
                if '3DB30' in product['user_code'] or '3DB30' in product['sku']:
                    print(f"  {product}")
            
            # 检查*号处理
            print("\n包含*号的产品:")
            for product in products:
                if '*' in product['description']:
                    print(f"  {product}")
            
        else:
            print(f"解析失败: {data.get('error')}")
    else:
        print(f"请求失败: {response.status_code}")

if __name__ == "__main__":
    test_specific_products() 