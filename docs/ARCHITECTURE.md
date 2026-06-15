# 架构设计草案

## 总体结构

平台采用前后端分离架构：

- 前端：React + Vite + CSS。
- 后端：FastAPI。
- 数据库：原型阶段使用 SQLite，后续可迁移到 PostgreSQL。
- AI 引擎：默认 DeepSeek API，OpenAI API 保留为可选切换。
- 任务队列：后续接入 Celery + Redis。
- 文件存储：后续接入 MinIO / S3。
- 通知：后续接入 Telegram Bot API + SMTP。

## 后端模块

- `app/api/`：HTTP API 路由。
- `app/core/`：配置和应用初始化。
- `app/agents/`：Agent prompt、角色元数据和调用入口。
- `app/orchestrator/`：中央协调器，负责对话上下文组装和 Agent 分发。
- `app/llm/`：DeepSeek / OpenAI 统一调用层，失败时回退模拟回复。
- `app/projects/`：项目、阶段、任务、计划草案、里程碑和仪表盘状态。
- `app/reminders/`：Rhea 本地监控提醒，基于任务截止日期和状态生成 48 小时、24 小时、逾期和受阻提醒。
- `app/protocols/`：Project Protocol 研究方案的读取、草案生成、长文本抽取和保存。
- `app/chat/`：聊天记录持久化。
- `app/db/`：SQLAlchemy 模型、会话和种子数据。

## 前端模块

当前原型先保持轻量结构：

- `src/App.tsx`：主控台、项目卡、任务状态、研究方案表单和聊天界面。
- `src/api.ts`：后端 API 客户端。
- `src/types.ts`：前端类型定义。
- `src/styles.css`：页面布局和主题样式。

后续页面复杂后，可再拆分到 `pages/`、`components/`、`api/` 和 `styles/`。

## 核心数据流

1. 用户进入“我的研究书房”。
2. 前端读取 `/api/dashboard/`、`/api/projects/` 和 `/api/agents/`。
3. 用户切换项目时，前端读取 `/api/projects/{project_id}/protocol`。
4. 用户点击“草案”时，后端为当前项目生成结构化研究方案草案。
5. 用户点击 Dr. Vera 回复下的“写入研究方案”时，后端抽取长文本字段并写入 `project_protocols` 表。
6. 用户编辑后点击“保存”，后端写入 `project_protocols` 表。
7. 用户点击“草案”时，后端根据 Project Protocol 生成计划草案并写入 `project_plan_drafts` 表，不修改当前项目。
8. 用户预览后点击“应用该草案”时，后端才替换当前项目的阶段、任务、截止日期和交付物。
9. 用户发送聊天消息时，后端通过 Orchestrator 组装项目上下文并调用当前 Agent。
10. DeepSeek 或 OpenAI 调用失败时，后端自动回退模拟回复，并记录失败原因。
11. 聊天双方消息写入 `chat_messages` 表。
12. 用户更新任务状态时，后端刷新项目进度和风险，再返回最新项目状态。
13. 前端读取 `/api/projects/{project_id}/reminders` 时，后端按当前任务状态生成或更新本地提醒记录。

## API 分组

- `GET /health`：健康检查。
- `GET /api/dashboard/`：仪表盘摘要与 Rhea 监控信息。
- `GET /api/agents/`：可咨询 Agent 列表。
- `GET /api/projects/`：项目列表。
- `GET /api/projects/{project_id}`：项目详情。
- `PATCH /api/projects/{project_id}/tasks/{task_id}`：更新任务状态。
- `GET /api/projects/{project_id}/reminders`：读取 Rhea 本地监控提醒。
- `POST /api/projects/{project_id}/reminders/refresh`：重新生成 Rhea 本地监控提醒。
- `PATCH /api/projects/{project_id}/reminders/{reminder_id}/dismiss`：归档指定提醒。
- `GET /api/projects/{project_id}/protocol`：读取研究方案。
- `POST /api/projects/{project_id}/protocol/draft`：生成研究方案草案。
- `POST /api/projects/{project_id}/protocol/extract`：从 Dr. Vera 回复中抽取并保存研究方案。
- `PUT /api/projects/{project_id}/protocol`：保存研究方案。
- `GET /api/projects/{project_id}/plan/drafts`：查看计划草案列表。
- `POST /api/projects/{project_id}/plan/drafts/from-protocol`：根据研究方案生成计划草案。
- `POST /api/projects/{project_id}/plan/drafts/{draft_id}/apply`：应用计划草案并替换当前项目阶段和任务。
- `POST /api/projects/{project_id}/plan/from-protocol`：兼容旧入口，当前同样只生成计划草案。
- `POST /api/chat/`：Agent 对话。

## Rhea 的位置

Rhea Chen 是页面级全流程实施监控员，不再作为普通咨询 Agent 出现在角色列表中。她的职责是监控项目执行、延误风险、受阻任务和下一里程碑。前端通过 Dashboard 数据展示 Rhea 的管理状态。

当前原型的 Rhea 提醒是本地模拟提醒：接口调用时根据任务截止日期和状态生成提醒，并写入 SQLite。后续接入 Celery / Redis 后，可把同一套提醒记录交给 Telegram / Email 发送任务处理。

## Project Protocol 的位置

Project Protocol 是每个论文项目的结构化方案资产。它承接 Dr. Vera Protocol 的方案输出，并为后续数据分析、写作、审查和 Rhea 进度管理提供稳定上下文。

当前原型先保存文本字段。后续可以继续扩展为：

- 与 Dr. Data Lin 联动，生成数据需求规格说明书。
- 与 Alex Writer 联动，生成论文方法部分。

## 隐私与安全原则

- 用户上传数据默认仅用于当前项目。
- 医学数据处理模块必须保留审计日志。
- 真实 DICOM 与临床数据接入前，需要增加脱敏、权限控制和存储加密。
- 统计与代码执行必须放入隔离沙箱，不允许默认访问外网。
