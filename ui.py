# 网页界面（Streamlit）：启动命令是 streamlit run ui.py（不是 python ui.py）
# 注意：generator.py 带 if __name__=="__main__" 守卫——import 它不会触发测试print，直接运行它才自测
# ★侧边栏上传 = 真入库（不是摆设）：传完文件立刻就能提问
import os# 路径处理 + 用完删临时文件
import tempfile# ★临时文件：上传的内容在内存里，而loader只认磁盘路径，所以先落盘
import streamlit as st# 界面库（st是大家约定俗成的缩写）
from loader import load_doc# ①读文件（PDF/Word/TXT→文字）
from splitter import split_text# ②切块
from ingest import ingest# ③转向量存进向量库
from generator import generate# 问答闭环：内部自己检索+生成，返回{"answer","sources"}

st.set_page_config(page_title="RAG知识库")# 浏览器标签页标题
st.title("📚 RAG 知识库问答")# 页面大标题

# —— 左侧边栏：上传入口（★真入库：load_doc读 → split_text切 → ingest存）——
with st.sidebar:# ★with里面缩进的都画在左栏
    up = st.file_uploader("上传 PDF/Word/TXT", type=["pdf", "docx", "txt"])# ★上传框（限制三种格式）
    if up:# 收到文件
        mark = f"{up.name}-{up.size}"# ★这份文件的"身份证"=文件名+大小（用来认出是不是同一份）
        if st.session_state.get("ingested") != mark:# ★★关键：是新的文件才入库
            # 为什么非要判断？Streamlit每点一下（提问/打字/上传）都会把整个文件从头重跑一遍。
            # 不记住"这份入过库了"，就会每问一个问题重新入一次库——重复烧embedding接口，又慢又费钱。
            suffix = os.path.splitext(up.name)[1] or ".txt"# 取扩展名（.pdf/.docx/.txt），没有就按txt处理
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:# ①先落成临时文件（loader只认路径）
                f.write(up.getvalue())# 把上传的字节写进临时文件
                tmp = f.name# 记住临时文件的路径
            try:
                with st.spinner("正在入库，请稍等…"):# ★转圈提示（要调embedding接口，大文件几秒到几十秒）
                    docs = load_doc(tmp)# ①读文件（自动按扩展名选加载器）
                    text = "\n".join(d.page_content for d in docs)# 把每段文字拼成全文
                    if not text.strip():# ★一个字都没读出来（多半是扫描件/图片PDF）
                        st.warning("没读到文字（可能是扫描件），先用 ocr.py 转成文字再传")# 友好提示，别硬入库
                    else:
                        chunks = split_text(text)# ②切块（默认256字一块、重叠50字）
                        ingest(chunks, up.name)# ③入库（用文件名当来源标记；重传同名文件=覆盖更新）
                        st.session_state["ingested"] = mark# ★记下"这份已入库"，下次重跑不再重复入
                        st.success(f"✅ {up.name} 已入库 {len(chunks)} 块，现在可以直接提问了")
            except Exception as e:# ★兜底：入库失败也不让页面崩
                st.error(f"入库失败：{e}")
            finally:
                os.unlink(tmp)# 用完删临时文件（不占磁盘）
        else:
            st.success(f"✅ {up.name} 已入库，可直接提问")# 同一份文件重复上传时，不再入库

# —— 主区：聊天 ——
if "history" not in st.session_state:# ★会话记忆：刷新网页不清空
    st.session_state.history = []# 历史=[(角色,文本,来源列表),...]，assistant才带来源

for item in st.session_state.history:# 每帧把历史气泡重放一遍（Streamlit从上到下重跑）
    role, text = item[0], item[1]# 取出角色和文本
    with st.chat_message(role):# ★按角色画气泡：user在左、assistant在右
        st.write(text)# 写内容
        if role == "assistant" and item[2]:# ★AI消息补来源小字（刷新后也不丢）
            st.caption("📄 来源：" + "、".join(item[2]))

q = st.chat_input("问点什么…")# ★底部输入框
if q:# 用户发来问题
    with st.chat_message("user"):# 用户气泡
        st.write(q)
    st.session_state.history.append(("user", q, []))# 先记住用户这条（来源为空列表）
    r = generate(q)# ★直接复用问答闭环（内部已检索+生成，别自己重写）
    with st.chat_message("assistant"):# AI气泡
        st.write(r["answer"])# 答案
        st.caption("📄 来源：" + "、".join(r["sources"]))# ★小字列出来源文件名（防幻觉、可核对）
    st.session_state.history.append(("assistant", r["answer"], r["sources"]))# 记住AI这条+来源（刷新不丢）
