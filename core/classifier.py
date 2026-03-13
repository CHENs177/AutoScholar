import openai
import json
from core.config import API_KEY, BASE_URL

client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_semantic_chunks(text, chunk_size=4000, overlap=800):
    """语义重叠切块逻辑：确保 main.py 能调用到它"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def analyze_chunk(chunk_text, idx, total):
    """Map阶段：学术细节抓取"""
    print(f"   > 正在精读第 {idx+1}/{total} 块...")
    prompt = f"""你是一名资深的脉冲神经网络（SNN）与类脑计算审稿人。请从以下论文片段中提取技术细节。
要求：
- 使用专业学术中文。
- 关键技术词汇（如算法名、模型名、指标）保留英文原单词或在中文后用括号标注。
- 提取：研究动机、具体算法改进、硬件参数、关键实验结果。

【片段内容】:
{chunk_text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing chunk: {e}"

def reduce_synthesis(summaries, outline_text):
    """Reduce阶段：按照高质量模板生成结构化 JSON"""
    combined_context = "\n\n".join(summaries)
    prompt = f"""你是一名资深的 SNN 软硬件协同设计专家。请根据分块提取的精华，撰写一份极具深度的学术总结。

【翻译准则】: 
- 严谨的科研中文。
- 关键术语保留英文原单词。

【提纲参考】: 
{outline_text}

【提取精华素材】: 
{combined_context}

任务要求：请严格按以下 JSON 格式返回，不要包含 Markdown 标记：
{{
  "bibliographic_info": {{
    "title": "原文准确标题",
    "authors_year": "作者 et al., 年份",
    "source": "真实的期刊/会议名称",
    "keywords": ["关键词1", "关键词2"]
  }},
  "one_sentence_summary": "一句话深度概括",
  "background_motivation": {{ "research_gap": "前人研究遗留的问题", "question": "本文解决的核心问题", "importance": "研究价值" }},
  "methodology": {{ "key_tech": "核心技术创新（含公式/逻辑描述）", "data_baselines": "数据集与对比基准" }},
  "key_results": {{
    "core_conclusion": "主要发现",
    "data_table": "使用 Markdown 格式生成的性能对比表",
    "interpretation": "对数据的深度专家级解读"
  }},
  "critical_analysis": {{
    "innovation": "创新性评估",
    "reliability": "可靠性与逻辑漏洞评估",
    "relevance_to_snn_codesign": "对 SNN 软硬件协同设计的具体启发"
  }},
  "classification": {{ "relevance": "相关/无关", "type": "综述/研究", "section": "提纲中的编号，如 2.1.1" }}
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)