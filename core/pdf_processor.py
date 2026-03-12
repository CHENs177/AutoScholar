import fitz
import os
from pathlib import Path


def get_all_pdfs(input_dir):
    """获取所有 PDF 文件"""
    return list(Path(input_dir).glob("*.pdf"))


def extract_smart_text(pdf_path):
    """
    针对长论文的结构化提取：抓取前 3 页（摘要/引言）和后 2 页（结论/讨论）
    """
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            # 提取前 3 页
            for i in range(min(3, total_pages)):
                text += doc[i].get_text()
            # 提取最后 2 页
            if total_pages > 3:
                for i in range(max(total_pages - 2, 3), total_pages):
                    text += doc[i].get_text()
        return text
    except Exception as e:
        print(f"❌ 读取 PDF 出错: {e}")
        return ""


def get_next_index(parent_dir):
    """
    扫描目标目录，计算下一个文件夹的编号（如 001, 002）
    """
    if not parent_dir.exists():
        return "001"

    # 获取所有子文件夹名
    existing_folders = [d for d in os.listdir(parent_dir) if os.path.isdir(parent_dir / d)]

    indices = []
    for folder in existing_folders:
        prefix = folder.split('_')[0]
        if prefix.isdigit():
            indices.append(int(prefix))

    next_idx = max(indices) + 1 if indices else 1
    return f"{next_idx:03d}"