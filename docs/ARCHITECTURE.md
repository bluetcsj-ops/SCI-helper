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
- `app/data/`：Dr. Data Lin 数据工作区，基于研究方案生成数据需求清单，并对上传 CSV 做字段覆盖、缺失率和数值列范围检查。
- `app/users/`：默认本地用户、用户资料和项目授权。
- `app/chat/`：聊天记录持久化。
- `app/db/`：SQLAlchemy 模型、会话和种子数据。

## 前端模块

当前原型先保持轻量结构：

- `src/App.tsx`：主控台、项目卡、任务状态、研究方案表单、数据工作区和聊天界面。
- `src/api.ts`：后端 API 客户端。
- `src/types.ts`：前端类型定义。
- `src/styles.css`：页面布局和主题样式。

后续页面复杂后，可再拆分到 `pages/`、`components/`、`api/` 和 `styles/`。

## 核心数据流

1. 用户进入“我的研究书房”后直接进入工作台。
2. 前端读取 `/api/users/me`、`/api/dashboard/`、`/api/projects/` 和 `/api/agents/`；后端默认使用 `user-primary`。
3. 用户切换项目时，前端读取 `/api/projects/{project_id}/access` 和 `/api/projects/{project_id}/protocol`。
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
14. 前端读取 `/api/projects/{project_id}/data/requirements` 时，后端根据 Project Protocol 的数据需求、主要终点和次要终点生成数据字段清单。
15. 用户上传脱敏 CSV 时，前端将文件内容发送到 `/api/projects/{project_id}/data/quality-report`，后端返回字段匹配、缺失率、数值列摘要、隐私检查报告和给 Alex Writer 的结果摘要。
16. 质量报告生成、统计草案生成、正式检验执行、正式检验阻止、隐私风险阻止和分析记录保存都会写入 `data_audit_logs` 表；审计日志只存摘要、风险等级和是否保存原始数据，不存 CSV 内容。
17. 用户确认分组列和结局列后，前端将同一份 CSV 发送到 `/api/projects/{project_id}/data/statistics-report`，后端会先做隐私检查；如存在红色直接身份标识风险，则阻止统计草案生成。
18. 通过隐私检查后，后端返回描述性统计、分类变量频数、分组比较草案、变量分布检查、候选检验建议、基础图表规格和可复现实验脚本。
19. 统计报告包含 P 值计算边界提示：当前系统先提示何时可以考虑正式检验，不在草案阶段计算或报告 P 值。
20. 用户完成确认人、研究设计、终点、脱敏、缺失值、统计假设和多重比较确认后，前端将同一份 CSV 发送到 `/api/projects/{project_id}/data/formal-test-report`。
21. 正式检验接口会再次做隐私检查；确认项缺失或红色隐私风险会阻止执行并写审计日志。当前原型支持两组数值结局的 Welch t 检验，多组或复杂设计返回需外部统计环境复核的结果状态。
22. 统计报告包含可复现参数快照，记录文件名、结局列、分组列、规则版本、图表 ID 和原始 CSV 保存状态。
23. 可复现实验脚本是标准库 Python 脚本，读取用户本地脱敏 CSV 并生成 `.analysis-summary.json`；脚本不联网、不自动计算 P 值。
24. 用户选择图表样式模板后，前端基于 chart spec 生成 SVG、PNG，或打开打印视图另存 PDF。
25. 用户点击“保存分析记录”时，前端将质控报告、统计报告和正式检验结果 JSON 写入 `data_analysis_records` 表，不保存原始 CSV 文件。

## API 分组

- `GET /health`：健康检查。
- `GET /api/users/me`：当前用户。
- `GET /api/dashboard/`：仪表盘摘要与 Rhea 监控信息。
- `GET /api/agents/`：可咨询 Agent 列表。
- `GET /api/projects/`：当前用户有权访问的项目列表。
- `GET /api/projects/{project_id}`：项目详情。
- `GET /api/projects/{project_id}/access`：当前用户在该项目的访问级别与操作能力。
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
- `GET /api/projects/{project_id}/data/requirements`：读取 Dr. Data Lin 数据需求清单。
- `GET /api/projects/{project_id}/data/analysis-records`：读取当前项目已保存的数据分析记录。
- `GET /api/projects/{project_id}/data/audit-logs`：读取当前项目的数据操作审计日志。
- `POST /api/projects/{project_id}/data/analysis-records`：保存当前质控报告和统计报告。
- `POST /api/projects/{project_id}/data/quality-report`：上传脱敏 CSV 并生成数据质量检查报告和隐私检查报告。
- `POST /api/projects/{project_id}/data/statistics-report`：上传脱敏 CSV，经隐私检查后生成描述性统计、变量分布检查、候选检验建议、分组比较草案、基础图表预览规格和可复现实验脚本。
- `POST /api/projects/{project_id}/data/formal-test-report`：上传同一份脱敏 CSV，经人工确认和隐私复查后执行正式检验并写入审计日志。
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
- 当前原型按单用户本地工具使用，默认用户为 `user-primary`；`X-SCI-User-Id` 只作为 Swagger 调试兼容入口保留。
- 所有带 `project_id` 的项目上下文接口都需要项目授权。
- `viewer` 可以读取项目、方案、提醒和数据报告；`editor`/`owner` 可以修改方案、任务、计划和数据工作区。
- 医学数据处理模块必须保留审计日志；当前原型记录操作摘要，不保存原始 CSV。
- 统计分析前必须先通过隐私检查；疑似直接身份标识会阻止统计草案生成。
- 真实 DICOM 与临床数据接入前，需要增加脱敏、权限控制和存储加密。
- 统计与代码执行必须放入隔离沙箱，不允许默认访问外网。
