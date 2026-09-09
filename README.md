# RAG 知识库

一个能「上传文档 → 按意思检索 → 生成回答」的问答系统。

## 功能
- 文档加载：PDF / Word / TXT / MD
- 混合检索：向量 + BM25
- 生成回答：带来源引用
- 评测：LLM-as-Judge 自动打分

## 运行
1. `pip install -r requirements.txt`
2. 把 KEY 填进 `.env`（DEEPSEEK_API_KEY / ZHIPU_API_KEY）
3. `python -m uvicorn main:app --reload`

## 架构
用户 → FastAPI(`/api/ask`) → 检索 → 生成 → 回答（附来源）