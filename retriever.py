import jieba   # ★中文分词（BM25前提）
from rank_bm25 import BM25Okapi         # 关键词检索
import chromadb     # 向量库
import os           # 读环境变量
from dotenv import load_dotenv      # .env
from zhipuai import ZhipuAI         # 智谱embedding


load_dotenv()   # 读key
emb_client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))    # embedding客户端


def embed(q):     # 文字→向量
    r = emb_client.embeddings.create(model="embedding-2",input=[q])     #调智谱
    return r.data[0].embedding


db = chromadb.PersistentClient(path="./chroma_data")     # 打开之前建的库
col =db.get_or_create_collection("kb_zsk")      # 取集合


def vector_search(q, k=5):          # ★向量路：按“意思”找
    hits = col.query(query_embeddings=[embed(q)], n_results=k)    # 向量路：问题先转向量再查（和入库同一模型）
    return hits["ids"][0]           # 返回命中的id列表


def bm25_search(q, k=5):                    # ★BM25路：按"关键词"找
    data = col.get(include=["documents"])   # 把库里全部原文+id一起搬出来
    docs, ids = data["documents"], data["ids"]   # 第i篇原文 ⇄ ids[i] 同位置
    tok = [list(jieba.cut(d)) for d in docs]
    bm25 = BM25Okapi(tok)
    scores = bm25.get_scores(list(jieba.cut(q)))
    top = sorted(range(len(docs)), key=lambda i: -scores[i])[:k]
    return [ids[i] for i in top]   # ★按下标找真id返回（不再是"0"这种下标）

def hybrid(q, k=5):                 # 融合：两路都真id，去重才对得上
    a = vector_search(q, k)
    b = bm25_search(q, k)
    return list(dict.fromkeys(a + b))[:k]

if __name__ == "__main__":    # ★直接运行本文件才跑真测试；被别人 import 时不跑（省得每次import都调一次API）
    # ★真测试：问一句，看它真捞回啥（不加这段，上面的函数都不会被调用）
    q = "Python是什么"
    hits = hybrid(q, 2)
    print("问题:", q)
    print("命中的id:", hits)
    texts = col.get(ids=hits, include=["documents"])["documents"]
    print("捞回的原文:", texts)
