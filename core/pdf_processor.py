import fitz
import os
from pathlib import Path

def get_all_pdfs(input_dir):
    """获取 input 文件夹内所有 PDF"""
    return list(Path(input_dir).glob("*.pdf"))

def extract_full_text(pdf_path):
    """提取 PDF 全文内容，不再截断"""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"❌ 读取 PDF 失败: {e}")
        return ""

def get_next_index(parent_dir):
    """自动生成三位编号，如 001"""
    if not parent_dir.exists(): return "001"
    existing = [d for d in os.listdir(parent_dir) if os.path.isdir(parent_dir / d)]
    indices = [int(d.split('_')[0]) for d in existing if d.split('_')[0].isdigit()]
    return f"{max(indices) + 1 if indices else 1:03d}"