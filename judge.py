# 评测模块：LLM-as-Judge 自动打分（Day24 移植进项目）
import os# os模块（读env）
import re# ★正则：抓AI回答里的数字
from dotenv import load_dotenv# .env
from openai import OpenAI# 客户端

load_dotenv()# 从.env加载key
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")# 连接（key放.env，别写死在代码里）

RUBRIC = "你是评委。回答正确结构清晰给5分，基本正确有缺失给3分，错误给1分。只输出数字。"# ★打分标准

def judge_answer(q, answer):# ★给一条问答打分
    prompt = RUBRIC + f"\n\n问题：{q}\n\n回答：{answer}"# 标准+题目+答案拼一起
    resp = client.chat.completions.create(# 让AI当评委
        model="deepseek-v4-flash",# 模型
        messages=[{"role": "user", "content": prompt}]# 发prompt
    )# 结束
    return resp.choices[0].message.content# 返回分数文本（可能是"4分""5."这种带字的）

def to_score(s):# ★把AI回的分数文本变成数字
    m = re.search(r"\d+", s)# ★抓第一个数字（"4分""5."都能抓到）
    return int(m.group()) if m else 0# 抓到转int，抓不到给0——别直接int(s)，会崩

def eval_dataset(pairs):# ★跑整个评测集
    scores = []# 存每条分数
    for q, a in pairs:# 逐条评测
        s = judge_answer(q, a)# 打分
        scores.append(to_score(s))# ★转数字前先正则兜底
    return sum(scores) / len(scores) if scores else 0# 平均分（空评测集给0，不除零）

if __name__ == "__main__":# ★入口守卫：被评测主程序import时不自动跑测试
    print(eval_dataset([("什么是RAG？", "RAG是检索增强生成")]))# 测试平均分
