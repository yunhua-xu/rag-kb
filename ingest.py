import os           # os模块
import chromadb      # 向量库
from dotenv import load_dotenv      # .env
from zhipuai import ZhipuAI         # ★智谱embedding（DS没有）


load_dotenv()       #加载key
emb_client =ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))   # embedding客户端


def embed(text):    # ★文字→向量
    r = emb_client.embeddings.create(model="embedding-2", input=[text]) #调智谱
    return r.data[0].embedding      # 取出向量（一长串数字）


db = chromadb.PersistentClient(path="./chroma_data")  # ★持久化到磁盘（重启不丢）
col = db.get_or_create_collection("kb_zsk")     # 建（或取）集合


def ingest(chunks, src_name):   #★入库链路：切块→向量→存库
    col.delete(where={"src": src_name})   # ★先删这个来源的旧记录：同一份文档重复跑不报 DuplicateIDError
    vecs = [embed(c) for c in chunks]    # 每块都转向量
    col.add(       # 批量存库
         ids=[f"{src_name}-{i}" for i in range(len(chunks))],      # ★唯一id：文件名 序号

              documents=chunks,     # 原文内容
              embeddings=vecs,      # 对应的向量
              metadatas=[{"src": src_name}for _ in chunks]      # 来源标记（引用答案用）
     )      # 结束add
    print(f"入库{len(chunks)}块")      # 提示


if __name__ == "__main__":    # ★只在"直接运行本文件"时跑下面演示；被 import 时不跑（不重复入库）
    # 测试： 先存3句， 再查一句， 闭环通=成功
    ingest(["Python语法简单","RAG是检索增强生成","向量数据库存向量"],"demo")   # 入库
             
    q_vec = embed("AI是怎么检索知识")          # 问题也转向量（和入库同一个embed函数=同一维度）
    r = col.query(query_embeddings=[q_vec], n_results=1)    # 拿向量去查，不再传文字
    print(r["documents"])   # 打印命中内容
             
