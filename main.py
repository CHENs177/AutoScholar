import os
import shutil
import pandas as pd
from core.config import INPUT_DIR, OUTPUT_DIR, OUTLINE_PATH
from core.folder_manager import create_structure_from_outline
from core.pdf_processor import get_all_pdfs, extract_smart_text, get_next_index
from core.classifier import analyze_paper_with_ai
from core.researcher import extract_and_analyze_images, generate_dual_reports


def smart_run():
    # 1. 环境准备
    if not OUTLINE_PATH.exists(): return
    with open(OUTLINE_PATH, 'r', encoding='utf-8') as f:
        outline_text = f.read()
    create_structure_from_outline(outline_text)

    pdfs = get_all_pdfs(INPUT_DIR)
    if not pdfs:
        print("💡 Input 文件夹已空，无新文献需要处理。")
        return

    processed_log = []

    for pdf_path in pdfs:
        print(f"\n🚀 处理中: {pdf_path.name}")

        # 2. 深度阅读与 AI 判定
        text = extract_smart_text(pdf_path)
        analysis = analyze_paper_with_ai(text, outline_text)

        relevance = analysis.get('relevance', '相关')
        title = analysis.get('title', 'Unknown').replace("/", "_").replace(":", "")

        if "无关" in relevance:
            dest = OUTPUT_DIR / "3_Irrelevant_Papers"
            dest.mkdir(exist_ok=True)
            shutil.move(pdf_path, dest / f"{title}.pdf")
            print("🚮 已剔除至无关区。")
            continue

        # 3. 路径路由与【自动编号】
        root_name = "1_Review_Papers" if "综述" in analysis.get('type', '研究') else "2_Research_Papers"
        target_root = OUTPUT_DIR / root_name

        # 寻找章节文件夹（含模糊匹配）
        found_folder = None
        temp_sec = analysis.get('section', '').strip(".")
        while temp_sec and not found_folder:
            matches = list(target_root.rglob(f"{temp_sec}_*"))
            if not matches: matches = list(target_root.rglob(f"{temp_sec}*"))
            if matches:
                found_folder = matches[0]
            else:
                temp_sec = ".".join(temp_sec.split(".")[:-1]) if "." in temp_sec else None

        # 确定最终目录名并【加上编号前缀】
        if found_folder:
            prefix = get_next_index(found_folder)
            final_dir = found_folder / f"{prefix}_{title}"
        else:
            final_dir = target_root / "0_Pending" / title

        final_dir.mkdir(parents=True, exist_ok=True)

        # 4. 生成双文档与图片提取
        print("🎨 提取图片并分析...")
        img_results = extract_and_analyze_images(pdf_path, final_dir)
        print("📝 生成双份 Word 报告...")
        generate_dual_reports(analysis, img_results, final_dir)

        # 5. 移动文件（增量归档）
        shutil.move(pdf_path, final_dir / f"{title}.pdf")

        processed_log.append({
            "编号": prefix if found_folder else "N/A",
            "标题": title,
            "类型": analysis.get('type'),
            "章节": analysis.get('section')
        })
        print(f"✅ 完成归类: {final_dir.name}")

    # 6. 更新 Excel 矩阵
    if processed_log:
        excel_path = OUTPUT_DIR / "Literature_Matrix.xlsx"
        new_df = pd.DataFrame(processed_log)
        if excel_path.exists():
            old_df = pd.read_excel(excel_path)
            new_df = pd.concat([old_df, new_df], ignore_index=True)
        new_df.to_excel(excel_path, index=False)
        print(f"📊 文献矩阵已更新: {excel_path}")


if __name__ == "__main__":
    smart_run()