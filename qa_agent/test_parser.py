from file_parser import extract_text_from_file
from pathlib import Path

# 读取本地文件为 bytes
file_path = Path("test.pdf")  # 如果你建的是 pdf，就改成 test.pdf
if not file_path.exists():
    print(f"找不到文件：{file_path.absolute()}，请先建一个测试文件。")
else:
    file_bytes = file_path.read_bytes()

    # 调用解析函数
    result = extract_text_from_file(file_bytes, file_path.name)

    print("=== 解析结果 ===")
    print(result)