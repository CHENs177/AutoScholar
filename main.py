import json
import shutil
import asyncio
from pathlib import Path
from core.config import INPUT_DIR, OUTPUT_DIR, OUTLINE_PATH
from core.pdf_processor import get_all_pdfs, extract_full_text, get_next_index
from core.classifier import get_semantic_chunks, analyze_chunk, reduce_synthesis
from core.researcher import generate_dual_reports, extract_and_analyze_images

async def process_paper(pdf_path, outline_text):
    """处理单篇论文：扁平化归档模式"""
    try:
        data = {}
        # 1. 提取与分块
        full_text = extract_full_text(pdf_path)
        if not full_text: return
            
        chunks = get_semantic_chunks(full_text)
        sem = asyncio.Semaphore(10)
        
        print(f"\n📖 正在精读: {pdf_path.name} (共 {len(chunks)} 个分块)")
        tasks = [analyze_chunk(c, i, len(chunks), sem) for i, c in enumerate(chunks)]
        chunk_summaries = await asyncio.gather(*tasks)
        
        # 2. 逻辑重组
        print(f"🧠 正在分析全文逻辑并提取标题...")
        data = await reduce_synthesis(chunk_summaries, outline_text)
        
        # 3. 确定大类路径 (不再寻找提纲子文件夹)
        p_type = data.get('type', '研究')
        root_name = "1_Review_Papers" if "综述" in p_type else "2_Research_Papers"
        dest_root = OUTPUT_DIR / root_name
        dest_root.mkdir(exist_ok=True, parents=True)

        # 4. 获取标题与唯一存档目录
        bib_info = data.get('bibliographic_info', {})
        raw_title = bib_info.get('title', 'Unknown_Title').strip()
        safe_title = "".join([c for c in raw_title if c.isalnum() or c in (' ', '_', '-')]).replace('\n', '').strip()
        
        idx = get_next_index(dest_root)
        final_dir = dest_root / f"{idx}_{safe_title[:80]}"
        final_dir.mkdir(parents=True, exist_ok=True)

        # 5. 存储与报告生成
        with open(final_dir / "analysis_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"📝 正在渲染深度 Word 报告...")
        img_results = extract_and_analyze_images(pdf_path, final_dir)
        generate_dual_reports(data, img_results, final_dir)
        
        # 6. 归档 PDF
        shutil.move(pdf_path, final_dir / f"{pdf_path.name}")
        
        try:
            rel_p = final_dir.relative_to(Path.cwd())
        except:
            rel_p = final_dir

        print("-" * 65)
        print(f"✅ 文献归档成功！")
        print(f"📌 文献标题: {raw_title}")
        print(f"📂 存放位置: {rel_p}")
        print("-" * 65)

    except Exception as e:
        print(f"❌ 处理 {pdf_path.name} 时出错: {e}")

async def main_async():
    print("🚀 AutoScholar v3.5 扁平化归档引擎启动...")
    # 扫描 input 文件夹
    pdfs = get_all_pdfs(INPUT_DIR)
    if not pdfs:
        print("💡 没有待处理的 PDF 文件。")
        return

    for pdf_path in pdfs:
        await process_paper(pdf_path, "") # 此时不需要提纲文本

if __name__ == "__main__":
    asyncio.run(main_async())