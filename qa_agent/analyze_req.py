import json
import asyncio
import sys
import os

# 把外层目录加入路径，方便导入 web.llm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.llm import client


async def analyze_requirement(req_text: str):
    prompt = f"""你是一个资深的测试架构师。
请仔细分析以下需求文档，并帮我做需求拆解：
1. 提取出所有描述清晰、可以直接测试的需求点。
2. 找出描述模糊、存在逻辑漏洞、或缺失边界条件的点，转化为需要找产品经理确认的问题。
3. 提取出隐藏的业务规则。

需求文档：
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
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(content)
        print("=== 需求拆解成功 ===")
        print(f"\n【明确的需求】共 {len(data['clear_requirements'])} 条:")
        for r in data['clear_requirements']:
            print(f" - {r}")

        print(f"\n【需要找产品确认的问题】共 {len(data['ambiguous_questions'])} 条:")
        for q in data['ambiguous_questions']:
            print(f" ? {q}")

        print(f"\n【业务规则】:")
        for b in data['business_rules']:
            print(f" * {b}")
    except Exception as e:
        print("解析失败，模型原始输出：", content)


if __name__ == "__main__":
    req_text = """
    新增一个用户注册功能。用户输入手机号、验证码、密码就能注册。
    密码要求稍微复杂一点。验证码有有效期。注册成功直接送 50 积分。
    注意同一手机号不能多次注册，另外要防止机器人恶意刷接口。
    """
    asyncio.run(analyze_requirement(req_text))