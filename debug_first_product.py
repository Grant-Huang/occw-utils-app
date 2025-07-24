import PyPDF2
import re

def debug_first_product():
    """调试第一个产品识别问题"""
    
    pdf_path = "upload/sample.pdf"
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    lines = text.split('\n')
    
    # 查找第一个Style的产品
    in_catalog_section = False
    in_style_section = False
    in_table_body = False
    current_door_color = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 第1层：查找CATALOG OPWM_1标题
        if 'CATALOG OPWM_1' in line.upper():
            in_catalog_section = True
            print(f"第{i}行: 找到CATALOG OPWM_1: {line}")
            continue
            
        # 第2层：在CATALOG OPWM_1下查找Style标题
        if in_catalog_section and 'Style' in line:
            in_style_section = True
            print(f"第{i}行: 找到Style: {line}")
            continue
            
        # 第3层：在Style下查找door color
        if in_style_section and in_catalog_section and 'door color' in line.lower():
            door_color_match = re.search(r'door\s+color\s+\d+\s+([A-Z]+)', line)
            if door_color_match:
                current_door_color = door_color_match.group(1)
                print(f"第{i}行: 找到Door Color: {current_door_color}")
            continue
            
        # 第3层：查找表头行
        if in_style_section and in_catalog_section and ('Description' in line or 'Manuf. code' in line or 'User code' in line):
            in_table_body = True
            print(f"第{i}行: 找到表头: {line}")
            continue
                
        # 第3层表体：检查产品行
        if in_table_body and in_style_section and in_catalog_section:
            # 检查是否以字母开头
            if re.match(r'^[A-Z]', line):
                print(f"第{i}行: 可能的产品行: {line}")
                
                # 检查是否被过滤掉
                if (line.startswith('Style') or line.startswith('Door') or 
                    line.startswith('Cabinet') or line.startswith('Cabinets') or 
                    line.startswith('Print')):
                    print(f"  被过滤掉，原因: {line.split()[0]}")
                else:
                    print(f"  应该被识别为产品行")
                    
                    # 解析产品行
                    parts = line.split()
                    if len(parts) >= 4:
                        # 查找价格
                        price_index = -1
                        for j, part in enumerate(parts):
                            if re.match(r'^\d+,?\d*\.?\d*$', part) and '.' in part:
                                price_index = j
                                break
                        
                        if price_index > 0:
                            user_code = parts[0]
                            seq_num = parts[1]
                            description = ' '.join(parts[2:price_index])
                            price = parts[price_index].replace(',', '')
                            
                            # 从最后一列提取数量
                            last_part = parts[-1]
                            qty_match = re.match(r'^(\d+)', last_part)
                            qty = qty_match.group(1) if qty_match else '1'
                            
                            print(f"    用户编码: {user_code}")
                            print(f"    序号: {seq_num}")
                            print(f"    描述: {description}")
                            print(f"    价格: {price}")
                            print(f"    数量: {qty}")
                            print(f"    花色: {current_door_color}")
                            
                            # 生成SKU
                            if 'CABINET' in description.upper():
                                occw_code = user_code.replace('-L', '').replace('-R', '')
                                sku = f"{occw_code}-PLY-{current_door_color}"
                            elif 'HARDWARE' in description.upper():
                                sku = f"HW-{user_code}"
                            elif 'ACCESSORY' in description.upper():
                                sku = f"{current_door_color}-{user_code}"
                            else:
                                sku = f"{current_door_color}-{user_code}"
                            
                            print(f"    SKU: {sku}")
                            print()

if __name__ == "__main__":
    debug_first_product() 