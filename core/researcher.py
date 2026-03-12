import fitz
import base64
from docx import Document
import openai
from core.config import API_KEY, BASE_URL

client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)


def extract_and_analyze_images(pdf_path, output_folder):
    """提取大尺寸图片并利用 GPT-4o 分析"""
    img_dir = output_folder / "Figures"
    img_dir.mkdir(exist_ok=True)

    doc = fitz.open(pdf_path)
    image_analyses = []

    for page_index in range(len(doc)):
        images = doc[page_index].get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # 重点：通过字节大小过滤掉小图标，只保留作者放入的真实图片
            if len(image_bytes) < 20000: continue

            img_name = f"page{page_index + 1}_img{img_index + 1}.png"
            img_path = img_dir / img_name
            with open(img_path, "wb") as f:
                f.write(image_bytes)

            # 视觉分析
            try:
                base64_img = base64.b64encode(image_bytes).decode('utf-8')
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "请分析该学术图表。它展示了什么？对SNN或硬件实现有什么意义？"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                    ]}],
                    max_tokens=300
                )
                image_analyses.append({"path": img_name, "desc": response.choices[0].message.content})
            except:
                continue
    return image_analyses


def generate_dual_reports(analysis, img_results, save_path):
    """生成两个独立的 Word 文档"""
    # 1. 文献总结报告
    doc_sum = Document()
    doc_sum.add_heading(f"文献总结: {analysis['title']}", 0)
    doc_sum.add_heading("核心内容与创新点", level=1)
    doc_sum.add_paragraph(analysis.get('synthesis', "待补充深度分析..."))
    doc_sum.save(save_path / "1_文献总结报告.docx")

    # 2. 图片详细解析
    doc_img = Document()
    doc_img.add_heading(f"图表解析: {analysis['title']}", 0)
    if img_results:
        for img in img_results:
            doc_img.add_heading(f"图片: {img['path']}", level=2)
            doc_img.add_paragraph(f"解析内容: {img['desc']}")
    else:
        doc_img.add_paragraph("未检测到有效大尺寸图表。")
    doc_img.save(save_path / "2_图表详细解析.docx")