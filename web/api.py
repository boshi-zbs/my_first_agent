#安装依赖pip install fastapi uvicorn pydantic
#fastapi 是框架，uvicorn 是运行服务器，pydantic 用来做数据格式校验
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List,Dict,Any
from chat_once import chat_once
from fastapi.middleware.cors import CORSMiddleware
app=FastAPI(title="My First Agent API")
# 允许所有跨域请求（生产环境应限制来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
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
if __name__=='__main__':
    import uvicorn
    #启动服务，监听端口8000端口
    uvicorn.run(app,host="0.0.0.0",port=8000)