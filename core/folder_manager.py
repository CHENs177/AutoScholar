import os
import re
from core.config import OUTPUT_DIR


def create_structure_from_outline(outline_text):
    all_roots = ["1_Review_Papers", "2_Research_Papers", "3_Irrelevant_Papers"]
    for root_name in all_roots: (OUTPUT_DIR / root_name).mkdir(exist_ok=True)

    detailed_roots = ["1_Review_Papers", "2_Research_Papers"]
    lines = outline_text.split('\n')

    for root_name in detailed_roots:
        root_path = OUTPUT_DIR / root_name
        for line in lines:
            line = line.strip()
            if not line: continue

            # 改进正则：支持 2.1 或 2.1.1 或 2.1.1.1
            sec_match = re.match(r'^(\d+(\.\d+)+)\s+(.*)', line)
            ch_match = re.match(r'^(\d+)\.\s+(.*)', line)

            if sec_match:
                sec_num, sec_name = sec_match.group(1), sec_match.group(3).replace(" ", "_")
                ch_prefix = sec_num.split('.')[0]
                try:
                    parent_ch = [d for d in os.listdir(root_path) if d.startswith(f"{ch_prefix}_")][0]
                    (root_path / parent_ch / f"{sec_num}_{sec_name}").mkdir(parents=True, exist_ok=True)
                except:
                    pass
            elif ch_match:
                ch_num, ch_name = ch_match.group(1), ch_match.group(2).replace(" ", "_")
                (root_path / f"{ch_num}_{ch_name}").mkdir(exist_ok=True)
    print("✅ 目录初始化完成！")