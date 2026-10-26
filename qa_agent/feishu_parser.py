import os
import httpx
import re
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

FEISHU_API_ID = os.getenv("FEISHU_API_ID")
FEISHU_API_SECRET = os.getenv("FEISHU_API_SECRET")


def parse_feishu_url(url: str):
    """
    第一步：智能识别链接类型
    返回: (token, doc_type)
    doc_type 可能的值: docx, wiki, sheet, unknown
    """
    url = url.strip().rstrip('#')

    # 知识库链接
    m = re.search(r'/wiki/([a-zA-Z0-9]+)', url)
    if m:
        return m.group(1), "wiki"

    # 普通新版文档
    m = re.search(r'/docx/([a-zA-Z0-9]+)', url)
    if m:
        return m.group(1), "docx"

    # 电子表格
    m = re.search(r'/sheets/([a-zA-Z0-9]+)', url)
    if m:
        return m.group(1), "sheet"

    return None, "unknown"


async def get_tenant_access_token() -> str:
    """获取飞书应用身份 Token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": FEISHU_API_ID, "app_secret": FEISHU_API_SECRET}
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取飞书凭证失败：{data.get('msg')}")
        return data["tenant_access_token"]


async def get_wiki_obj_token(wiki_token: str, access_token: str) -> str:
    """第二步：如果是知识库，需要用 wiki_token 换取真实的 obj_token"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node",
            params={"token": wiki_token},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取知识库节点失败：{data.get('msg')}")

        node = data.get("data", {}).get("node", {})
        obj_type = node.get("obj_type")
        obj_token = node.get("obj_token")

        if obj_type != "docx":
            raise Exception(f"该知识库节点不是新版文档（当前类型：{obj_type}），暂不支持解析。")

        return obj_token


async def get_feishu_doc_content(url: str) -> str:
    """第三步：主控函数，获取最终内容"""
    if not FEISHU_API_ID or not FEISHU_API_SECRET:
        return "错误：未配置飞书应用凭证，请检查 .env 文件。"

    token, doc_type = parse_feishu_url(url)

    if doc_type == "unknown":
        return "错误：无法识别该飞书链接，目前支持 /docx/ 和 /wiki/ 格式。"
    if doc_type == "sheet":
        try:
            access_token = await get_tenant_access_token()
            return await get_feishu_sheet_content(token, access_token)
        except Exception as e:
            return f"错误：{str(e)}"

    try:
        # 获取 Token
        access_token = await get_tenant_access_token()

        # 如果是知识库，置换真实的 doc_token
        if doc_type == "wiki":
            doc_token = await get_wiki_obj_token(token, access_token)
        else:
            doc_token = token

        # 请求真实的文档内容
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://open.feishu.cn/open-apis/docs/v1/content",
                params={
                    "doc_token": doc_token,
                    "doc_type": "docx",
                    "content_type": "markdown"
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=15
            )
            data = resp.json()

            if data.get("code") != 0:
                msg = data.get('msg')
                if "permission" in msg.lower() or data.get("code") == 1770002:
                    return "错误：应用没有该文档的访问权限。请打开飞书文档，点击右上角「...」->「添加文档应用」，搜索你的应用并添加为「可阅读」。"
                return f"读取飞书文档失败：{msg}"

            return data["data"]["content"]

    except Exception as e:
        return f"错误：{str(e)}"
async def get_feishu_sheet_content(spreadsheet_token: str, access_token: str) -> str:
    """读取电子表格内容（自动获取第一个工作表并读取 A1:Z100 范围）"""
    async with httpx.AsyncClient() as client:
        # 1. 获取工作表列表，拿到第一个工作表的 sheetId
        resp = await client.get(
            f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data = resp.json()
        if data.get("code") != 0:
            return f"错误：获取工作表列表失败：{data.get('msg')}"

        sheets = data.get("data", {}).get("sheets", [])
        if not sheets:
            return "错误：该电子表格没有工作表。"
        sheet_id = sheets[0]["sheet_id"]

        # 2. 读取第一个工作表的 A1:Z100 范围（可根据需要调整）
        range_str = f"{sheet_id}!A1:Z100"
        resp2 = await client.get(
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}",
            params={"valueRenderOption": "ToString"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        data2 = resp2.json()
        if data2.get("code") != 0:
            return f"错误：读取表格数据失败：{data2.get('msg')}"

        # 3. 把二维数组拼成可读文本
        values = data2.get("data", {}).get("valueRange", {}).get("values", [])
        lines = []
        for row in values:
            row_text = " | ".join([str(cell) if cell else "" for cell in row])
            if row_text.strip():
                lines.append(row_text)
        return "\n".join(lines) if lines else "表格内容为空。"