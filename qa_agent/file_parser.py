import io
from docx import Document
from pypdf import PdfReader
import pandas as pd  # 新增 pandas


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """根据文件后缀名，提取文本内容"""
    filename = filename.lower()

    # 处理 TXT
    if filename.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return "TXT文件编码错误，请使用UTF-8编码。"

    # 处理 Word (.docx)
    elif filename.endswith(".docx"):
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n".join(text)
        except Exception:
            return "Word文件解析失败，文件可能已损坏或格式错误。"

    # 处理 PDF
    elif filename.endswith(".pdf"):
        try:
            if not file_bytes.startswith(b'%PDF-'):
                return "解析失败：该文件不是标准的PDF格式（可能是被强行修改了后缀名）。"
            reader = PdfReader(io.BytesIO(file_bytes))
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            return f"PDF文件解析失败：{str(e)}"

    # 处理 Excel (.xlsx, .xls)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            # 使用 pandas 读取所有 sheet
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            all_text = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                df = df.fillna("")  # 把空值填充为空字符串，防止拼出来是 nan

                all_text.append(f"\n【工作表：{sheet_name}】")

                # 把表头加上
                if not df.empty:
                    all_text.append(" | ".join([str(col) for col in df.columns]))
                    all_text.append("-" * 40)  # 加个分隔线

                # 遍历每一行数据
                for index, row in df.iterrows():
                    row_data = [str(val) for val in row.values]
                    all_text.append(" | ".join(row_data))

            return "\n".join(all_text)
        except Exception as e:
            return f"Excel文件解析失败：{str(e)}"

    else:
        return "不支持的文件格式，请上传 txt、docx、pdf、xlsx 或 xls 文件。"