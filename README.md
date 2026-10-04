# 求职导航平台

面向大学生的求职准备工具，包含职位搜索、岗位分析、学习计划、简历检查和面试练习。

前端使用 React、TypeScript、Ant Design 和 Vite；后端使用 FastAPI、Pydantic 和 Playwright。
职位保存在 `backend/data/jobs.json`，日志保存在 `backend/logs`。配置和运行数据不提交到仓库。

## 本地运行

需要 Python 3.10 及以上、Node.js 22。先启动后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python init_data.py
.venv\Scripts\python main.py
```

Linux/macOS 使用 `.venv/bin/python`，复制配置使用 `cp .env.example .env`。
Linux 如果缺少浏览器系统库，运行 `python -m playwright install --with-deps chromium` 安装所需依赖。
`init_data.py` 只在数据为空时添加 15 条演示岗位，不代表正在招聘的职位。

在另一终端启动前端：

```sh
cd frontend
npm ci
npm run dev
```

访问 `http://localhost:5173`，接口文档位于 `http://localhost:8000/docs`。
Windows 下后端关闭自动重载，修改代码后需重启，以保证爬虫能启动浏览器子进程。
也可以运行 `.\deploy.ps1 -Mode local` 或 `bash deploy.sh local`，脚本会安装依赖并在 4173 端口提供前端预览。

## 模型配置

在后端的 `.env` 中填写 `AI_API_KEY`，`AI_PROVIDER` 可选 `openai`、`dashscope`、`zhipu`。
只设置提供商时使用对应的默认地址和模型，也可以通过 `AI_API_BASE_URL` 和 `AI_MODEL` 覆盖。
JD 解析、学习计划和面试评估会调用模型；未配置、调用失败或回复格式不正确时使用规则处理。
简历检查与排版整理使用规则，不改写个人经历的事实。

职位获取读取招聘网页搜索结果，不用模型编造招聘信息。结果可能受网络、网站访问限制和搜索索引更新影响，投递前请查看原始招聘页面。

## Docker

```sh
cp backend/.env.production.example backend/.env.production
docker compose up -d --build
```

按需修改生产配置中的模型参数和访问域名。前端访问 `http://localhost`，后端仅绑定本机 8000 端口。
配置文件通过 Compose 传入后端，浏览器随后端镜像安装；生产模式关闭接口文档。
`.\deploy.ps1 -Mode docker` 和 `bash deploy.sh docker` 会在缺少生产配置时复制模板并检查服务状态。

使用 `docker compose logs -f` 查看日志，`docker compose down` 停止服务。
职位和日志分别存放在数据卷中；删除数据卷会清除对应数据，应先备份。
当前 JSON 存储采用进程内事务锁，服务需使用单个 worker。多进程或多实例部署需要先更换数据库存储。

## 验证与维护

```sh
cd backend
python -m unittest discover -s tests -v
cd ../frontend
npm ci
npm run build
```

后端测试使用临时目录和模拟外部服务，不依赖已启动的服务器、模型密钥或真实招聘网站。
提交说明以中文为主，更新现有分支，不自动新建分支。保留源码、依赖锁文件、配置模板与有效测试，避免提交编辑器工作目录、开发过程记录、密钥和运行数据。
