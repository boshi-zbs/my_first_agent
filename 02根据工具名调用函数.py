def search_web(query: str) -> str:
    """模拟搜索，返回搜索结果。"""
    return f"搜索到关于「{query}」的 3 条结果"

def read_file(path: str) -> str:
    """模拟读文件，返回文件内容。"""
    return f"文件 {path} 的内容是：..."

def execute_tool(tool_name: str, arguments: dict) -> str:
    """根据工具名执行对应的工具函数。

    tool_name 是 "search_web" 时，调用 search_web(arguments["query"])
    tool_name 是 "read_file" 时，调用 read_file(arguments["path"])
    tool_name 是其他值时，返回 "未知工具：{tool_name}"
    """
    if tool_name=="search_web":
        return search_web(arguments.get("query"))
    elif tool_name=="read_file":
        return read_file(arguments.get("path"))
    else:
        return f"未知工具：{tool_name}"


print(execute_tool("search_web", {"query": "Python教程"}))
# 期望输出：搜索到关于「Python教程」的 3 条结果
print(execute_tool("read_file", {"path": "data.json"}))
# 期望输出：文件 data.json 的内容是：...
print(execute_tool("delete_all", {}))
# 期望输出：未知工具：delete_all