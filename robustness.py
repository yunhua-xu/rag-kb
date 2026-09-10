import os # os模块
import time # 睡眠用
from dotenv import load_dotenv # .env
from openai import OpenAI # 客户端

load_dotenv() # 加载key
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com") # 连模型

def call_llm(prompt, retries=3): # ★带重试的调用（防超时闪退）
    for i in range(retries): # 最多试3次
        try: # ★包住可能失败的操作
            resp = client.chat.completions.create( # 调模型
                model="deepseek-flash", # ★模型：官方接口ID（不是别名、不是展示名）
                messages=[{"role": "user", "content": prompt}], # 内容
                timeout=30 # ★30秒超时，不设会一直等
            ) # 结束
            return resp.choices[0].message.content # 成功就直接返回
        except Exception as e: # ★捕获任何异常
            print(f"第{i+1}次失败：{e}") # 打印失败原因
            if i == retries - 1: # ★最后一次失败：别再等，直接去兜底
                break
            time.sleep(2 ** (i + 1)) # ★指数退避：2秒、4秒…失败越多次等越久
    return "服务暂时不可用" # ★全部失败给兜底答案，不崩

def check_size(path, limit=10_000_000): # ★文件太大/不存在→友好提示
    try:
        size = os.path.getsize(path) # 取文件字节数
    except FileNotFoundError: # ★文件不存在：别崩，给友好提示
        return f"文件不存在：{path}"
    if size > limit: # 超过10MB
        return f"文件太大（{size/1e6:.1f}MB），请传10MB以内" # 友好提示
    return None # 没问题返回None

if __name__ == "__main__": # ★入口守卫：被import时不跑测试（不然一import就真调API）
    print(call_llm("你好")) # 测试重试（key对=真答案；key错/超时=看兜底）
    print(check_size("big.pdf")) # 测试文件限制（big.pdf不存在→友好提示，不崩）
