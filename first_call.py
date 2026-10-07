import os
import json
from dotenv import load_dotenv
from zhipuai import ZhipuAI
#加载.env文件
load_dotenv()
#从环境变量读取API key
api_key=os.getenv("LLM_API_KEY")
#初始化客户端
client=ZhipuAI(api_key=api_key)
#发起第一次对话
response=client.chat.completions.create(
    model="glm-4-flash",
    messages=[
        {
            "role":"user",
            "content":"""请解释什么是软件测试，严格按照以下JSON格式返回，不要用Markdown代码块包裹，直接输出JSON：
            {"definition": "一句话定义", "purpose": "主要目的", "example": "一个具体例子"}
            """,
        }
    ]
)
content=response.choices[0].message.content
print("原始返回：", content)
# 方法一：用字符串替换
content=content.replace("```json","").replace("```","").strip()
# replace("```json", "") 去掉开头的 ```json replace("```", "") 去掉结尾的 ``` .strip() 去掉首尾空白（包括换行）
# 方法二：用正则提取
# import re
# match = re.search(r"\{.*\}", content, re.DOTALL)
# data = json.loads(match.group())
data=json.loads(content)
print("定义：", data["definition"])
print("目的：", data["purpose"])
print("例子：", data["example"])
# Agent 的核心循环就是“让模型输出 JSON → 解析 → 执行工具 → 把结果喂回去”
# “现在完成了一个完整的让模型输出结构化 JSON → 清洗 → 解析 → 取值”的闭环。
# 模型不总是听话。 replace 清洗正好兜住了这个坑。这就是 Agent 开发和普通脚本最大的区别——你必须假设模型会“犯错”，并为此设计防御。