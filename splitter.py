from langchain_text_splitters import RecursiveCharacterTextSplitter #  ★ 智能切分器



def split_text(text, size=256, overlap=50):    # ★ 切分函数
    splitter = RecursiveCharacterTextSplitter(    # 创建切分器
        chunk_size=size,        # 每块多大
        chunk_overlap=overlap          # 相邻块重叠：防止切断语义
    )   # 结束创建
    return splitter.split_text(text)        # 纯文本切，返回块列表


if __name__ == "__main__":    # ★直接运行本文件才做切分实验；被 import 时不跑（import 干净无副作用）
    long_text = ("RAG是检索增强生成，它把检索和生成结合起来。") * 30    # 模拟长文档（30遍）



    # 实验1： 小块（256字）
    small = split_text(long_text, 256, 50)      # 切小块
    # 实验2： 大块（1024字）
    big = split_text(long_text, 1024, 50)       # 切大块
    print("256 ->", len(small),"块; 1024 ->", len(big), "块")     #对比块数
    print("小块第1块:", small[0][:30],"...")    # 看内容

    # 面试：chunk_size 越碎检索越准但是越贵；越糙越省但可能打不准。这是调参核心。
