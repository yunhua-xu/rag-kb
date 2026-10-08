# Dockerfile —— 把整个 RAG 知识库"打包成一台可以搬走的机器"
# 文件名固定就叫 Dockerfile（一个字都不能改，Docker 只认这个名字）
# 用法：docker build -t rag-system:1.0 .        （在项目目录下执行）
# ============================================================
# ★ 这份是照 rag_system 的真实代码写的（不是照抄项目二那份），
#   两处关键差别在文件末尾「和项目二不一样的地方」里写明。


# FROM = 从哪个"基础镜像"开始（镜像=装好系统的光盘模板；容器=拿它跑起来的那台机器）
# python:3.10-slim = 官方 Python 3.10 精简版，自带 pip，体积小（约 120MB）
# 为什么不用 latest？因为 latest 会随时间变，今天能构建、下个月可能就构建失败，版本要写死
FROM python:3.10-slim


# WORKDIR = 工作目录（working directory 的缩写）。进入容器后默认站在哪个文件夹
# 相当于在容器里执行了一次 cd /app；后面的 COPY、RUN、CMD 都相对于这个目录
# ★ 这一条对本项目特别重要：ingest.py 和 retriever.py 里写的是
#   chromadb.PersistentClient(path="./chroma_data")，这个 "./" 就是相对于 WORKDIR 的。
#   所以工作目录一变，向量库的路径就跟着变 —— 容器里它一定是 /app/chroma_data
WORKDIR /app


# ENV = 环境变量（environment 的缩写），设一次后面所有命令都生效
# PYTHONUNBUFFERED=1 = Python 输出不缓存，实时打印日志（否则 docker logs 看不到实时输出）
# PYTHONIOENCODING=utf-8 = 让 Python 的输入输出统一用 utf-8 编码
#   —— 这条是给我们本机踩过的坑准备的：本机 GBK 环境 print emoji 会直接 UnicodeEncodeError
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8


# ★★ 面试必问：为什么先 COPY requirements.txt，而不是直接 COPY . ？ ★★
# Docker 构建是一层一层（layer）来的，每一层只要内容没变就会用缓存，不重新执行。
# 依赖清单（requirements.txt）很少改，源代码（.py）天天改。
# 先拷 requirements.txt 再 pip install，就把"装依赖"这层单独锁成一层：
#   → 以后你只改 .py 文件，这层缓存直接命中，构建只要几秒；
#   → 如果反过来先 COPY . 再装依赖，改一个字就会让缓存失效，每次都要重装全部依赖（几分钟）。
# 一句话记住：把"变得慢的东西"放前面，"变得快的东西"放后面。
COPY requirements.txt .


# RUN = 构建镜像时执行的命令（在容器里跑一条命令）
# pip install -r requirements.txt = 按清单装依赖（-r = read 读取清单文件）
# --no-cache-dir = 不保留 pip 下载缓存，镜像能小几百 MB
# -i https://pypi.tuna.tsinghua.edu.cn/simple = 换清华镜像源，国内装包快很多（不换会超时）
# ★ 本项目依赖比项目二重（chromadb / langchain / streamlit），第一次构建会慢几分钟，属于正常
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


# COPY . . = 把当前目录（宿主机项目目录）的剩余文件全部拷进容器的 /app
#   第一个点 = 宿主机当前目录（构建时所在目录）
#   第二个点 = 容器里的 WORKDIR（也就是 /app）
# ★ 注意：被 .dockerignore 里列出的文件（.env、chroma_data、__pycache__ 等）不会被拷进来
#   .env 不在镜像里 —— 所以这份镜像可以放心发给别人，密钥是运行时从外面传进去的
COPY . .


# EXPOSE = 声明这个容器打算对外用哪些端口（只是"说明书"，真正映射靠 docker run -p / compose ports）
# 8000 = FastAPI 接口（main.py，自带 /docs 调试页）
# 8501 = Streamlit 网页（ui.py）
# 这个镜像两种形态共用，所以两个端口都声明上
EXPOSE 8000 8501


# CMD = 容器启动时默认执行的命令（一个 Dockerfile 只有最后一条 CMD 生效）
# 中括号这种写法叫 exec 格式（推荐），它不经过 shell，能被正确接收停止信号
# "uvicorn" = 启动 FastAPI 的服务器程序；"main:app" = main.py 文件里的 app 这个变量
#   ★ 这里跟项目二不一样：项目二的入口文件叫 api.py，本项目叫 main.py（FastAPI 写在 main.py 里）
# --host 0.0.0.0 = 监听所有网卡，容器外（也就是你的浏览器）才连得进来；写 127.0.0.1 就只有容器自己能用
# --port 8000 = 监听 8000 端口
# ★ 不加 --reload：--reload 是开发时"改代码自动重启"用的，它会常驻一个监视进程，
#   在生产/容器里既不必要又占资源（本机练习时用 --reload 很方便，进了镜像就去掉）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# ============================================================
# 和项目二那份 Dockerfile 不一样的地方（面试问"你几个项目 Docker 一样吗"就答这个）
# ============================================================
# ① 入口文件不同：项目二 `api:app`；本项目 `main:app`
#    —— 因为本项目的 FastAPI 直接写在 main.py 里，没有单独的 api.py
#
# ② 本项目多一个"向量库要持久化"的问题：
#    向量库用的是嵌入版（chromadb.PersistentClient），存在容器里的 /app/chroma_data。
#    容器一删，这个目录就没了 —— 所以必须靠 docker-compose.yml 里的 volumes
#    把宿主机的 chroma_data 挂进来，数据才留得住。
#    ★ 这一点面试很可能被追问，答法见同目录 架构图.md 和 README.md
#
# ③ 本项目没有 healthcheck 的必要性差异：见 docker-compose.yml 里的说明
