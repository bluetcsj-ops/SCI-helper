# 使用方法

本文档说明当前 v0.1 原型的启动、访问和基础使用方式。

## 1. 启动后端

打开一个 PowerShell 窗口：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

看到以下日志时，说明后端已经正常启动：

```text
Application startup complete.
```

后端验证地址：

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## 2. 启动前端

再打开第二个 PowerShell 窗口：

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run dev
```

如果 `3000` 被占用，可以临时使用：

```powershell
.\node_modules\.bin\vite.cmd --host 0.0.0.0 --port 3001
```

浏览器访问：

```text
http://localhost:3000
```

或：

```text
http://localhost:3001
```

后端窗口和前端窗口都需要保持运行。

## 3. 使用“我的研究书房”

进入前端页面后，可以完成以下操作：

- 查看总体完成度、活跃项目数、风险状态和 Rhea 的监控提示。
- 查看 `Project A` 与 `Project B` 的论文进度卡。
- 点击项目卡片，切换当前关联项目。
- 在“Rhea 监控中心”查看当前项目的逾期、受阻和临近截止提醒。
- 对已经处理的提醒点击“归档”，让它从活跃提醒列表中移除。
- 在“本阶段任务”区域更新任务状态，项目进度和风险状态会自动刷新。
- 在“研究方案”区域生成草案、编辑研究问题、终点、数据需求、实验流程和统计路线，并保存到 SQLite。
- 在“研究方案”区域点击“草案”，让 Rhea 生成执行计划草案；确认预览后再点击“应用该草案”替换当前项目计划。
- 点击五个可咨询智能体入口，切换当前协作角色。
- 在聊天框输入问题，例如：

```text
请帮我制定实验方案
```

## 4. 使用研究方案模块

研究方案模块对应 Dr. Vera Protocol 的产出沉淀。

推荐流程：

1. 先选中 `Project A` 或 `Project B`。
2. 与 `Dr. Vera Protocol` 对话，获得研究方案建议。
3. 在 Dr. Vera 的回复气泡下点击“写入研究方案”，系统会自动抽取字段并保存。
4. 如需从空白状态开始，也可以在“研究方案”面板点击“草案”，生成本地结构化草案。
5. 根据真实课题修改各字段。
6. 点击“保存”，内容会写入本地 SQLite。
7. 点击“草案”，Rhea 会根据研究方案生成执行计划草案。
8. 在下方预览阶段、任务、截止日期和交付物摘要。
9. 确认无误后点击“应用该草案”，当前项目的阶段和任务才会被替换。

当前保存字段包括：

- 研究问题
- 研究假设
- 研究类型
- 主要终点
- 次要终点
- 纳入标准
- 排除标准
- 数据需求
- 实验流程
- 统计路线
- 目标期刊
- Rhea 里程碑

## 5. 使用 Swagger 测试 API

Swagger 是 FastAPI 自动生成的接口测试网页：

```text
http://localhost:8000/docs
```

常用接口：

- `GET /health`：检查后端是否运行。
- `GET /api/agents/`：查看五个可咨询智能体配置。
- `GET /api/projects/`：查看 Project A / Project B。
- `GET /api/dashboard/`：查看仪表盘摘要和 Rhea 监控信息。
- `PATCH /api/projects/{project_id}/tasks/{task_id}`：更新任务状态。
- `GET /api/projects/{project_id}/reminders`：查看 Rhea 本地监控提醒。
- `POST /api/projects/{project_id}/reminders/refresh`：重新生成 Rhea 本地监控提醒。
- `PATCH /api/projects/{project_id}/reminders/{reminder_id}/dismiss`：归档指定提醒。
- `GET /api/projects/{project_id}/protocol`：读取研究方案。
- `POST /api/projects/{project_id}/protocol/draft`：生成研究方案草案。
- `POST /api/projects/{project_id}/protocol/extract`：从 Dr. Vera 回复中抽取并保存研究方案。
- `PUT /api/projects/{project_id}/protocol`：保存研究方案。
- `GET /api/projects/{project_id}/plan/drafts`：查看计划草案列表。
- `POST /api/projects/{project_id}/plan/drafts/from-protocol`：根据研究方案生成计划草案，不替换当前项目计划。
- `POST /api/projects/{project_id}/plan/drafts/{draft_id}/apply`：应用指定计划草案，替换当前项目阶段和任务。
- `POST /api/projects/{project_id}/plan/from-protocol`：兼容旧入口，当前也只生成计划草案。
- `POST /api/chat/`：测试 Agent 对话。

在 Swagger 页面中点开接口，点击 `Try it out`，再点击 `Execute`，即可看到返回结果。

## 6. 启用真实 DeepSeek Agent 回复

当前系统默认使用 DeepSeek 作为真实 Agent 调用端。没有配置 DeepSeek API key 时，系统会自动回退到模拟回复。

在后端目录创建或编辑 `.env`：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

然后重启后端。

如果 API key 可用，聊天接口会返回真实 Agent 回复，并在响应中显示：

```json
{
  "response_source": "deepseek"
}
```

如果调用失败，系统会自动回退到模拟回复，并在响应中记录 `fallback_reason`。

## 7. 保留 OpenAI 端

OpenAI 端仍保留。如需切回 OpenAI，在 `.env` 中配置：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4o
```

然后重启后端。

## 8. 当前尚未支持

以下能力已经预留工程位置，但还没有真实接入：

- PostgreSQL 数据库。
- Redis / Celery 任务队列。
- Telegram / Email 提醒。
- DICOM / CSV 真实科研数据分析。
- PubMed / Crossref 文献检索。
- Word / PDF 论文生成。
- 登录、用户权限和医学数据脱敏。

## 9. 常见问题

### PowerShell 中文乱码

如果 PowerShell 返回的中文乱码，但浏览器页面中文正常，这是控制台编码问题，不是后端数据错误。

可以尝试：

```powershell
chcp 65001
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### `npm` 被 PowerShell 拦截

如果出现 `无法加载文件 npm.ps1`，使用：

```powershell
npm.cmd run dev
```

### 前端页面连接失败

先确认后端是否运行：

```text
http://localhost:8000/health
```

如果后端未运行，前端无法获取项目和智能体数据。

### 数据库文件在哪里

默认数据库文件位于：

```text
J:\Radiation Therapy SCI assitant\backend\sci_workshop.db
```

如需重新初始化演示数据，可以先停止后端，再删除该文件，随后重新启动后端。
