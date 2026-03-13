import openai
import json
import asyncio
import hashlib
from pathlib import Path
from core.config import API_KEY, BASE_URL

client = openai.AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_text_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_semantic_chunks(text, chunk_size=4000, overlap=800):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

async def analyze_chunk(chunk_text, idx, total, semaphore):
    chunk_hash = get_text_hash(chunk_text)
    cache_file = CACHE_DIR / f"chunk_{chunk_hash}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)['result']
        except: pass
    async with semaphore:
        prompt = f"你是一名资深的 SNN 审稿人。请提取该片段的技术细节，将英文翻译成中文，翻译要求信雅达，部分：\n{chunk_text}"
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            result = response.choices[0].message.content
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({"result": result}, f, ensure_ascii=False)
            return result
        except Exception: return "Error"

async def reduce_synthesis(summaries, outline_text):
    combined_context = "\n\n".join(summaries)
    title_focus = "\n\n".join(summaries[:2])

    prompt = f"""你是一名资深的 SNN 专家。请根据素材撰写学术总结。
【重要提示】：每一篇论文都是独立的，请务必从以下“标题素材”中提取本文真实标题。

【标题素材】: {title_focus}
【全篇精华素材】: {combined_context}
【提纲参考】: {outline_text}

任务要求：请严格按照以下 JSON 格式返回，【键名】必须完全一致：
{{
  "bibliographic_info": {{
    "title": "提取真实独立标题",
    "authors_year": "作者, 年份",
    "source": "期刊/会议名",
    "keywords": ["关键词1", "关键词2"]
  }},
  "one_sentence_summary": "一句话总结",
  "background_motivation": {{
    "research_gap": "前人研究遗留的问题",
    "research_question": "本文解决的核心问题",
    "importance": "研究价值"
  }},
  "methodology": {{
    "key_tech": "核心技术创新",
    "data_source": "数据集与对比基准"
  }},
  "key_results": {{
    "core_conclusion": "主要发现",
    "data_table": "Markdown格式性能对比表",
    "interpretation": "深度解读"
  }},
  "critical_analysis": {{
    "innovation": "创新性评估",
    "reliability": "可靠性评估",
    "relevance_to_snn_codesign": "对协同设计的启发"
  }},
  "classification": {{
    "section": "提纲中的编号，例如 2.1.1"
  }}
}}
"""
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "你是一个极其严谨的学术助理，严格输出 JSON 且键名对齐。"},
                  {"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)