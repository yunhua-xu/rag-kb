# RAG 知识库问答系统

把 PDF / Word / TXT 丢进去，用自然语言提问——系统从文档里检索相关内容，交给大模型生成回答，**并给出答案来源**，方便核对、减少幻觉。

## 功能

- **多格式入库**：PDF / Word / TXT 自动按扩展名解析
- **文本切块**：chunk_size / overlap 可调（默认 256 / 50）
- **混合检索**：向量检索（语义）+ BM25（关键词，jieba 中文分词），两路分数归一化后加权融合
- **相关度门槛**：检索结果按余弦相似度过滤，低于阈值（默认 0.28，可配置）的不进 Prompt——检索不到就明确回复未找到，不拿无关内容硬答
- **带来源回答**：Prompt 约束"只根据资料回答"，并返回来源文件名
- **两种使用方式**：网页界面（Streamlit）/ HTTP 接口（FastAPI，自带 /docs 调试页）
- **稳定性**：调用大模型失败自动重试 + 指数退避 + 友好降级
- **效果评测**：LLM-as-Judge 自动打分
- **可选扩展**：扫描件 OCR、重排精排、Docker 编排

## 运行

```bash
pip install -r requirements.txt                  # 安装依赖
# 然后把 .env.example 复制成 .env，填入自己的两个密钥
```

**方式一：网页界面（推荐，上传和提问都在浏览器里完成）**
```bash
streamlit run ui.py
```
打开 http://localhost:8501 → 左侧上传文档 → 下方输入问题。

**方式二：HTTP 接口**
```bash
uvicorn main:app --reload
```
打开 http://127.0.0.1:8000/docs ，可在页面上点按钮测试 `/api/ask`（问答）和 `/api/upload`（上传入库）。

## 架构

```
入库：文档 → loader.py → splitter.py → 智谱embedding-2 → ingest.py → ChromaDB
问答：提问 → retriever.py 双路召回(向量+BM25) → 归一化加权融合 → 相关度门槛过滤 → generator.py 拼Prompt → DeepSeek → 答案+来源
```

详见 [架构图.md](架构图.md)

## 项目结构

| 文件 | 作用 |
|---|---|
| `loader.py` | 按扩展名解析 PDF / Word / TXT |
| `splitter.py` | 长文本切块（chunk_size / overlap） |
| `ingest.py` | 向量化并写入 ChromaDB（同来源覆盖更新） |
| `retriever.py` | 混合检索：向量 + BM25，分数归一化加权融合 |
| `generator.py` | 检索 → 拼 Prompt → 调用 DeepSeek → 答案 + 来源 |
| `main.py` | FastAPI 接口（`/api/ask`、`/api/upload`） |
| `ui.py` | Streamlit 网页界面（含上传入库） |
| `robustness.py` | 超时重试、指数退避、降级兜底 |
| `judge.py` | LLM-as-Judge 自动评测 |
| `reranker.py` | （可选）重排精排，默认未接入主链路 |
| `ocr.py` | （可选）扫描件图片转文字 |
| `sample_docs/` | 示例文档，可直接拿来试 |
| `docker-compose.yml` | API + ChromaDB 容器编排 |

## 配置

`.env`（**不要提交到 Git**）：

```
DEEPSEEK_API_KEY=...      # 生成回答用
ZHIPU_API_KEY=...         # 文本向量化（embedding）用
# MIN_SIMILARITY=0.28     # 可选：检索最低相关度门槛，越大越严格
# RERANKER_MODEL=...      # 可选：启用 reranker.py 精排时才需要
```

## 技术栈

Python · FastAPI · LangChain · ChromaDB · 智谱 embedding-2 · DeepSeek · BM25(rank_bm25) + jieba · Streamlit · Docker

## 修改记录

每次改动的时间 / 文件 / 原因，见 [CHANGELOG.md](CHANGELOG.md)
