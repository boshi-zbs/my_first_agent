def search_web(query: str) -> str:
    return f"搜索到关于「{query}」的 3 条结果"

def read_file(path: str) -> str:
    return f"文件 {path} 的内容是：..."

TOOLS = {
    "search_web": {"func": search_web, "arg": "query"},
    "read_file": {"func": read_file, "arg": "path"},
}
def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据工具名执行对应的工具函数。

    用 TOOLS 字典查找函数，找不到时返回 "未知工具：{tool_name}"
    """
    if tool_name not in TOOLS:
        return f"未知工具：{tool_name}"
    if TOOLS[tool_name]["arg"] not in arguments:
        return f"工具 {tool_name} 缺少参数：{TOOLS[tool_name]['arg']}"
    return TOOLS[tool_name]["func"](arguments[TOOLS[tool_name]["arg"]])



# print(execute_tool("search_web", {"query": "Python教程"}))
print(execute_tool("search_web", {}))
# 期望输出：工具 search_web 缺少参数：query
print(execute_tool("read_file", {"path": "data.json"}))
print(execute_tool("delete_all", {}))