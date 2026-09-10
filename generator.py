import os    # os模块
from dotenv import load_dotenv    # .env
from openai import OpenAI    # 客户端
from retriever import hybrid_docs    # ★混合检索：向量路+关键词路 归一化加权融合后的Top-k


load_dotenv()    # 加载key
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
base_url="https://api.deepseek.com")    # 连模型


def generate(q):    # ★问答闭环：检索 → 拼prompt → 调LLM → 返回答案+来源
    docs, metas = hybrid_docs(q)    # ★①先检索（双路召回融合，比只走向量更全）
    if not docs:    # ★库里空/没查到：直接友好兜底，别硬调模型（省token也不瞎答）
        return {"answer": "没在资料里找到相关内容，请先确认已入库。", "sources": []}
    context = "\n---\n".join(docs)    # 把命中的几块拼成一段资料
    prompt = f"只根据以下资料回答。资料里没有就说不知道。\n\n资料：\n{context}\n\n问题:{q}"    # ★RAG灵魂：资料和问题一起发给模型
    resp = client.chat.completions.create(    # 调LLM
         model="deepseek-flash",    # ★模型：必须填官方接口ID（deepseek-flash），写别名/展示名会直接报错
         messages=[{"role": "user", "content": prompt}]    # 发prompt
    )    # 结束调用
    answer = resp.choices[0].message.content    # 取回答
    sources = list(dict.fromkeys(m["src"] for m in metas))    # ★去重来源文件名（dict.fromkeys=去重且保序）
    return {"answer": answer, "sources": sources}    # 返回答案+来源


if __name__ == "__main__":    # ★入口守卫：直接运行本文件才测试；被import时不白调API
    print(generate("什么是RAG"))    # 测试
