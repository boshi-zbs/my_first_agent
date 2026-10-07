def describe_case(case:dict)->str:
    """接收一个测试用例字典，返回一句话描述。
       字典格式示例：
       {"id": "TC001", "name": "登录-错误密码", "priority": "高"}
       """
    # 你要写的内容：
    # 从 case 里取出 id、name、priority
    # 拼成一句话返回，比如：
    # "用例 TC001（登录-错误密码）优先级为高"
    return f'用例 {case["id"]}（{case["name"]}）优先级为{case.get("priority","未知")}'
# 测试你的函数
case1 = {"id": "TC001", "name": "登录-错误密码", "priority": "高"}
case2 = {"id": "TC004", "name": "退出登录"}
print(describe_case(case1))
print(describe_case(case2))   # 用例 TC004（退出登录）优先级为未知
# 期望输出：用例 TC001（登录-错误密码）优先级为高

def summarize_cases(cases: list[dict]) -> str:
    """接收一个测试用例列表，返回汇总描述。
    要求：统计一共有几条用例，并列出所有用例的 id。
    示例输出："共 3 条用例：TC001, TC002, TC003"
    """
    ids=[]
    for case in cases:
        ids.append(case["id"])
    ids_text="，".join(ids)
    return f'共{len(cases)}条用例：{ids_text}'
cases = [
    {"id": "TC001", "name": "登录-错误密码", "priority": "高"},
    {"id": "TC002", "name": "登录-正确密码", "priority": "中"},
    {"id": "TC003", "name": "注册-重复邮箱", "priority": "高"},
]
print(summarize_cases(cases))

def list_tool_names(tool_calls: list[dict]) -> str:
    """接收工具调用列表，返回所有工具名字的汇总。
    示例输出："调用了 2 个工具：search_web, read_file"
    """
    if not tool_calls:
        return "没有调用任何工具"
    arr=[]
    for case in tool_calls:
        arr.append(case.get("name"))
    arr_text="，".join(arr)
    return f"调用了{len(tool_calls)}个工具：{arr_text}"
tool_calls = [
    {"name": "search_web", "arguments": {"query": "Python教程"}},
    {"name": "read_file", "arguments": {"path": "data.json"}},
]
print(list_tool_names(tool_calls))
# 期望输出：调用了 2 个工具：search_web, read_file

def analyze_cases(cases: list[dict]) -> str:
    """接收测试用例列表，返回每条用例的描述，用换行分隔。
    示例输出：
    用例 TC001（登录-错误密码）优先级为高
    用例 TC002（登录-正确密码）优先级为中
    """
    arr=[]
    for case in cases:
        arr.append(describe_case(case))
    return "\n".join(arr)
cases = [
    {"id": "TC001", "name": "登录-错误密码", "priority": "高"},
    {"id": "TC002", "name": "登录-正确密码", "priority": "中"},
    {"id": "TC003", "name": "注册-重复邮箱"},   # 没有 priority
]
print(analyze_cases(cases))