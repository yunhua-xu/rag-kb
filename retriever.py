import jieba    # ★中文分词（BM25的前提：中文没有空格，得先切成词才有"词"可数）
from rank_bm25 import BM25Okapi    # 关键词检索算法（按词频算相关度）
import chromadb    # 向量库
import os    # 读环境变量
from dotenv import load_dotenv    # .env
from zhipuai import ZhipuAI    # 智谱embedding


load_dotenv()    # 读key
emb_client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))    # embedding客户端

# ★最低相关度门槛：问句和候选块的余弦相似度低于它，就当作"不相关"——不进Prompt，也不列进来源。
# 为什么需要它：没有门槛时，库里只要有东西，任何问题都会硬凑出Top-k，结果是
#   ① 问个库里没有的问题，它也拿无关内容去答 ② 来源里混进一堆不相干文件名。
# ⚠ 这个数值跟embedding模型有关。本机用智谱embedding-2实测：
#   相关的问题 top 在 0.37~0.44，不相关的问题 top 在 0.20 以下 → 取中间值 0.28。
#   换模型或换语料要重新量（拍脑袋定阈值 = 埋坑），所以做成可配置。
MIN_SIM = float(os.getenv("MIN_SIMILARITY", "0.28"))

db = chromadb.PersistentClient(path="./chroma_data")    # 打开之前建的库
col = db.get_or_create_collection("kb_zsk")    # 取集合


def embed(q):    # 文字→向量
    r = emb_client.embeddings.create(model="embedding-2", input=[q])    # 调智谱
    return r.data[0].embedding    # 返回向量


def _cosine(a, b):    # ★余弦相似度：只比"方向"不比"长短"，越大越像；用来判断到底相不相关
    s = sum(float(x) * float(y) for x, y in zip(a, b))    # 点积
    na = sum(float(x) * float(x) for x in a) ** 0.5    # a的长度
    nb = sum(float(y) * float(y) for y in b) ** 0.5    # b的长度
    return s / (na * nb) if na and nb else 0.0    # 各自除以长度=归一化；有任意一个长度为0就返回0


def vector_scores(q, k=5, qv=None):    # ★向量路：按"意思"找；返回（id列表, 相似度列表）
    if qv is None:    # 没传现成向量就自己算
        qv = embed(q)
    hits = col.query(query_embeddings=[qv], n_results=k)    # 问题向量去查（和入库同一个模型，维度才对得上）
    ids = hits["ids"][0]    # 命中的id
    dists = hits["distances"][0]    # 距离（越小越像）
    return ids, [1.0 / (1.0 + d) for d in dists]    # 距离→相似度（越大越像）；后面还要归一化，这步只为统一方向


def bm25_scores(q, k=5):    # ★关键词路：按"字面"找；返回（id列表, 分数列表）
    data = col.get(include=["documents"])    # 把库里全部原文+id搬出来
    docs, ids = data["documents"], data["ids"]    # 第i篇原文 ⇄ ids[i] 同位置
    if not docs:    # ★空库：直接返回空，别让BM25去建空索引
        return [], []
    tok = [list(jieba.cut(d)) for d in docs]    # 每篇原文分词（中文必须先分词）
    bm25 = BM25Okapi(tok)    # 建索引
    scores = bm25.get_scores(list(jieba.cut(q)))    # 给库里每一篇打分
    top = sorted(range(len(docs)), key=lambda i: -scores[i])[:k]    # 取分数最高的k篇
    return [ids[i] for i in top], [scores[i] for i in top]    # 下标换回真id + 对应分数


def _norm(scores):    # ★把一组分数压到 0~1
    if not scores:    # 空列表
        return []
    lo, hi = min(scores), max(scores)    # 最小/最大
    if hi == lo:    # 全一样大：避免除以0
        return [1.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]    # 否则线性压缩到0~1


def hybrid(q, k=5, alpha=0.5, qv=None):    # ★混合检索：两路各自归一化 → 加权融合 → 排序取前k个id
    v_ids, v_scores = vector_scores(q, k, qv=qv)    # 向量路
    b_ids, b_scores = bm25_scores(q, k)    # 关键词路
    v_scores, b_scores = _norm(v_scores), _norm(b_scores)    # ★必须先归一化：向量相似度和BM25分数不是一个量纲，直接相加没有意义
    fused = {}    # 融合分：id → 总分
    for i, s in zip(v_ids, v_scores):    # 向量路贡献 alpha 权重
        fused[i] = fused.get(i, 0.0) + alpha * s
    for i, s in zip(b_ids, b_scores):    # 关键词路贡献 1-alpha 权重；两路都命中的会累加，自然排更前
        fused[i] = fused.get(i, 0.0) + (1 - alpha) * s
    return [i for i, _ in sorted(fused.items(), key=lambda kv: -kv[1])][:k]    # 按融合分从高到低取k个


def hybrid_docs(q, k=5, alpha=0.5, min_sim=None):    # ★给生成环节用：融合 → 过相关度门槛 → 返回（原文列表, 来源列表）
    if min_sim is None:    # 没指定就用 .env 里配的门槛
        min_sim = MIN_SIM
    qv = embed(q)    # ★问题向量只算一次：向量路和下面的门槛都用它（省一次接口调用）
    ids = hybrid(q, k, alpha, qv=qv)    # 先拿融合后的id
    if not ids:    # 库是空的 / 一条都没命中
        return [], []    # 返回空，让上层去走兜底
    data = col.get(ids=ids, include=["documents", "metadatas", "embeddings"])    # 连向量一起取回来（门槛要用）
    pos = {i: n for n, i in enumerate(ids)}    # id → 相关度名次
    rows = sorted(zip(data["ids"], data["documents"], data["metadatas"], data["embeddings"]), key=lambda t: pos[t[0]])    # ★col.get不保证按传入顺序返回，必须自己按名次重排
    rows = [r for r in rows if _cosine(qv, r[3]) >= min_sim]    # ★相关度门槛：不够像的直接丢掉——宁可回"没找到"，也不拿无关内容硬答
    return [r[1] for r in rows], [r[2] for r in rows]    # 原文、来源（保持同一顺序）


if __name__ == "__main__":    # ★直接运行本文件才跑真测试；被别人 import 时不跑（省得每次import都调一次API）
    q = "年假有几天"    # 测试问题（库里已有 sample_docs 时能命中）
    print("问题:", q)
    print("融合后命中的id:", hybrid(q, 3))
    docs, metas = hybrid_docs(q, 3)
    print("过门槛后捞回的原文:", [d[:30] for d in docs])
    print("来源:", [m["src"] for m in metas])
    print("无关问题（应捞不到）:", hybrid_docs("今天天气怎么样", 3)[0])    # 门槛生效的证明
