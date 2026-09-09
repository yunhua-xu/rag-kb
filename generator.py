import os # os模块
from dotenv import load_dotenv # .env
from openai import OpenAI # 客户端
import chromadb # 向量库
from zhipuai import ZhipuAI # 智谱embedding(和入库同一个)


load_dotenv() # 加载key
emb_client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY")) # embedding客户端
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
base_url="https://api.deepseek.com")     # 连模型
db = chromadb.PersistentClient(path="./chroma_data")    # 打开库
col = db.get_or_create_collection("kb_zsk")     # 取集合


def embed(q): #★ 文字→向量（和入库同一个模型，维度才一致）
    r = emb_client.embeddings.create(model="embedding-2", input=[q]) # 调智谱
    return r.data[0].embedding # 返回向量


def retrieve(q, k=5): # ★检索
    hits = col.query(query_embeddings=[embed(q)],n_results=k) # 查询（问题先转向量，同一模型）
    docs = hits["documents"][0]     # 命中内容
    metas = hits["metadatas"][0]    # ★命中来源（引用答案用）
    return docs, metas # 返回内容+来源


def generate(q): # ★生成回答：检索→拼prompt→掉LLM
    docs, metas =retrieve(q)    # 先检索
    if not docs: # ★库里没入库/没查到：直接友好兜底，别硬调模型
        return{"answer":"没在资料里找到相关尼尔，请先确认已入库。","sources":[]}
    context = "\n---\n".join(docs)
    prompt = f"只根据以下资料回答。资料里没有就说不知道。\n\n资料：\n{context}\n\n问题:{q}" # ★RAG灵魂：资料问题一起发
    resp = client.chat.completions.create( # 调LLM
         model="deepseek-v4-flash", # 模型
         messages = [{"role":"user","content":prompt}] # 发prompt
    ) # 结束调用
    answer = resp.choices[0].message.content # 取回答
    sources = list(set(m["src"] for m in metas)) # ★去重来源文件名
    return{"answer": answer,"sources": sources} # 返回答案+来源

if __name__ == "__main__": # ★入口守卫：直接运行本文件才测试；被import时不白调API
         print(generate("什么是RAG")) # 测试
    
