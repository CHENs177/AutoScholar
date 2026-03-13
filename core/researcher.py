import fitz
import base64
import openai
import re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from core.config import API_KEY, BASE_URL

def clean_text(text):
    if not text: return "未提取"
    return re.sub(r'[*_`~#]', '', str(text)).strip()

def set_font(run, size=10, is_bold=False):
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = Pt(size)
    run.bold = is_bold

def insert_markdown_table(doc, markdown_text):
    if not markdown_text or "|" not in str(markdown_text):
        p = doc.add_paragraph()
        set_font(p.add_run(clean_text(markdown_text)))
        return
    lines = [l.strip() for l in str(markdown_text).split('\n') if '|' in l]
    rows_data = []
    for line in lines:
        if re.match(r'^[|\s:-]+$', line): continue
        cells = [clean_text(c) for c in line.split('|') if c.strip()]
        if cells: rows_data.append(cells)
    if not rows_data: return
    table = doc.add_table(rows=len(rows_data), cols=len(rows_data[0]))
    table.style = 'Table Grid'
    for i, row in enumerate(rows_data):
        for j, cell_text in enumerate(row):
            run = table.cell(i, j).paragraphs[0].add_run(cell_text)
            set_font(run, size=9)

def generate_dual_reports(data, img_results, save_path):
    doc = Document()
    bib = data.get('bibliographic_info', {})
    bm = data.get('background_motivation', {})
    meth = data.get('methodology', {})
    res = data.get('key_results', {})
    crit = data.get('critical_analysis', {})

    # 标题
    title_text = clean_text(bib.get('title', 'Unknown Title'))
    h = doc.add_heading('', 0)
    set_font(h.add_run(title_text), size=16, is_bold=True)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 定义各个板块的读取映射
    sections = [
        ('1. 基础元数据', [
            f"• 作者与年份：{bib.get('authors_year', '未提取')}",
            f"• 来源：{bib.get('source', '未提取')}",
            f"• 关键词：{', '.join(bib.get('keywords', [])) if bib.get('keywords') else '未提取'}"
        ]),
        ('2. 研究背景与动机', [
            f"• 研究缺口：{bm.get('research_gap', '未提取')}",
            f"• 核心问题：{bm.get('research_question', '未提取')}",
            f"• 研究价值：{bm.get('importance', '未提取')}"
        ]),
        ('3. 核心方法论', [
            f"• 技术创新：{meth.get('key_tech', '未提取')}",
            f"• 数据集与基准：{meth.get('data_source', '未提取')}"
        ])
    ]

    for title, contents in sections:
        doc.add_heading(title, level=1)
        for text in contents:
            p = doc.add_paragraph()
            set_font(p.add_run(clean_text(text)))

    doc.add_heading('4. 主要发现与结果', level=1)
    p = doc.add_paragraph()
    set_font(p.add_run(f"• 核心结论：{clean_text(res.get('core_conclusion'))}"))
    insert_markdown_table(doc, res.get('data_table'))

    doc.add_heading('6. 个人批判性评价', level=1)
    doc.add_paragraph().add_run(f"⭐ 创新评估：{clean_text(crit.get('innovation'))}")
    doc.add_paragraph().add_run(f"🎯 对协同设计的启发：{clean_text(crit.get('relevance_to_snn_codesign'))}")

    doc.save(save_path / "1_深度总结报告.docx")

def extract_and_analyze_images(pdf_path, output_folder):
    return []