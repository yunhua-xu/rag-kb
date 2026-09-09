# main.py = FastAPI 主入口：把"检索+生成"和"上传入库"做成接口给网页/curl 调（Day29空壳→Day36补两个端点）
import os    # os模块（拼路径、删临时文件）
import tempfile    # 临时文件（上传先落盘再读）
from fastapi import FastAPI    # FastAPI主类
from fastapi.middleware.cors import CORSMiddleware    # 跨域（网页从别的端口调要开）
from fastapi import UploadFile    # 上传文件的类型
from pydantic import BaseModel    # 请求体模型（自动校验JSON）
from loader import load_doc    # ①读文件→Document列表（按扩展名分流PDF/Word/TXT）
from splitter import split_text    # ②切块
from ingest import ingest    # ③存进向量库（chunks, src_name）
from generator import generate    # ★问答核心：检索+拼prompt+调DeepSeek（自己带兜底）

app = FastAPI()    # 创建应用
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])    # 全放开跨域（本地练习够用）


class AskRequest(BaseModel):    # /api/ask 收到的请求体长这样
    question: str    # {"question": "什么是RAG"} 里的 question


@app.post("/api/ask")    # ★问答端点：POST + JSON
def ask(req: AskRequest):    # FastAPI 自动把请求体转成 AskRequest 对象
    r = generate(req.question)    # ★直接复用 generator：里面自己检索、自己兜底
    return {"answer": r["answer"], "sources": r["sources"]}    # 返回 答案+来源


@app.post("/api/upload")    # ★上传入库端点：POST + 文件
async def upload(file: UploadFile):    # async=异步；file=上传的文件对象
    suffix = os.path.splitext(file.filename)[1] or ".txt"    # 取扩展名（.pdf/.docx/.txt）
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:    # 先存成临时文件（loader只认路径）
        f.write(await file.read())    # 把上传内容写进临时文件
        tmp = f.name    # 记住临时文件路径
    try:
        docs = load_doc(tmp)    # ①读文件（自动按扩展名选PDF/Word/TXT加载器）
        text = "\n".join(d.page_content for d in docs)    # 把每段文字拼成全文（page_content=文档内容）
        chunks = split_text(text)    # ②切块（默认256字一块、重叠50字防切断语义）
        ingest(chunks, file.filename)    # ③入库（以文件名当来源标记，可重复传同一文件=覆盖更新）
    finally:
        os.unlink(tmp)    # 用完删临时文件（不占磁盘）
    return {"message": f"入库 {len(chunks)} 块"}    # 告诉调用方入了几块


# 启动：uvicorn main:app --reload   （main=文件名，app=变量名；--reload=改代码自动重启）
# 测问答：   curl -X POST http://127.0.0.1:8000/api/ask -H "Content-Type: application/json" -d '{"question":"什么是RAG"}'
# 测上传：   curl -X POST http://127.0.0.1:8000/api/upload -F "file=@c.txt"
# 文档页：   浏览器打开 http://127.0.0.1:8000/docs 可在线点按钮测试
