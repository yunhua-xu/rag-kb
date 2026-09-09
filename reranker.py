from FlagEmbedding import FlagReranker                          # 精排模型（固定名）
reranker = FlagReranker("D:/models/bge-reranker-base")          # 读本地模型（已下好，秒开）

def rerank(q, candidates):                                      # q=问题；candidates=候选清单
    pairs = [[q, c] for c in candidates]                        # 问题+每条候选 组对
    scores = reranker.compute_score(pairs)                      # 打分（越高越相关）
    if not isinstance(scores, list):                            # 只有1条候选时返回单个数字
        scores = [scores]                                       # 包成列表防报错
    order = sorted(range(len(candidates)), key=lambda i: -scores[i])   # 分高的排前面
    return [candidates[i] for i in order]                       # 按新顺序返回

print(rerank("RAG是什么", ["Python教程", "RAG是检索增强生成", "今天天气不错"]))  # 最相关那条应排最前
