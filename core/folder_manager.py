import os
import re
from core.config import OUTPUT_DIR

def create_structure_from_outline(outline_text):
    """
    根据提纲文本自动创建章、节两层目录
    """
    lines = outline_text.split('\n')
    current_chapter = ""
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 匹配章：例如 "2. Foundations of SNN Algorithms" [cite: 3]
        chapter_match = re.match(r'^(\d+)\.\s+(.*)', line)
        # 匹配节：例如 "2.1 Mathematical Models" [cite: 4]
        section_match = re.match(r'^(\d+\.\d+)\s+(.*)', line)
        
        if section_match:
            section_num = section_match.group(1)
            section_name = section_match.group(2).replace(" ", "_")
            # 创建节文件夹，例如: output/2_Foundations/2.1_Mathematical_Models
            chapter_folder = [d for d in os.listdir(OUTPUT_DIR) if d.startswith(section_num.split('.')[0])][0]
            path = OUTPUT_DIR / chapter_folder / f"{section_num}_{section_name}"
            path.mkdir(parents=True, exist_ok=True)
            
        elif chapter_match:
            ch_num = chapter_match.group(1)
            ch_name = chapter_match.group(2).replace(" ", "_")
            current_chapter = f"{ch_num}_{ch_name}"
            (OUTPUT_DIR / current_chapter).mkdir(exist_ok=True)

    print("目录结构创建完成！")