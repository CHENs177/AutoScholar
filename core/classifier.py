import openai
from core.config import API_KEY, BASE_URL

client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)

def analyze_paper_with_ai(pdf_text, outline_text):
    prompt = f"""你是一名资深的神经形态计算专家。请根据以下文献内容（含头尾核心部分）完成任务：

【文献内容】: {pdf_text}
【综述提纲】: {outline_text}

任务：
1. 判定：相关/无关。
2. 类型：综述/研究。
3. 编号：所属三级小节（如 2.1.1）。
4. 标题：论文准确英文标题。
5. 深度总结：用300字左右概括本文的核心创新点、实验数据集以及对硬件/算法协同的贡献。

格式：
判定: [相关/无关]
类型: [综述/研究]
编号: [编号]
标题: [标题]
总结: [总结内容]
"""
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0)
        res = response.choices[0].message.content.strip()
        data = {}
        for line in res.split('\n'):
            line = line.replace("*", "").replace("[", "").replace("]", "").strip()
            if "判定:" in line: data['relevance'] = line.split("判定:")[1].strip()
            if "类型:" in line: data['type'] = line.split("类型:")[1].strip()
            if "编号:" in line:
                raw = line.split("编号:")[1].strip()
                data['section'] = "".join(c for c in raw if c.isdigit() or c == '.')
            if "标题:" in line: data['title'] = line.split("标题:")[1].strip()
            if "总结:" in line: data['synthesis'] = line.split("总结:")[1].strip()
        return data
    except: return {"relevance": "相关", "type": "研究", "section": "", "title": "Error"}