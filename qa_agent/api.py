from fastapi import FastAPI, UploadFile, File, Form,HTTPException
import sys
import os
from pydantic import BaseModel
from typing import List,Dict,Any
from chat_once import chat_once
from fastapi.middleware.cors import CORSMiddleware
# 把外层目录加入路径，确保能找到 qa_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from qa_agent.file_parser import extract_text_from_file
from qa_agent.analyzer import analyze_requirement
from qa_agent.memory import add_to_memory
from qa_agent.script_generator import generate_action_script
from qa_agent.feishu_parser import get_feishu_doc_content  # 导入飞书解析
from qa_agent.case_generator import generate_test_cases_to_excel
from fastapi.responses import FileResponse
import uuid
import subprocess
from fastapi.responses import FileResponse
app=FastAPI(title="My First Agent API")
# 允许所有跨域请求（生产环境应限制来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 接收飞书链接分析需求 ---
@app.post("/api/feishu_analyze")
async def feishu_analyze(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="链接不能为空")

    content = await get_feishu_doc_content(url)
    if content.startswith("错误") or content.startswith("获取") or content.startswith("解析"):
        raise HTTPException(status_code=400, detail=content)

    try:
        result = await analyze_requirement(content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 接收飞书链接执行自动化 ---
@app.post("/api/feishu_execute")
async def feishu_execute(url: str = Form(...)):
    if not url.strip():
        raise HTTPException(status_code=400, detail="链接不能为空")

    content = await get_feishu_doc_content(url)
    if content.startswith("错误") or content.startswith("获取") or content.startswith("解析"):
        raise HTTPException(status_code=400, detail=content)

    filename = f"temp_script_{uuid.uuid4().hex[:6]}.py"
    try:
        code = await generate_action_script(content)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run(
            ["python", filename], capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=60
        )

        if result.returncode != 0:
            return {"status": "error", "code": code, "error_msg": result.stderr}
        return {"status": "success", "code": code, "message": "执行完成"}
    except Exception as e:
        return {"status": "error", "code": code if 'code' in locals() else "", "error_msg": str(e)}
    finally:
        if os.path.exists(filename):
            os.remove(filename)

class ExecuteRequest(BaseModel):
    command: str


@app.post("/api/execute_ui")
async def execute_ui_api(
        command: str = Form(""),
        file: UploadFile = File(None)
    ):
    content_to_process = command

    if file and file.filename:
        file_bytes = await file.read()
        file_text = extract_text_from_file(file_bytes, file.filename)
        content_to_process += f"\n\n【补充的测试用例文档内容】\n{file_text}"

    if not content_to_process.strip():
        raise HTTPException(status_code=400, detail="指令不能为空")

    filename = f"temp_script_{uuid.uuid4().hex[:6]}.py"
    try:
        # 1. 生成代码
        code = await generate_action_script(content_to_process)

        # 2. 写入临时文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        # 3. 执行代码 (强制使用 utf-8 编码，忽略无法解码的字符)
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=60
        )
        if result.returncode != 0:
            return {"status": "error", "code": code, "error_msg": result.stderr}

        return {"status": "success", "code": code, "message": "执行完成，已截图 result.png"}

    except subprocess.TimeoutExpired:
        return {"status": "error", "code": code, "error_msg": "执行超时（超过60秒），请检查是否有死循环或等待时间过长。"}
    except Exception as e:
        return {"status": "error", "code": code if 'code' in locals() else "", "error_msg": str(e)}
    finally:
        # 4. 无论成功失败，必须清理临时文件，否则会堆满垃圾
        if os.path.exists(filename):
            os.remove(filename)
class MemoryInput(BaseModel):
    content: str
    source_type: str = "history_doc"


@app.post("/api/add_memory")
async def add_memory_api(
        file: UploadFile = File(None),
        text: str = Form("")
):
    content_to_save = ""

    if file and file.filename:
        file_bytes = await file.read()
        content_to_save = extract_text_from_file(file_bytes, file.filename)
        if "失败" in content_to_save:
            raise HTTPException(status_code=400, detail=content_to_save)

    if text.strip():
        content_to_save += "\n" + text

    if not content_to_save.strip():
        raise HTTPException(status_code=400, detail="未提供任何内容")

    doc_id = f"mem_{uuid.uuid4().hex[:8]}"
    add_to_memory(content_to_save, doc_id, {"source": "user_upload"})
    return {"status": "success", "message": "已成功存入企业知识库！"}


