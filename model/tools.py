from pathlib import Path
import ast
import operator
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
class ToolException(Exception):
    pass
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
BOCHA_API_KEY=os.getenv("BOCHA_API_KEY")
def search_web(query:str)->str:
    #搜索网络，返回搜索结果的标题和摘要
    try:
        response=requests.post(
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
            timeout=10,
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
ALLOWED_DIR=Path(__file__).parent   #tools.py所在目录
def read_file(path: str) -> str:
    #读取本地文件内容，安全边界限制只允许读取ALLOWED_DIR下的文件
    file_path=(ALLOWED_DIR/path).resolve()
    #安全检查：确保解析后的路径在ALLOWED_DIR内
    # Agent 安全的核心原则：永远不要相信模型传来的参数。 模型可能被用户诱导，传一个危险路径。你的工具必须在执行前做检查，而不是无条件信任。
    if not str(file_path).startswith(str(ALLOWED_DIR.resolve())):
        return f"拒绝访问：{path} 不在允许的目录内"
    if not file_path.exists():
        return f"文件不存在:{path}"
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"读取失败：{e}"

#允许的运算符
# 语法节点类型 → 实际执行函数的映射
SAFE_OPERATORS={
    ast.Add:operator.add,
    ast.Sub:operator.sub,
    ast.Mult:operator.mul,
    ast.Div:operator.truediv,
    ast.Pow:operator.pow,
    ast.USub:operator.neg,
}
def safe_eval(node):
    #递归计算AST节点，只允许数字和基本运算
    if isinstance(node,ast.Constant):#数字
        return node.value
    elif isinstance(node,ast.BinOp):#二元计算a+b
        op=SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符：{type(node.op).__name__}")
        return op(safe_eval(node.left),safe_eval(node.right))
    elif isinstance(node,ast.UnaryOp):#一元计算-a
        op=SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的一元运算符：{type(node.op).__name__}")
        return op(safe_eval(node.operand))
    else:
        raise ValueError(f"不支持的表达式：{type(node).__name__}")
def calculator(expression:str)->str:
    #计算数学表达式
    try:
        # result=eval(expression)
        tree=ast.parse(expression,mode="eval")
        result=safe_eval(tree.body)
        return f"{expression}={result}"
    except Exception as e:
        return f"计算失败{e}"

TOOLS= {
    "search_web":{"func": search_web,"arg":"query","desc":"搜索网络"},
    "read_file":{"func": read_file,"arg":"path","desc":"读取本地文件"},
    "calculator":{"func": calculator,"arg":"expression","desc":"计算数学表达式"},
}

def execute_tool(tool_name:str,arguments:dict)->str:
    if tool_name not in TOOLS:
        raise ToolException(f"未知工具：{tool_name}")
    arg_name=TOOLS[tool_name]["arg"]
    if arg_name not in arguments:
        raise ToolException(f"工具 {tool_name} 缺少参数：{arg_name}")
    return TOOLS[tool_name]["func"](arguments[arg_name])