import json
from llm import client
# 导入刚才写的记忆库
from memory import search_memory
async def analyze_requirement(req_text: str) -> dict:
    # 1. 去记忆库检索相关的历史经验
    print("正在检索历史记忆...")
    history_memories = search_memory(req_text, top_k=3)
    # 拼接历史经验的文本
    memory_context = ""
    if history_memories:
        memory_context = "【企业历史经验参考】\n"
        for i, mem in enumerate(history_memories):
            memory_context += f"- 历史记录{i + 1}：{mem}\n"
        memory_context += "请结合上述历史经验，分析新需求中是否遗漏了类似场景。\n"
    else:
        memory_context = "【无历史经验参考】\n"

    # 2. 构造带有历史上下文的 Prompt
    """调用大模型拆解需求，返回结构化的字典"""
    prompt = f"""你是一个资深的测试架构师。
请仔细分析以下需求文档，并帮我做需求拆解：
1. 提取出所有描述清晰、可以直接测试的需求点。
2. 找出描述模糊、存在逻辑漏洞、或缺失边界条件的点，转化为需要找产品经理确认的问题。
3. 提取出隐藏的业务规则。
{memory_context}
【新需求文档】
{req_text}

请严格按照以下 JSON 格式返回，不要用Markdown包裹：
{{
  "clear_requirements": ["明确的需求1", "明确的需求2"],
  "ambiguous_questions": ["需要确认的问题1", "需要确认的问题2"],
  "business_rules": ["业务规则1", "业务规则2"]
}}
"""
    response = await client.chat.completions.create(
        model="hy3",
        messages=[{"role": "user", "content": prompt}],
        # 如果你使用的模型支持，加上 response_format 强制 JSON
        # response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except Exception as e:
        raise ValueError(f"模型返回格式错误，无法解析 JSON。原始输出：{content}")