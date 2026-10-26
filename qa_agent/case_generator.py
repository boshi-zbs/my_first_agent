import json
import pandas as pd
import uuid
import asyncio
from pathlib import Path
from llm import client

# 标准测试用例八要素表头
STANDARD_COLUMNS = [
    "用例编号", "所属模块", "功能点", "用例标题",
    "前置条件", "操作步骤", "预期结果", "优先级"
]


async def split_requirement(requirement_text: str) -> list[str]:
    """第一步：让大模型把长需求拆分成独立的功能模块，避免上下文过大"""
    prompt = f"""你是一个资深的测试架构师。请将以下需求文档，拆分成独立的功能模块（最多拆成 5 个）。
如果需求很短，可以直接原样返回一个列表。
请直接返回 JSON 字符串数组格式，不要用 Markdown 包裹，例如：
["模块1的需求描述", "模块2的需求描述"]

需求文档：
{requirement_text}
"""
    response = await client.chat.completions.create(
        model="hy3",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    try:
        modules = json.loads(content)
        if not isinstance(modules, list):
            return [requirement_text]
        return modules
    except:
        # 如果解析失败，就不拆分了，直接全量丢进去
        return [requirement_text]


async def generate_cases_for_module(module_text: str, module_index: int) -> list[dict]:
    """第二步：针对单个模块生成用例（并发执行）"""
    prompt = f"""你是一个顶级的资深测试工程师。请根据以下需求模块，设计出详尽的测试用例。

【核心要求】
1. **粒度要求**：一条用例只能验证一个测试点。尽可能穷举正常流、异常流、边界值。
2. **待验证需求**：如果需求中有描述模糊的地方，依然生成用例，但在“预期结果”中明确标注“【待验证】”。
3. **表头要求**：必须包含这八个字段："用例编号", "所属模块", "功能点", "用例标题", "前置条件", "操作步骤", "预期结果", "优先级"。

需求模块：
{module_text}

请严格按照 JSON 数组格式返回，不要用任何 Markdown 代码块包裹，直接返回 JSON：
[
  {{
    "用例编号": "TC_{module_index}_001",
    "所属模块": "模块名称",
    "功能点": "功能点",
    "用例标题": "测试标题",
    "前置条件": "前置条件",
    "操作步骤": "1. xxx\\n2. xxx",
    "预期结果": "期望表现",
    "优先级": "高"
  }}
]
"""
    try:
        response = await client.chat.completions.create(
            model="hy3",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        cases = json.loads(content)
        if isinstance(cases, list):
            return cases
        return []
    except Exception as e:
        print(f"模块 {module_index} 生成失败: {e}")
        return []


async def generate_test_cases_to_excel(requirement_text: str) -> str:
    """主控函数：拆分 -> 并发 -> 合并 -> 导出 Excel"""

    print("开始分析并拆分需求...")
    modules = await split_requirement(requirement_text)
    print(f"需求被拆分为 {len(modules)} 个模块，开始并发生成测试用例...")

    # 构造并发任务
    tasks = []
    for i, module in enumerate(modules):
        tasks.append(generate_cases_for_module(module, i + 1))

    # 并发执行所有任务
    results = await asyncio.gather(*tasks)

    # 合并结果
    all_cases = []
    for cases in results:
        all_cases.extend(cases)

    if not all_cases:
        raise ValueError("未能生成任何测试用例，请检查需求内容或模型状态。")

    print(f"全部生成完毕，共 {len(all_cases)} 条用例，正在合并为 Excel...")

    # 转换为 DataFrame
    df = pd.DataFrame(all_cases)

    # 确保八要素表头一定存在，补齐缺失列
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[STANDARD_COLUMNS]

    # 重新编号，保证顺序连贯 (TC_001, TC_002...)
    df["用例编号"] = [f"TC_{str(i + 1).zfill(3)}" for i in range(len(df))]

    # 导出
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)

    filename = f"test_cases_{uuid.uuid4().hex[:6]}.xlsx"
    filepath = output_dir / filename
    df.to_excel(filepath, index=False)

    return filename