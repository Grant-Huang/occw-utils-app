import re

def test_parse_logic():
    """测试解析逻辑"""
    
    # 模拟PDF内容
    test_content = """CATALOG OPWM_1
Supplier4 Premium (Single Shaker) Style
Door Style 4 Single Shaker
Cabinet color 5 Particle Board Box
door color 4 WSS
Description Manuf. code # Qty User code
Cabinets
3DB30 27 3-Drawers Base Cabinet 758.00 13DB30
SB36 28 Sink Base Cabinet 1 FK Drawer + 2 Door 468.00 1SB36
BLS36-R 29 Base Corner Cabinet 949.00 1BLS36-R
B36FH 33 Base Full Height Cabinet 2 Door 507.00 1B36FH
B30 34 Base Cabinet 1 Drawer+2 Door 549.00 1B30
BSR12 36 1-door Base spice rack Cabinet 554.00 1BSR12
3DB24 39 3-Drawers Base Cabinet 678.00 13DB24
7 Elite (Slim Shaker) Style
Door Style 7 Slim Shaker
Cabinet color 6 Plywood Box
door color 7 SSW
Description Manuf. code # Qty User code
Cabinets
W3036 1 Wall Cabinet 2 Door 602.00 1W3036
W3015 2 Wall Short Cabinet 281.00 1W3015"""
    
    # 测试door color识别
    lines = test_content.split('\n')
    for line in lines:
        if 'door color' in line.lower():
            print(f"检查door color行: {line}")
            door_color_match = re.search(r'door\s+color\s+\d+\s+([A-Z]+)', line)
            if door_color_match:
                print(f"找到Door Color: {door_color_match.group(1)}")
            else:
                door_color_match = re.search(r'door\s+color\s+([A-Z]+)', line.lower())
                if door_color_match:
                    print(f"找到Door Color: {door_color_match.group(1)}")
                else:
                    print("未找到door color")
    
    # 测试产品行解析
    for line in lines:
        if re.match(r'^\d+', line):
            parts = line.split()
            print(f"产品行: {line}")
            print(f"  字段数: {len(parts)}")
            print(f"  字段: {parts}")
            
            # 查找价格（包含逗号的数字）
            price_index = -1
            for i, part in enumerate(parts):
                if re.match(r'^\d+,?\d*\.?\d*$', part) and '.' in part:
                    price_index = i
                    break
            
            print(f"  价格索引: {price_index}")
            
            if price_index >= 2 and len(parts) >= 6:
                user_code = parts[0]  # 第1列：用户编码
                seq_num = parts[1]    # 第2列：序号
                description = ' '.join(parts[2:price_index])  # 第3列：描述
                price = parts[price_index].replace(',', '')   # 第4列：价格
                
                # 第5列：数量+用户编码，需要拆分
                last_part = parts[-1]
                qty_match = re.match(r'^(\d+)', last_part)
                qty = qty_match.group(1) if qty_match else '1'
                
                print(f"  解析结果:")
                print(f"    用户编码: {user_code}")
                print(f"    序号: {seq_num}")
                print(f"    描述: {description}")
                print(f"    价格: {price}")
                print(f"    数量: {qty}")
                print(f"    最后一列: {last_part}")
            print()

if __name__ == "__main__":
    test_parse_logic() 