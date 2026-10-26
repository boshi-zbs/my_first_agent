import json
from llm import client
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def explore_page(url: str) -> str:
    """使用无头浏览器真实访问网页，提取页面上所有的输入框和按钮特征"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # 设置超时，防止死等
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)  # 等页面渲染一下

            html = page.content()
            browser.close()

            # 用 BeautifulSoup 提取关键交互元素
            soup = BeautifulSoup(html, 'html.parser')
            elements = []

            # 找输入框
            for el in soup.find_all(['input', 'textarea']):
                elements.append({
                    "type": "输入框",
                    "tag": el.name,
                    "id": el.get('id', ''),
                    "name": el.get('name', ''),
                    "placeholder": el.get('placeholder', ''),
                    "class": ' '.join(el.get('class', []))
                })

            # 找按钮/链接
            for el in soup.find_all(['button', 'a']):
                text = el.get_text(strip=True)
                if text:  # 忽略空链接
                    elements.append({
                        "type": "按钮/链接",
                        "text": text,
                        "id": el.get('id', ''),
                        "class": ' '.join(el.get('class', []))
                    })

            # 截取前 20 个关键元素返回
            return json.dumps(elements[:20], ensure_ascii=False, indent=2)
    except Exception as e:
        return f"探索页面失败：{str(e)}"


async def generate_action_script(user_command: str) -> str:
    """根据用户指令，先真实探索页面，再生成脚本"""

    # 1. 尝试从指令中提取 URL (简单匹配)
    import re
    urls = re.findall(r'https?://[^\s]+', user_command)
    # 如果没有带 http，但提到了域名（比如百度），这里简化处理，要求用户尽量带 url。
    url = urls[0] if urls else ""

    page_context = ""
    if url:
        print(f"正在探索真实页面：{url}")
        # 真实访问页面，获取元素的真实特征！
        page_context = f"\n【真实页面元素探索结果】\n{explore_page(url)}\n请根据以上真实的 id 或 placeholder 来编写定位器！\n"

    prompt = f"""你是一个顶级的 UI 自动化专家，精通 Playwright。
请根据用户的指令编写一段可以直接运行的 Python 脚本。

用户指令：
{user_command}
{page_context}

🚨 核心要求（非常重要）：
1. 使用 `from playwright.sync_api import sync_playwright`。
2. 必须运行在非无头模式：`browser = p.chromium.launch(headless=False)`。
3. 在 page = browser.new_page() 之后，加入反爬绕过代码：
   page.add_init_script("Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}})")
4. 如果上面提供了【真实页面元素探索结果】，**必须优先使用里面真实的 id、name 或 placeholder** 来定位元素！
5. 如果没提供，请使用语义化定位（如 get_by_role, get_by_placeholder）。
# 在 prompt 里把第 6 条改一下
6. 执行操作后，等待 3 秒（page.wait_for_timeout(3000)），截图保存到 `screenshots/result.png`（请确保代码里有 `import os; os.makedirs('screenshots', exist_ok=True)` 来创建目录）。
7. 直接返回纯代码，不要包含任何 Markdown 标记（如 ```python），第一行必须是 from import。
"""

    response = await client.chat.completions.create(
        model="hy3",
        messages=[{"role": "user", "content": prompt}]
    )

    code_content = response.choices[0].message.content
    code_content = code_content.replace("```python", "").replace("```", "").strip()
    return code_content