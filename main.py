import json
import shutil
from core.config import INPUT_DIR, OUTPUT_DIR, OUTLINE_PATH
from core.folder_manager import create_structure_from_outline
from core.pdf_processor import get_all_pdfs, extract_full_text, get_next_index
from core.classifier import get_semantic_chunks, analyze_chunk, reduce_synthesis
from core.researcher import generate_dual_reports, extract_and_analyze_images


def find_best_folder(target_root, section_code):
    """递归模糊匹配：确保文献归位"""
    if not section_code: return None
    clean_code = "".join(c for c in str(section_code) if c.isdigit() or c == '.').strip('.')
    current_code = clean_code
    while current_code:
        matches = list(target_root.rglob(f"{current_code}*"))
        valid_matches = [m for m in matches if '0_Pending' not in str(m) and m.is_dir()]
        if valid_matches:
            return sorted(valid_matches, key=lambda x: len(str(x)), reverse=True)[0]
        if '.' in current_code:
            current_code = ".".join(current_code.split('.')[:-1])
        else:
            break
    return None


def main_workflow():
    print("🚀 正在初始化科研工作流...")
    if not OUTLINE_PATH.exists(): return
    with open(OUTLINE_PATH, 'r', encoding='utf-8') as f:
        outline_text = f.read()

    create_structure_from_outline(outline_text)
    pdfs = get_all_pdfs(INPUT_DIR)

    for pdf_path in pdfs:
        try:
            print(f"\n深度处理开始: {pdf_path.name}")
            full_text = extract_full_text(pdf_path)
            if not full_text: continue

            # 分块
            chunks = get_semantic_chunks(full_text)
            print(f"📄 已切分为 {len(chunks)} 个语义块，开始逐块精读...")

            # Map 阶段
            chunk_summaries = [analyze_chunk(c, i, len(chunks)) for i, c in enumerate(chunks)]

            # Reduce 阶段
            print("🧠 正在进行逻辑重组与学术级翻译...")
            data = reduce_synthesis(chunk_summaries, outline_text)

            # 路由分类
            is_review = "综述" in data.get('type', '研究')
            root_name = "1_Review_Papers" if is_review else "2_Research_Papers"
            target_root = OUTPUT_DIR / root_name

            found_folder = find_best_folder(target_root, data.get('classification', {}).get('section', ''))
            dest_root = found_folder if found_folder else (target_root / "0_Pending")
            dest_root.mkdir(exist_ok=True)

            # 编号与文件夹创建
            idx = get_next_index(dest_root)
            safe_title = "".join(
                [c for c in data['bibliographic_info']['title'] if c.isalnum() or c in (' ', '_', '-')]).strip()
            final_dir = dest_root / f"{idx}_{safe_title[:80]}"
            final_dir.mkdir(parents=True, exist_ok=True)

            # 保存 JSON
            with open(final_dir / "analysis_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # 生成报告
            print(f"📝 正在生成 Word 报告与图表解析...")
            img_results = extract_and_analyze_images(pdf_path, final_dir)
            generate_dual_reports(data, img_results, final_dir)

            # 归档
            shutil.move(pdf_path, final_dir / f"{pdf_path.name}")
            print(f"✅ 处理完成: {final_dir.name}")

        except Exception as e:
            print(f"❌ 意外错误: {e}")


if __name__ == "__main__":
    main_workflow()