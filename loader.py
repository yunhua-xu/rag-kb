from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader    # 三种加载器

def load_pdf(path):    # 读PDF
    loader = PyPDFLoader(path)    # 创建加载器
    return loader.load()    # 返回Document列表

def load_docx(path):    # 读Word
    loader = Docx2txtLoader(path)    # 创建加载器
    return loader.load()    # 返回Document列表

def load_txt(path):    # 读TXT/MD
    loader = TextLoader(path, encoding="utf-8")    # 中文必须指定utf-8，乱码换gbk
    return loader.load()    # 返回Document列表

def load_doc(path):    # ★统一入口：按扩展名自动选加载器
    if path.endswith(".pdf"):    # 是PDF
        return load_pdf(path)    # 走PDF
    if path.endswith(".docx"):    # 是Word
        return load_docx(path)    # 走Word
    return load_txt(path)    # 其他都当文本

if __name__ == "__main__":    # ★直接运行本文件才读文件演示；被 import 时不跑（不然每次import都去读a.pdf）
    # 测试：三种格式各读一个（换成你的真实文件）
    for p in ["a.pdf", "b.docx", "c.txt"]:    # 测试文件清单
        docs = load_doc(p)    # 读文件
        print(p, "→", len(docs), "段")    # 打印读了几段
