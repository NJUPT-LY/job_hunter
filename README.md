# 职路AI - 大学生求职导航平台

> 参加TRAE「AI 无限职场」SOLO 挑战赛公益赛道 - 帮助大学生跨越求职迷茫

## 项目简介

职路AI是一个面向大学生的求职导航平台，通过AI技术帮助求职者：

- **了解岗位**：爬取真实招聘信息，AI智能解析JD，把招聘描述翻译为真实工作内容与能力要求
- **明确路径**：根据目标岗位生成个性化阶段性行动清单
- **提升能力**：AI简历优化与模拟面试，提升求职竞争力

## 技术栈

### 前端

- React 18 + TypeScript
- Vite
- Ant Design
- Zustand (状态管理)
- React Router v6
- ECharts (数据可视化)
- Axios

### 后端

- Python 3.10+
- FastAPI
- Uvicorn
- Requests + BeautifulSoup4 (爬虫)

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.10

### 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 运行项目

```bash
# 启动后端（端口8000）
cd backend
python main.py

# 启动前端（端口5173）
cd frontend
npm run dev
```

访问 <http://localhost:5173> 开始使用

## 项目结构

```
job_hunter/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── pages/            # 页面
│   │   └── services/         # API服务
│   └── package.json
├── backend/                  # 后端项目
│   ├── app/
│   │   ├── api/              # API路由
│   │   ├── core/             # 配置
│   │   ├── models/           # 数据模型
│   │   └── services/         # 业务逻辑
│   └── requirements.txt
└── README.md
```

## 功能模块

| 模块   | 说明          | 状态 |
| ---- | ----------- | -- |
| 职位搜索 | 爬取并展示招聘信息   | ✅  |
| 岗位分析 | AI智能解析JD    | ✅  |
| 能力差距 | 对比用户技能与岗位要求 | ✅  |
| 行动清单 | 生成个性化学习路径   | ✅  |
| 简历优化 | AI评估与优化简历   | ✅  |
| 模拟面试 | AI模拟面试与反馈   | ✅  |

## 配置

复制 `backend/.env.example` 为 `backend/.env` 并配置你的AI API密钥：

```env
AI_API_KEY=your_api_key_here
AI_API_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-3.5-turbo
```

<br />

# License

MIT
