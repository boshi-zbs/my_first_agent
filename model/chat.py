from parser import parse_tool_call
from llm import client
from datetime import datetime
from tools import execute_tool,TOOLS
import json
from pathlib import Path

def validate_tools(tools:dict)->list[str]:
    """检查工具注册表，返回问题列表。空列表表示全部通过。
        检查项：
        1. 每个工具必须有 func、arg、desc
        2. func 必须是可调用的（callable）
        3. arg 必须是非空字符串
        4. desc 必须是非空字符串
        """
    problems=[]
    for name,info in tools.items():
        if 'func' not in info:
            problems.append(f'{name}:缺少func')
        elif not callable(info['func']):
            problems.append(f"{name}:func不可调用")
        if not info.get("arg"):
            problems.append(f'{name}:缺少arg')
        if not info.get("desc"):
            problems.append(f"{name}:缺少desc")
    return problems

def build_system_prompt(tools:dict)->str:
    #根据工具注册表自动生成system prompt
    lines=["你可以使用以下工具："]
    for name,info in tools.items():
        lines.append(f"- {name}:{info.get('desc','无描述')}，参数是{info['arg']}")
    lines.append("")
    lines.append("当需要调用工具时，必须严格按照以下JSON格式返回，不要用Markdown代码块包裹：")
    lines.append('{"tool": "工具名", "arguments": {"参数名": "参数值"}}')
    lines.append("如果不需要调用工具，直接用自然语言回答。")
    lines.append("重要：只根据工具返回的内容回答，不要编造工具未提供的信息。但请把工具结果组织成自然、完整的回答，不要直接照搬工具返回的原文。")
    return "\n".join(lines)
#启动时校验
problems=validate_tools(TOOLS)
if problems:
    for p in problems:
        print(f"工具配置错误：{p}")
    raise SystemExit("工具配置不完整，退出")
#校验通过后再生成
system_prompt=build_system_prompt(TOOLS)
# system_prompt = """你可以使用以下工具：
#             - search_web: 搜索网络，参数是 query
#             - read_file:读文件内容，参数是 path
#             - calculator:计算器，参数是 expression
#             当需要调用工具时，必须严格按照以下JSON格式返回，不要用Markdown代码块包裹：
#             {"tool": "工具名", "arguments": {"参数名": "参数值"}}
#             如果不需要调用工具，直接用自然语言回答。"""
def save_logs(log:dict,filepath:str="agent_logs.json"):
    #把工具调用日志追加写入json文件
    path=Path(filepath)
    #如果文件存在，读出来;不存在，用空列表
    if path.exists():
        text=path.read_text(encoding="utf-8").strip()
        existing=json.loads(text) if text else []
    else:
        existing=[]
    existing.append(log)
    path.write_text(json.dumps(existing,ensure_ascii=False,indent=2),encoding="utf-8")
def compress_history(history:list[dict],max_message:int=4)->list[dict]:
    #当history超过max_message条时，把最早的部分压缩成一条摘要
    if len(history)<=max_message:
        return history
    old=history[:-max_message]
    recent=history[-max_message:]
    old_text="\n".join(f"{m['role']}：{m['content']}" for m in old)
    summary_prompt=f"请用一句话总结以下对话的核心内容：\n{old_text}"

    response=client.chat.completions.create(
        model="hy3",
        messages=[{"role":"user","content":summary_prompt}]
    )
    summary=response.choices[0].message.content
    return [{"role":"system","content":f"之前的对话摘要：{summary}"}]+recent
def chat():
    history=[]
    while True:
        user_input=input("你：")
        if user_input=="退出":
            break
        round_log={
            "time": datetime.now().isoformat(),
            "user_input": user_input,
            "steps": [],  # 工具调用记录
            "final_answer": "",
        }
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
                success=not(tool_result.startswith("搜索失败")
                            or tool_result.startswith("拒绝访问")
                            or tool_result.startswith("文件不存在")
                            or tool_result.startswith("计算失败")
                            or tool_result.startswith("读取失败")
                            or tool_result.startswith("没有找到相关结果")
                            )
                round_log["steps"].append({
                    "step":step,
                    "tool":tool_name,
                    "arguments":arguments,
                    "result":tool_result,
                    "success":success
                })
                history.append({"role":"assistant","content":content})
                history.append({"role":"user","content": f"工具执行结果是：{tool_result}。如果还需要调用其他工具，请继续返回JSON；如果不需要，请直接回答用户。"})
            else:
                answer=content
                break
        #填入最终回答
        round_log["final_answer"]=answer
        history.append({"role":"assistant","content":answer})
        history=compress_history(history)
        print(f"调试-history 长度：{len(history)}")
        print("本轮工具调用记录：")
        for log in round_log['steps']:
            print(f"  第{log['step']}步：{log['tool']}({log['arguments']}) → {log['result']}")
        save_logs(round_log)
        print(f"Agent:{answer}")