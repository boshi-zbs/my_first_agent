import os
import json
from zhipuai import ZhipuAI
from dotenv import load_dotenv
class ToolError(Exception):
    pass
load_dotenv()
client=ZhipuAI(api_key=os.getenv("LLM_API_KEY"))
# 工具定义
def search_web(query: str) -> str:
    return f"搜索到关于「{query}」的 3 条结果"
TOOLS = {
    "search_web": {"func": search_web, "arg": "query"},
}
def execute_tool(tool_name: str, arguments: dict) -> str:
    if tool_name not in TOOLS:
        raise ToolError(f"未知工具：{tool_name}")
    arg_name = TOOLS[tool_name]["arg"]
    if arg_name not in arguments:
        raise ToolError(f"工具 {tool_name} 缺少参数：{arg_name}")
    return TOOLS[tool_name]["func"](arguments[arg_name])

def decide_and_execute(user_input: str) -> str:
    """让模型决定调用哪个工具，然后执行它。
    步骤：
    1. 构造 prompt，告诉模型有哪些工具可用，要求它返回 JSON：
       {"tool": "工具名", "arguments": {"参数名": "参数值"}}
    2. 调用模型
    3. 清洗并解析 JSON
    4. 从解析结果里取出 tool 和 arguments
    5. 调用 execute_tool(tool, arguments)
    6. 返回执行结果
    """
    response = client.chat.completions.create(
        model = "glm-4-flash",
        messages = [
        {
            "role": "user",
            "content": f"""你可以使用以下工具：
               - search_web: 搜索网络，参数是 query
               用户说：{user_input}
               请决定调用哪个工具，严格按照以下JSON格式返回，不要用Markdown代码块包裹：
               {{"tool": "工具名", "arguments": {{"参数名": "参数值"}}}}"""
        }
    ])
    content=response.choices[0].message.content
    content=content.replace("```json","").replace("```","").strip()
    print(content)
    data=json.loads(content)
    tool_name=data["tool"]
    arguments=data["arguments"]
    # 执行工具
    tool_result=execute_tool(tool_name,arguments)
    # 第二轮：把工具结果喂回给模型，让它生成最终回答
    response2=client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": content},  # 模型上一轮的决策
            {"role": "user", "content": f"工具执行结果是：{tool_result}。请根据这个结果回答用户的问题。"}
        ]
    )
    return response2.choices[0].message.content

print(decide_and_execute("帮我搜索一下 Python 教程"))
# 期望输出：搜索到关于「Python教程」的 3 条结果
# Agent的核心机制：用户输入 → 模型决定调用工具 → 解析JSON → 执行工具 → 返回结果。
# 真实的 Agent 是：用户问 → 模型说“调 search_web” → 你执行 → 把搜索结果喂回给模型 → 模型根据结果生成最终回答。