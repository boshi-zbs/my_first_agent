class ToolError(Exception):
    """工具执行相关的错误。"""
    pass
def search_web(query: str) -> str:
    return f"搜索到关于「{query}」的 3 条结果"
TOOLS = {
    "search_web": {"func": search_web, "arg": "query"},
}
def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据工具名执行对应的工具函数。

    工具不存在时抛出 ToolError("未知工具：xxx")
    参数缺失时抛出 ToolError("工具 xxx 缺少参数：yyy")
    正常时返回工具执行结果
    """
    if tool_name not in TOOLS:
        raise ToolError(f"未知工具：{tool_name}")
    arg_name=TOOLS[tool_name]["arg"]
    if arg_name not in arguments:
        raise ToolError(f"工具 {tool_name} 缺少参数：{arg_name}")
    return TOOLS[tool_name]["func"](arguments[arg_name])
try:
    print(execute_tool("search_web", {"query": "Python教程"}))
    print(execute_tool("search_web", {}))          # 会抛异常
except ToolError as e:
    print(f"工具调用失败：{e}")

# return 把错误伪装成正常结果，raise 让错误无法被忽略。