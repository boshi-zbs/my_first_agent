import os
import json
from zhipuai import ZhipuAI
from dotenv import load_dotenv
class ToolException(Exception):
    pass
def search_web(query:str)->str:
    return f"搜索到关于「{query}」的 3 条结果"
TOOLS= {
    "search_web":{"func": search_web,"arg":"query"},
}

def execute_tool(tool_name:str,arguments:dict)->str:
    if tool_name not in TOOLS:
        raise ToolException(f"未知工具：{tool_name}")
    arg_name=TOOLS[tool_name]["arg"]
    if arg_name not in arguments:
        raise ToolException(f"工具 {tool_name} 缺少参数：{arg_name}")
    return TOOLS[tool_name]["func"](arguments[arg_name])
load_dotenv()
client=ZhipuAI(api_key=os.getenv("LLM_API_KEY"))
def decide_and_execute(user_input:str)->str:
    response=client.chat.completions.create(
        model="glm-4-flash",
        messages=[{
            "role":"user",
            "content":f"""你可以使用以下工具：
            - search_web:搜索网络，参数是 query
            用户说：{user_input}
            请决定调用哪个工具，严格按照以下JSON格式返回，不要用Markdown代码块包裹：
               {{"tool": "工具名", "arguments": {{"参数名": "参数值"}}}}"""
        }
    ])
    content=response.choices[0].message.content
    # print(response.choices[0].message)
    content=content.replace("```json","").replace("```","").strip()
    data=json.loads(content)
    tool_name=data["tool"]
    arguments=data["arguments"]
    tool_result=execute_tool(tool_name,arguments)
    response2=client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role":"user","content":user_input},
            {"role":"assistant","content":content},
            {"role":"user","content":f"工具执行结果是：{tool_result}。请根据这个结果回答用户的问题。"}
        ]
    )
    return response2.choices[0].message.content
# print(decide_and_execute("帮我搜索一下 Python 教程"))
# role 有四种：user（用户）、assistant（模型）、system（系统指令）、tool（工具结果，某些 API 支持）。每一条消息都要记录，下一轮才能完整地传给模型。

def parse_tool_call(content:str):
    """解析模型返回的工具调用。

        支持两种格式：
        1. JSON: {"tool": "search_web", "arguments": {"query": "..."}}
        2. 工具名+换行+参数JSON: search_web\n{"query": "..."}

        返回 (tool_name, arguments)，解析失败返回 None
        """
    cleaned=content.replace("```json","").replace("```","").strip()
    #尝试格式1：标准JSON
    try:
        data=json.loads(cleaned)
        if isinstance(data,dict) and "tool" in data:
            return data["tool"], data["arguments"]
    except json.JSONDecodeError:
        pass
    #尝试格式2：工具名+换行+参数JSON
    lines=cleaned.strip().split("\n")
    if len(lines)>=2:
        tool_name=lines[0].strip()
        arg_text="\n".join(lines[1:]).strip()
        try:
            arguments=json.loads(arg_text)
            if isinstance(arguments,dict):
                return tool_name,arguments
        except json.JSONDecodeError:
            pass
    return None
def is_tool_call(content:str)->bool:
    #判断模型返回的是不是工具调用
    cleaned=content.replace("```json","").replace("```","").strip()
    try:
        data=json.loads(cleaned)
        return isinstance(data,dict) and "tool" in data
    except json.JSONDecodeError:
        return False
def chat():
    history=[]
    while True:
        user_input=input("你：")
        if user_input=="退出":
            break
        history.append({"role":"user","content":user_input})
        system_prompt = """你可以使用以下工具：
        - search_web: 搜索网络，参数是 query
        当需要调用工具时，必须严格按照以下JSON格式返回，不要用Markdown代码块包裹：
        {"tool": "工具名", "arguments": {"参数名": "参数值"}}
        如果不需要调用工具，直接用自然语言回答。"""
        messages = [{"role": "system", "content": system_prompt}] + history
        #第一轮：让模型决定是否调用工具
        response=client.chat.completions.create(
            model="glm-4-flash",
            messages=messages
        )
        content=response.choices[0].message.content
        print("调试-模型原始返回：", repr(content))
        # repr()会显示转义字符和换行，帮你确认内容到底是什么。
        cleaned=content.replace("```json","").replace("```","").strip()

        parsed=parse_tool_call(content)
        if parsed is not None:
            tool_name,arguments=parsed
            tool_result=execute_tool(tool_name,arguments)
            history.append({"role":"assistant","content":content})
            history.append({"role":"user","content": f"工具执行结果是：{tool_result}。请根据结果回答用户。"})
            response2=client.chat.completions.create(
                model="glm-4-flash",
                messages=history
            )
            answer=response2.choices[0].message.content
        else:
            answer=content
        # if is_tool_call(cleaned):
        #     #是工具调用：执行工具，喂回结果，在调用一次模型
        #     data=json.loads(cleaned)
        #     tool_result=execute_tool(data["tool"],data["arguments"])
        #     history.append({"role":"assistant","content":cleaned})
        #     history.append({"role":"user","content": f"工具执行结果是：{tool_result}。请根据结果回答用户。"})
        #     response2=client.chat.completions.create(
        #         model="glm-4-flash",
        #         messages=history
        #     )
        #     answer=response2.choices[0].message.content
        # else:
        #     #不是工具调用：直接就是回答
        #     answer=content
        history.append({"role":"assistant","content":answer})
        print(f"Agent:{answer}")
chat()

# 模型不总是按你要求的格式返回。 这是 Agent 开发中最常见的工程问题。真实的解决方案有三种：
# 1.用更强的模型（比如 glm-4 而不是 glm-4-flash），它更可能遵循格式指令
# 2.代码容错：像上面这样，兼容多种格式
# 3.用原生 tool_calls：但智谱这个模型没走这条路

