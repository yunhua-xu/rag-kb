# Streamlit = 用Python写网页：代码一存，浏览器自动出界面（先 pip install streamlit）
# 注意：generator.py 已带 if __name__=="__main__": 门——import 它不会触发测试print，直接运行它才自测（Day36已改好）
import streamlit as st# 界面库（st是大家约定俗成的缩写）
from generator import generate# 复用Day36：检索+生成，返回{"answer","sources"}

st.set_page_config(page_title="RAG知识库")# 浏览器标签页标题
st.title("📚 RAG 知识库问答")# 页面大标题

# —— 左侧边栏：上传入口（真正入库=Day32的 load_doc 切块→ingest 进向量库，界面先占位）——
with st.sidebar:# ★with里面缩进的都画在左栏
    up = st.file_uploader("上传 PDF/Word/TXT", type=["pdf", "docx", "txt"])# ★上传框（限制三种格式）
    if up:# 收到文件
        st.info(f"收到 {up.name}——入库链路见Day32 loader+ingest")# 界面提示（进阶自己接上入库）

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
    r = generate(q)# ★直接复用Day36问答闭环（内部已检索+生成，别自己重写）
    with st.chat_message("assistant"):# AI气泡
        st.write(r["answer"])# 答案
        st.caption("📄 来源：" + "、".join(r["sources"]))# ★小字列出来源文件名（防幻觉、可核对）
    st.session_state.history.append(("assistant", r["answer"], r["sources"]))# 记住AI这条+来源（刷新不丢）
