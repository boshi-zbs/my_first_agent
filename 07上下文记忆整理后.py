import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
class ToolException(Exception):
    pass
def search_web(query:str)->str:
    return f"搜索到关于「{query}」的 3 条结果"
def read_file(path: str) -> str:
    return f"文件 {path} 的内容是：这是模拟的文件内容"
def calculator(expression:str)->str:
    #计算数学表达式
    try:
        result=eval(expression)
        return f"{expression}={result}"
    except Exception as e:
        return f"计算失败{e}"
def save_logs(logs:list[dict],filepath:str="agent_logs.json"):
    #把工具调用日志追加写入json文件
    path=Path(filepath)
    #如果文件存在，读出来;不存在，用空列表
    if path.exists():
        existing=json.loads(path.read_text(encoding="utf-8"))
    else:
        existing=[]
    existing.extend(logs)
    path.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding="utf-8")

TOOLS= {
    "search_web":{"func": search_web,"arg":"query"},
    "read_file":{"func": read_file,"arg":"path"},
    "calculator":{"func": calculator,"arg":"expression"},
}

def execute_tool(tool_name:str,arguments:dict)->str:
    if tool_name not in TOOLS:
        raise ToolException(f"未知工具：{tool_name}")
    arg_name=TOOLS[tool_name]["arg"]
    if arg_name not in arguments:
        raise ToolException(f"工具 {tool_name} 缺少参数：{arg_name}")
    return TOOLS[tool_name]["func"](arguments[arg_name])
load_dotenv()
client=OpenAI(api_key=os.getenv("API_KEY"),base_url="https://tokenhub.tencentmaas.com/v1")
def parse_tool_call(content:str):
    cleaned=content.replace("```json","").replace("```","").strip()
    try:
        data=json.loads(cleaned)
        if isinstance(data,dict) and "tool" in data:
            return data["tool"], data["arguments"]
    except json.JSONDecodeError:
        pass
        # 用正则找出所有 {...} 结构，从后往前试
    matches = re.findall(r'\{[^{}]*\}', cleaned)
    for match in reversed(matches):
        try:
            data=json.loads(match)
        except json.JSONDecodeError:
            continue
        if not isinstance(data,dict):
            continue
        # 情况 A：JSON 里有 tool 字段
        if "tool" in data:
            return data["tool"],data["arguments"]
        # 情况 B：JSON 只是参数，工具名在 JSON 前面的文本里
        # 从 JSON 前面的文本中找已知工具名
        pos = cleaned.find(match)
        before = cleaned[:pos]
        for known_tool in TOOLS:
            if known_tool in before:
                return known_tool, data
    return None
system_prompt = """你可以使用以下工具：
            - search_web: 搜索网络，参数是 query
            - read_file:读文件内容，参数是 path
            - calculator:计算器，参数是 expression
            当需要调用工具时，必须严格按照以下JSON格式返回，不要用Markdown代码块包裹：
            {"tool": "工具名", "arguments": {"参数名": "参数值"}}
            如果不需要调用工具，直接用自然语言回答。"""

def chat():
    history=[]
    while True:
        user_input=input("你：")
        if user_input=="退出":
            break
        tool_logs=[]
        history.append({"role":"user","content":user_input})
        #内层循环：反复决策+执行，直到模型不再调用工具
        max_steps=5 #防止无限循环
        step=0
        while step<max_steps:
            step+=1
            messages = [{"role": "system", "content": system_prompt}] + history
            response=client.chat.completions.create(
                model="hy3",
                messages=messages
            )
            content=response.choices[0].message.content
            print("调试-模型原始返回：", repr(content))
            parsed=parse_tool_call(content)
            if parsed is not None:
                tool_name,arguments=parsed
                tool_result=execute_tool(tool_name,arguments)
                tool_logs.append({
                    "time":datetime.now().isoformat(),
                    "step":step,
                    "tool":tool_name,
                    "arguments":arguments,
                    "result":tool_result
                })
                history.append({"role":"assistant","content":content})
                history.append({"role":"user","content": f"工具执行结果是：{tool_result}。如果还需要调用其他工具，请继续返回JSON；如果不需要，请直接回答用户。"})
            else:
                answer=content
                break
        history.append({"role":"assistant","content":answer})
        print("本轮工具调用记录：")
        for log in tool_logs:
            print(f"  第{log['step']}步：{log['tool']}({log['arguments']}) → {log['result']}")
        save_logs(tool_logs)
        print(f"Agent:{answer}")
chat()
# isinstance(对象, 类型) 用来判断一个对象是不是某个类型的实例。返回 True 或 False。

