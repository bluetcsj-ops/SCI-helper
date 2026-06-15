# 项目交接记录

更新时间：2026-06-15

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的原型工程。当前目标是先建立一个可运行、可扩展的多智能体平台骨架，再逐步接入真实科研数据分析、文献检索、论文生成、审稿和提醒服务。

## 当前完成进度

### 已完成

- 完整工程骨架：`backend/`、`frontend/`、`docs/`、`shared/`、`infra/`。
- FastAPI 后端：
  - 健康检查：`GET /health`
  - Agent 列表：`GET /api/agents/`
  - 项目列表与详情：`GET /api/projects/`
  - 仪表盘：`GET /api/dashboard/`
  - 聊天：`POST /api/chat/`
- React + Vite 前端：
  - “我的研究书房”主页面
  - Project A / Project B 项目卡
  - 任务状态更新
  - 角色对话区
  - 研究方案面板
  - Rhea 监控中心
- SQLite 持久化：
  - `projects`
  - `phases`
  - `tasks`
  - `chat_messages`
  - `project_protocols`
  - `project_plan_drafts`
  - `task_reminders`
- LLM 调用：
  - 默认 DeepSeek
  - 保留 OpenAI 可切换
  - API 调用失败或余额不足时自动回退模拟回复
  - 聊天记录入库
- 角色调整：
  - Rhea Chen 不再作为普通咨询 Agent，而是页面级“全流程实施监控员”
  - 新增 Dr. Vera Protocol，负责论文和实验方案制定
- Project Protocol：
  - 结构化研究方案字段
  - 本地草案生成
  - 从 Dr. Vera 长回复中抽取方案字段
  - 保存到 SQLite
- Rhea 执行计划草案：
  - 根据 Project Protocol 生成阶段和任务草案
  - 草案先预览，不直接覆盖当前项目
  - 用户点击“应用该草案”后才替换当前项目阶段和任务
- Rhea 本地提醒与监控中心：
  - 48 小时提醒
  - 24 小时提醒
  - 逾期提醒
  - 受阻提醒
  - 提醒归档

## 本地启动方式

### 后端

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端验证：

```text
http://localhost:8000/health
http://localhost:8000/docs
```

### 前端

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run dev
```

前端访问：

```text
http://localhost:3000
```

如果 `3000` 被占用：

```powershell
.\node_modules\.bin\vite.cmd --host 0.0.0.0 --port 3001
```

## 环境变量

不要提交真实 `.env`。用 `.env.example` 作为模板。

DeepSeek：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

OpenAI：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4o
```

## 当前验证记录

最近一次验证通过：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\python.exe -m py_compile app\db\models.py app\db\seed.py app\projects\models.py app\reminders\repository.py app\api\routes\reminders.py app\api\router.py
.\.venv\Scripts\python.exe -m pip check

cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run build
```

已额外用临时 SQLite 验证：

- 生成计划草案不会修改当前项目。
- 应用计划草案后才替换阶段和任务。
- 将任务设为 `blocked` 后会生成红色 Rhea 提醒。
- 归档提醒后，该提醒会从活跃列表移除。

## Git 上传安全规则

以下内容不能上传：

- `backend/.env`
- `backend/.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/sci_workshop.db`
- `*.db`
- `*.log`
- `My SCI article/` 内真实论文和个人资料

当前 `.gitignore` 已覆盖这些内容。

## 下一步建议

建议下一阶段进入科研功能薄切片：

1. Dr. Data Lin 数据需求清单模块。
2. CSV 上传原型。
3. 数据质量检查报告。
4. 简单统计分析和图表生成。
5. 把分析结果交给 Alex Writer 生成结果段落草稿。

如果继续做项目管理侧，则下一步是：

1. 将 Rhea 本地提醒接入 Celery / Redis。
2. 新增 Telegram / Email 真实发送配置。
3. 增加提醒发送日志和失败重试。

## 换电脑恢复步骤

1. 克隆仓库。
2. 根据 `.env.example` 创建 `backend/.env`。
3. 后端创建虚拟环境并安装依赖：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

4. 前端安装依赖：

```powershell
cd frontend
npm.cmd install
```

5. 分别启动后端和前端。

首次启动后端时，会自动创建 SQLite 表和演示项目数据。