class CodeGenRequest(BaseModel):
    test_case_content: str


@app.post("/api/generate_code")
async def generate_code_api(req: CodeGenRequest):
    if not req.test_case_content.strip():
        raise HTTPException(status_code=400, detail="测试用例内容不能为空")

    try:
        code = await generate_action_script(req.test_case_content)
        return {"code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#1.定义请求的数据格式
class ChatRequest(BaseModel):
    user_input:str
    history:List[Dict[str,Any]]=[]
#2.定义响应的数据格式
class ChatResponse(BaseModel):
    answer:str
    history:List[Dict[str,Any]]
#3.编写接口
@app.post("/chat",response_model=ChatResponse)
async def chat_endpoint(request:ChatRequest):
    #调用我们刚刚重构的单轮对话函数
    new_history,answer=await chat_once(
        history=request.history,
        user_input=request.user_input
    )
    #把最新的历史和回答返回给前端
    return ChatResponse(
        answer=answer,
        history=new_history
    )


# 新增一个专门接收文件并分析需求的接口
@app.post("/analyze_file")
async def analyze_file_endpoint(
        file: UploadFile = File(...),
        extra_text: str = Form("")
):
    # 1. 读取上传的文件字节
    file_bytes = await file.read()

    # 2. 解析文件文本
    extracted_text = extract_text_from_file(file_bytes, file.filename)

    if "不支持" in extracted_text:
        return {"error": extracted_text}

    # 3. 将解析出的文本 + 用户额外补充的文字 拼在一起
    full_requirement = extracted_text + "\n" + extra_text

    # 4. 调用我们写好的需求分析函数（注意这里为了测试先直接返回解析的内容，后续接入 LLM）
    # 记得把 analyze_requirement 从你的 qa_agent 里导入进来
    # ...

    return {
        "filename": file.filename,
        "extracted_length": len(extracted_text),
        "preview": extracted_text[:200] + "..."  # 预览前200字
    }


@app.post("/api/analyze")
async def analyze_api(
        file: UploadFile = File(None),
        text: str = Form("")
):
    requirement_text = ""

    # 1. 如果上传了文件，解析文件内容
    if file and file.filename:
        file_bytes = await file.read()
        requirement_text = extract_text_from_file(file_bytes, file.filename)
        if "失败" in requirement_text or "不支持" in requirement_text:
            raise HTTPException(status_code=400, detail=requirement_text)

    # 2. 如果用户还填了补充文本，拼接到一起
    if text.strip():
        requirement_text += "\n" + text

    if not requirement_text.strip():
        raise HTTPException(status_code=400, detail="未提供任何需求内容")

    # 3. 调用 LLM 分析需求
    try:
        result = await analyze_requirement(requirement_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/get_screenshot")
async def get_screenshot():
    # 截图保存在 api.py 运行的目录下的 screenshots 文件夹
    img_path = os.path.join("screenshots", "result.png")
    if os.path.exists(img_path):
        # 加个时间戳防止浏览器缓存旧图片
        return FileResponse(img_path, headers={"Cache-Control": "no-cache"})
    return {"error": "截图不存在"}


# --- 新增：生成 Excel 用例接口 ---
class ExcelGenRequest(BaseModel):
    requirement_text: str


@app.post("/api/generate_excel")
async def generate_excel_api(req: ExcelGenRequest):
    if not req.requirement_text.strip():
        raise HTTPException(status_code=400, detail="需求内容不能为空")

    try:
        filename = await generate_test_cases_to_excel(req.requirement_text)
        return {"filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 新增：下载 Excel 接口 ---
@app.get("/api/download_excel/{filename}")
async def download_excel_api(filename: str):
    filepath = os.path.join("exports", filename)
    if os.path.exists(filepath):
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="文件不存在")
if __name__=='__main__':
    import uvicorn
    #启动服务，监听端口8000端口
    uvicorn.run(app,host="0.0.0.0",port=8000)