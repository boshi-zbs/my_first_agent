import json
import re
from tools import TOOLS
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