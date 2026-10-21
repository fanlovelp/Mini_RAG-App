# ------------- 简易版 知识库chatbot -------------
# @Time: 2026/10/22
# @Author: fan
# version: 2.3 (纯净流式版)
# --------------------------------------------


from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import json
import uvicorn


load_dotenv()
app = FastAPI(
    title = "知识库chatbot",
    description = "一个基于知识库的chatbot",
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 模拟数据库
memorydb = ''

class ChatRequste(BaseModel):
    prompt : str

# ----------------- 上传文件 ----------------
@app.post('/upload')
async def upload(file : UploadFile = File(...)):
    global memorydb
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code = 400, detail = '目前仅支持 TXT 文件。')
    text_b = await file.read()
    try:
        text_str = text_b.decode('utf-8')
        memorydb = text_str
        return {'msg' : '上传成功', 'words' : len(memorydb)}
    except Exception:
        raise HTTPException(status_code = 400, detail = '文件解析失败，请确保是 UTF-8 编码')
# ------------------------------------------

# -------------- 核心生成器 ----------------
async def deepseek_event_generator(user_prompt: str):
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
    
    if not DEEPSEEK_API_KEY:
        yield 'data: [error] 请设置环境变量 DEEPSEEK_API_KEY\n\n'
        return
    
    Headers = {
        "Content-Type" : "application/json",
        "Authorization" : f"Bearer {DEEPSEEK_API_KEY}" 
    }
    
    # 删除了 thinking 和 reasoning_effort 参数
    DataJson = {
        "model": "deepseek-flash",
        "messages": [
            {"role": "system", "content": f"你是一个有用的助手。请根据以下知识库回答：\n{memorydb}"},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True
    }   
    
    try:
        async with httpx.AsyncClient() as client:
            # 取消思考模式后响应很快，timeout 30秒足够了
            async with client.stream('POST', DEEPSEEK_API_URL, json=DataJson, headers=Headers, timeout=30) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        data_str = line[len('data:'):].strip()
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk['choices'][0]['delta']
                            
                            # 只处理最终回答，直接输出文本
                            content = delta.get('content', '')
                            if content:
                                safe_text = content.replace('\n', '')
                                yield f'data: {safe_text}\n\n'
                                
                        except:
                            continue
    except Exception as e:
        yield f'data: [error] {str(e)}\n\n'
#  ----------------------------------------

# --------------- 接口路由 ---------------
@app.post('/chat')
async def chat(req: ChatRequste):
    return StreamingResponse(
        deepseek_event_generator(req.prompt), 
        media_type="text/event-stream"
    )
# -----------------------------------------


# ------------------ 启动服务 -------------
if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
# ---------------------------------------



