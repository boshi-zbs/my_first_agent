import ast
import operator
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import httpx
class ToolException(Exception):
    pass
env_path=Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
BOCHA_API_KEY=os.getenv("BOCHA_API_KEY")
async def search_web(query:str)->str:
    #搜索网络，返回搜索结果的标题和摘要
    try:
        async with httpx.AsyncClient() as http_client:
            response=await http_client.post(
                "https://api.bocha.cn/v1/web-search",
                headers={
                    "Authorization":f"Bearer {BOCHA_API_KEY}",
                    "Content-Type":"application/json"
                },
                json={
                    "query":query,
                    "freshness":"noLimit",
                    "summary":True,
                    "count":3
                },
                timeout=10
            )
            response.raise_for_status()
            data=response.json()
            results=data.get("data",{}).get("webPages",{}).get("value",[])
            if not results:
                return "没有找到相关结果"
            lines=[]
            for r in results:
                lines.append(
                    f"标题：{r['name']}\n"
                    f"摘要：{r.get('summary') or r.get('snippet','')[:200]}\n"
                    f"链接：{r['url']}\n"
                )
            return "\n\n".join(lines)
    except Exception as e:
        return f"搜索失败：{e}"
#定义允许读取的根目录
ALLOWED_DIR=Path(__file__).parent   #tools.py所在的目录也就是model
async def read_file(path:str)->str:
    file_path=(ALLOWED_DIR/path).resolve()
    #.absolute():只转绝对路径，不会清理
    #.resolve():转绝对路径+解析.././，拿到最终真实的路径
    if not str(file_path).startswith(str(ALLOWED_DIR.resolve())):
        return f"拒绝访问：{path}不在允许的目录内"
    if not file_path.exists():
        return f"文件不存在：{path}"
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"读取失败：{e}"
SAFE_OPERATORS={
    ast.Add:operator.add,
    ast.Sub:operator.sub,
    ast.Mult:operator.mul,
    ast.Div:operator.truediv,
    ast.Pow:operator.pow,
    ast.USub:operator.neg
}
def safe_eval(node):
    if isinstance(node,ast.Constant):
        return node.value
    elif isinstance(node,ast.BinOp):
        op=SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符：{type(node.op).__name__}")
        return op(safe_eval(node.left),safe_eval(node.right))
    elif isinstance(node,ast.UnaryOp):
        op=SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的一元运算符：{type(node.op).__name__}")
        return op(safe_eval(node.operand))
    else:
        raise ValueError(f"不支持的表达式：{type(node).__name__}")
async def calculator(expression:str)->str:
    try:
        tree=ast.parse(expression,mode="eval")
        result=safe_eval(tree.body)
        return f"{expression}={result}"
    except Exception as e:
        return f"计算失败{e}"
TOOLS={
    "search_web":{"func":search_web,"arg":"query","desc":"搜索网络"},
    "read_file":{"func":read_file,"arg":"path","desc":"读取本地文件"},
    "calculator":{"func":calculator,"arg":"expression","desc":"计算数学表达式"}
}
async def execute_tool(tool_name:str,arguments:dict)->str:
    if tool_name not in TOOLS:
        raise ToolException(f"未知工具：{tool_name}")
    arg_name=TOOLS[tool_name]['arg']
    if arg_name not in arguments:
        raise ToolException(f"工具{tool_name}缺少参数：{arg_name}")
    if tool_name=="read_file":
        path=arguments[arg_name]
        if "secret" in path.lower() or "password" in path.lower():
            # 在 Web API 中不能使用 input() 阻塞进程
            return "权限拒绝：出于安全策略，系统禁止通过 API 读取包含 secret 或 password 的敏感文件。"
    return await TOOLS[tool_name]["func"](arguments[arg_name])
