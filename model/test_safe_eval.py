from tools import calculator
test_case=[
     "123 * 456",
    "2 ** 10",
    "__import__('os').system('dir')",
    "open('test.txt').read()",
    "(15 + 27) * 3",
    "1 / 0",
]
for expr in test_case:
    print(f"输入：{expr}")
    print(f"输出：{calculator(expr)}")
    print()
# 为什么要直接测
# Agent 安全的核心原则：不能依赖模型自觉。 模型今天拒绝，不代表明天拒绝；这个模型拒绝，不代表换个模型也拒绝。你的工具层必须自己扛住所有攻击。