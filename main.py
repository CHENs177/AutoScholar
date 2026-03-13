import json
import shutil
import asyncio
import re
from pathlib import Path
from core.config import INPUT_DIR, OUTPUT_DIR, OUTLINE_PATH
from core.folder_manager import create_structure_from_outline
from core.pdf_processor import get_all_pdfs, extract_full_text, get_next_index
from core.classifier import get_semantic_chunks, analyze_chunk, reduce_synthesis
from core.researcher import generate_dual_reports, extract_and_analyze_images

def find_best_folder(target_root, section_code):
    """
    智能路由逻辑：从 AI 返回的杂乱编号中提取纯数字编号，
    并在提纲中寻找最深层级的匹配目录，同时严格排除文献存档文件夹。
    """
    if not section_code:
        return None
    
    # 1. 提取纯数字编号：例如从 "2.1.1 脉冲神经元" 提取出 "2.1.1"
    match = re.search(r'(\d+(\.[\d\.]+)*)', str(section_code))
    if not match:
        return None
    
    clean_code = match.group(1).strip('.')
    current_code = clean_code
    
    while current_code:
        # 2. 寻找匹配编号开头的文件夹
        # 排除规则：'0_Pending' 以及 包含 '/001_' 这种三位数字加下划线的存档目录
        matches = [
            m for m in target_root.rglob(f"{current_code}*") 
            if m.is_dir() 
            and '0_Pending' not in str(m)
            and not re.search(r'/\d{3}_', m.as_posix()) 
        ]
        
        if matches:
            # 优先选择路径最长的项（即最精确、层级最深的分类）
            return sorted(matches, key=lambda x: len(str(x)), reverse=True)[0]
        
        # 3. 向上溯源：如果没有找到 2.1.1，则尝试寻找 2.1
        if '.' in current_code:
            current_code = ".".join(current_code.split('.')[:-1])
        else:
            break
            
    return None

async def process_paper(pdf_path, outline_text):
    """处理单篇论文的异步工作流"""
    try:
        # 每一轮处理前确保局部变量干净
        data = {}
        
        # 1. 提取与分块
        full_text = extract_full_text(pdf_path)
        if not full_text:
            print(f"⚠️ 无法读取 PDF 文本: {pdf_path.name}")
            return
            
        chunks = get_semantic_chunks(full_text)
        sem = asyncio.Semaphore(10) # 限制并发 API 请求数
        
        print(f"\n📖 正在精读: {pdf_path.name} (共 {len(chunks)} 个分块)")
        # 这里的 analyze_chunk 由 tqdm 或 之前的并发逻辑调用
        tasks = [analyze_chunk(c, i, len(chunks), sem) for i, c in enumerate(chunks)]
        chunk_summaries = await asyncio.gather(*tasks)
        
        # 2. 逻辑重组 (Reduce)
        print(f"🧠 正在分析全文逻辑并生成专属报告数据...")
        data = await reduce_synthesis(chunk_summaries, outline_text)
        
        # 3. 获取标题与分类
        bib_info = data.get('bibliographic_info', {})
        raw_title = bib_info.get('title', 'Unknown_Title').strip()
        
        # 清洗标题：移除换行符和非法字符
        safe_title = "".join([c for c in raw_title if c.isalnum() or c in (' ', '_', '-')]).replace('\n', '').strip()
        
        # 确定大类 (综述 vs 研究)
        is_review = "综述" in data.get('classification', {}).get('type', '研究')
        root_name = "1_Review_Papers" if is_review else "2_Research_Papers"
        target_root = OUTPUT_DIR / root_name
        
        # 执行智能路由
        section_code = data.get('classification', {}).get('section', '')
        dest_root = find_best_folder(target_root, section_code)
        
        if not dest_root:
            dest_root = target_root / "0_Pending"
            dest_root.mkdir(exist_ok=True, parents=True)

        # 4. 创建唯一的存档目录 (001_Title)
        idx = get_next_index(dest_root)
        final_dir = dest_root / f"{idx}_{safe_title[:80]}"
        final_dir.mkdir(parents=True, exist_ok=True)

        # 5. 持久化存储与报告渲染
        # 保存原始 JSON
        with open(final_dir / "analysis_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # 调用 researcher 模块生成 Word
        print(f"📝 正在渲染深度 Word 报告...")
        img_results = extract_and_analyze_images(pdf_path, final_dir)
        generate_dual_reports(data, img_results, final_dir)
        
        # 6. 移动 PDF 到存档目录
        shutil.move(pdf_path, final_dir / f"{pdf_path.name}")
        
        # 获取相对路径显示
        try:
            rel_p = final_dir.relative_to(Path.cwd())
        except:
            rel_p = final_dir

        print("-" * 65)
        print(f"✅ 文献归档成功！")
        print(f"📌 识别标题: {raw_title}")
        print(f"📂 存放位置: {rel_p}")
        print("-" * 65)

    except Exception as e:
        print(f"❌ 处理 {pdf_path.name} 时发生错误: {e}")
        import traceback
        traceback.print_exc()

async def main_async():
    print("🚀 AutoScholar v3.4 异步科研引擎启动...")
    
    if not OUTLINE_PATH.exists():
        print(f"❌ 错误：找不到提纲文件 {OUTLINE_PATH}")
        return
        
    with open(OUTLINE_PATH, 'r', encoding='utf-8') as f:
        outline_text = f.read()
    
    # 动态初始化 output 目录结构
    create_structure_from_outline(outline_text)
    
    # 扫描 input 文件夹
    pdfs = get_all_pdfs(INPUT_DIR)
    if not pdfs:
        print("💡 Input 文件夹中没有待处理的 PDF 文献。")
        return

    # 串行处理每篇论文，但论文内部是并发精读
    for pdf_path in pdfs:
        await process_paper(pdf_path, outline_text)

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 用户终止了程序。")