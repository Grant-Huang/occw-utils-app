import PyPDF2
import re

def debug_missing_products():
    """调试缺失的序号30和31的产品"""
    
    pdf_path = "upload/sample.pdf"
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    lines = text.split('\n')
    
    print("=== 查找序号30和31的产品行 ===")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 查找包含序号30或31的行
        if '30' in line or '31' in line:
            print(f"第{i}行: {line}")
            
            # 检查是否包含3DB30
            if '3DB30' in line:
                print(f"  包含3DB30，检查格式...")
                
                # 检查是否以数字开头
                if re.match(r'^[0-9]', line):
                    print(f"  以数字开头，应该被识别")
                    
                    # 解析产品行
                    parts = line.split()
                    if len(parts) >= 4:
                        print(f"  分割结果: {parts}")
                        
                        # 查找价格
                        price_index = -1
                        for j, part in enumerate(parts):
                            if re.match(r'^\d+,?\d*\.\d{2}$', part):
                                price_index = j
                                break
                        
                        if price_index > 0:
                            user_code = parts[0]
                            seq_num = parts[1]
                            description = ' '.join(parts[2:price_index])
                            price = parts[price_index].replace(',', '')
                            
                            print(f"    用户编码: {user_code}")
                            print(f"    序号: {seq_num}")
                            print(f"    描述: {description}")
                            print(f"    价格: {price}")
                        else:
                            print(f"    未找到价格格式")
                else:
                    print(f"  不以数字开头，可能被过滤")
            
            print()

if __name__ == "__main__":
    debug_missing_products() 