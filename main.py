import csv
import os

MAP_FILENAME = 'remainder_map.csv'      
OUTPUT_FILENAME = 'possible_chars_filtered.csv' 

def ensure_map_csv():
    if os.path.exists(MAP_FILENAME): return
    map_data =[
        (0,'g'), (1,'k'), (2,'a'), (3,'m'), (4,'z'), (5,'t'), (6,'l'), (7,'b'), (8,'d'), (9,'q'),
        (10,'i'), (11,'y'), (12,'f'), (13,'u'), (14,'c'), (15,'x'), (16,'b'), (17,'h'), (18,'s'), (19,'j'),
        (20,'o'), (21,'p'), (22,'r'), (23,'n'), (24,'w'), (25,'e'), (26,'y'), (27,'g'), (28,'t'), (29,'j'),
        (30,'m'), (31,'e'), (32,'v'), (33,'c'), (34,'h'), (35,'d'), (36,'x'), (37,'s'), (38,'a'), (39,'n'),
        (40,'q'), (41,'o'), (42,'l'), (43,'k'), (44,'r'), (45,'v'), (46,'w'), (47,'i'), (48,'y'), (49,'p'),
        (50,'j'), (51,'z'), (52,'q'), (53,'u'), (54,'h'), (55,'e')
    ]
    with open(MAP_FILENAME, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['remainder', 'letter'])
        for row in map_data: writer.writerow(row)

def load_reverse_mapping():
    letter_to_remainders = {}
    with open(MAP_FILENAME, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rem = int(row['remainder'])
            letter = row['letter'].lower()
            if letter not in letter_to_remainders: letter_to_remainders[letter] = []
            letter_to_remainders[letter].append(rem)
    return letter_to_remainders

def get_common_chinese_characters():
    """
    黑科技：利用 GB2312 编码规则自动提取 3755 个常用一级汉字
    (区位码 16-55 均为一级拼音排序常用汉字)
    """
    chars =[]
    for q in range(16, 56):      # 区(16-55)
        for w in range(1, 95):   # 位(1-94)
            try:
                # 组合成 GB2312 字节后解码还原成 Unicode 汉字
                b = bytes([q + 0xA0, w + 0xA0])
                c = b.decode('gb2312')
                chars.append(c)
            except:
                pass
    return set(chars) # 转成集合，查询速度 O(1)

def build_filtered_char_db():
    print("[*] 正在加载一级常用汉字库 (3755字)...")
    common_chars = get_common_chinese_characters()
    remainder_to_chars = {i:[] for i in range(56)}
    
    # 仅遍历这 3755 个常用字，计算它们的模 56 余数
    for char in common_chars:
        cp = ord(char)
        rem = cp % 56
        remainder_to_chars[rem].append(char)
        
    return remainder_to_chars

def decode_letters_to_csv(input_letters, letter_to_remainders, remainder_to_chars):
    input_letters = input_letters.lower()
    
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Input_Letter', 'Matched_Remainders', 'Possible_Characters_Filtered'])
        
        for letter in input_letters:
            if letter not in letter_to_remainders:
                writer.writerow([letter, 'N/A', '未找到对应的映射'])
                continue
            
            rems = letter_to_remainders[letter]
            possible_chars =[]
            for rem in rems:
                possible_chars.extend(remainder_to_chars[rem])
            
            # 排序一下，让输出看起来更整齐
            possible_chars.sort()
            chars_str = " ".join(possible_chars) # 用空格隔开，更适宜肉眼阅读
            rems_str = " or ".join(map(str, rems))
            
            writer.writerow([letter, rems_str, chars_str])
            print(f"[+] 字母 '{letter}' 匹配到 {len(possible_chars)} 个常用汉字。")

    print(f"\n[√] 成功！已使用【一级汉字标准】过滤，纯净结果导出至 {OUTPUT_FILENAME}")

if __name__ == '__main__':
    ensure_map_csv()
    letter_to_rems = load_reverse_mapping()
    rem_to_chars = build_filtered_char_db()
    
    user_input = input("请输入字母串 (例如 gds): ")
    if user_input:
        decode_letters_to_csv(user_input, letter_to_rems, rem_to_chars)