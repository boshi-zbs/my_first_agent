import os
# 关键：强制 HuggingFace 走国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path


# 指定数据库存放的本地文件夹
DB_PATH = Path(__file__).parent / "chroma_db"
DB_PATH.mkdir(exist_ok=True)

# 初始化 Chroma 客户端
client = chromadb.PersistentClient(path=str(DB_PATH))

# 使用本地的向量化模型（第一次运行会自动下载，大概需要一两分钟）
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # 轻量级英文/中文通用模型
)

# 获取或创建一个“知识库集合”
collection = client.get_or_create_collection(
    name="history_requirements",
    embedding_function=sentence_transformer_ef
)


def add_to_memory(text: str, doc_id: str, metadata: dict = None):
    """把一段历史需求存入记忆"""
    if not text.strip():
        return
    # 简单起见，每次存一段
    collection.add(
        documents=[text],
        metadatas=[metadata or {"source": "history"}],
        ids=[doc_id]
    )



    print(f"已存入记忆：{doc_id}")


def search_memory(query: str, top_k: int = 2) -> list[str]:
    """根据新需求，检索历史上最相似的文档片段"""
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    # 返回检索到的文本列表
    if results and results["documents"]:
        return results["documents"][0]
    return []


# 测试一下
if __name__ == "__main__":
    # 假想一段历史测试用例/旧需求
    add_to_memory(
        "历史需求：用户注册时，密码必须包含大小写字母、数字和特殊字符，长度至少8位。连续输错5次锁定账号。",
        doc_id="req_001"
    )
    add_to_memory(
        "历史缺陷：iOS端在输入验证码时，如果不点击页面空白处，键盘不会收起，导致无法点击下一步。",
        doc_id="bug_001"
    )

    # 模拟检索
    print("\n--- 检索测试 ---")
    query = "现在要做一个新的用户登录模块，帮我看看有什么历史经验？"
    found = search_memory(query)
    for i, f in enumerate(found):
        print(f"匹配结果 {i + 1}: {f}")