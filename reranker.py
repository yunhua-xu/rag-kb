# 可选精排模块：先粗召回一批候选，再用重排模型"问题-候选"逐对打分，挑最相关的排前面。
# ⚠ 默认不参与主链路（main.py / ui.py 不会 import 它）。要启用需要两步：
#   ① pip install flagembedding
#   ② 在 .env 里配 RERANKER_MODEL=本地模型路径（如 D:/models/bge-reranker-base）或模型名（走在线下载）
import os    # 读环境变量
from dotenv import load_dotenv    # .env

load_dotenv()    # 加载配置
MODEL_PATH = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")    # ★模型从配置读，不再写死路径（换台电脑也能跑）

try:    # ★没装 flagembedding 时，整个文件不至于一 import 就报错
    from FlagEmbedding import FlagReranker    # 重排模型（固定写法）
    reranker = FlagReranker(MODEL_PATH)    # 加载模型
except ImportError:    # 没装这个库
    reranker = None    # 置空，调用时给可执行的提示


def rerank(q, candidates):    # q=问题；candidates=候选清单
    if reranker is None:    # ★没装依赖：给出能照做的提示，而不是抛一堆看不懂的报错
        raise RuntimeError("未启用精排：请先 pip install flagembedding，并在 .env 配置 RERANKER_MODEL")
    pairs = [[q, c] for c in candidates]    # 问题 + 每条候选 组成一对
    scores = reranker.compute_score(pairs)    # 打分（越高越相关）
    if not isinstance(scores, list):    # 只有1条候选时返回的是单个数字
        scores = [scores]    # 包成列表防报错
    order = sorted(range(len(candidates)), key=lambda i: -scores[i])    # 分高的排前面
    return [candidates[i] for i in order]    # 按新顺序返回


if __name__ == "__main__":    # ★入口守卫：直接运行本文件才演示；被 import 时不跑（不然一 import 就去加载模型）
    print(rerank("RAG是什么", ["Python教程", "RAG是检索增强生成", "今天天气不错"]))    # 最相关那条应排最前
