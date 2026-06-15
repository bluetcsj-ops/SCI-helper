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
- 在“Dr. Data Lin 数据工作区”查看数据需求清单，并上传脱敏 CSV 生成字段覆盖和数据质量检查报告。
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

## 5. 使用数据工作区

数据工作区对应 Dr. Data Lin 的第一阶段能力。

推荐流程：

1. 先在“研究方案”面板填写或生成数据需求、主要终点和次要终点。
2. 查看“Dr. Data Lin 数据工作区”的字段需求清单。
3. 上传一份脱敏 CSV。
4. 查看行数、列数、关键字段覆盖、缺失率、唯一值、数值列范围和“脱敏与隐私检查”。
5. 如果出现红色隐私风险，先移除姓名、电话、邮箱、证件号等直接身份标识；红色风险会阻止统计草案生成。
6. 选择分组列和结局列，生成描述性统计、分组比较草案、变量分布检查和基础图表预览。
7. 查看“正式统计边界”，确认候选检验、P 值使用前提和需要补充说明的统计限制。
8. 选择“期刊蓝 / 单色 / 高对比”图表样式，并在图表卡片中导出 SVG、PNG，或打开打印视图另存 PDF。
9. 在“可复现参数”中查看分组列、结局列、规则版本和原始 CSV 保存状态，并可导出 JSON。
10. 在“可复现实验脚本”中下载 Python 脚本，用本地脱敏 CSV 复现描述性统计和基础图表数据。
11. 在“正式假设检验”中填写确认人，逐项确认研究设计、终点、脱敏、缺失值、统计假设和多重比较后，点击“确认并执行正式检验”。
12. 点击“交给 Alex Writer”，让写作智能体基于质控、统计、图表摘要和已确认的正式检验结果生成 Results 段落草稿。
13. 点击“保存分析记录”，将当前质控报告、统计草案、正式检验结果和图表规格保存到 SQLite。
14. 在“已保存报告”中恢复历史分析记录，并在“数据操作日志”中查看上传、统计、正式检验和保存事件。
15. 根据缺少字段、高缺失率、脱敏风险和统计草案提示，回到数据导出流程补齐字段或重新脱敏。

当前 CSV 原型只做结构化质控，不会保存原始数据文件。
保存分析记录时只保存报告 JSON 和摘要，不保存原始 CSV。
当前隐私检查会基于列名和前 50 行样本值识别常见直接身份标识、编码标识符、日期标识符和高唯一文本列；它不能替代医院正式脱敏流程。
当前统计草案会给出描述性统计、变量分布信号和候选检验建议。正式检验入口要求完成六项人工确认后才会计算 P 值；当前原型支持两组数值结局的 Welch t 检验，多组或复杂设计会标记为需要外部统计环境复核。
当前图表可导出为 SVG 矢量文件、PNG 图片，或通过打印视图另存为 PDF。
参数 JSON 可用于复核当次分析使用的文件名、结局列、分组列、规则版本和图表 ID。
Python 脚本只依赖标准库，读取本地脱敏 CSV 后生成 `.analysis-summary.json`；脚本不会联网，也不会自动计算 P 值。

当前原型按单用户本地工具设计：打开前端后默认使用 `user-primary` 演示用户，不需要登录。后端仍保留项目级权限边界，项目列表、仪表盘、聊天上下文、研究方案、提醒和数据工作区都会检查项目授权；默认用户拥有示例项目的负责人权限。

## 6. 使用 Swagger 测试 API

Swagger 是 FastAPI 自动生成的接口测试网页：

```text
http://localhost:8000/docs
```

常用接口：

- `GET /health`：检查后端是否运行。
- `GET /api/users/me`：读取当前默认用户；Swagger 中也可通过请求头 `X-SCI-User-Id` 调试切换用户。
- `GET /api/agents/`：查看五个可咨询智能体配置。
- `GET /api/projects/`：查看当前用户有权访问的项目。
- `GET /api/projects/{project_id}/access`：查看当前用户在该项目中的权限。
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
- `GET /api/projects/{project_id}/data/requirements`：读取数据需求清单。
- `GET /api/projects/{project_id}/data/analysis-records`：读取已保存分析记录。
- `GET /api/projects/{project_id}/data/audit-logs`：读取当前项目的数据操作审计日志。
- `POST /api/projects/{project_id}/data/analysis-records`：保存当前质控和统计报告。
- `POST /api/projects/{project_id}/data/quality-report`：上传脱敏 CSV 并生成数据质量报告和隐私检查报告。
- `POST /api/projects/{project_id}/data/statistics-report`：上传脱敏 CSV 并生成描述性统计草案、变量分布检查、检验建议、基础图表预览和可复现实验脚本。
- `POST /api/projects/{project_id}/data/formal-test-report`：上传同一份脱敏 CSV，在人工确认后执行正式检验并写入审计日志。
- `POST /api/chat/`：测试 Agent 对话。

在 Swagger 页面中点开接口，点击 `Try it out`，再点击 `Execute`，即可看到返回结果。

## 7. 启用真实 DeepSeek Agent 回复

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

## 8. 保留 OpenAI 端

OpenAI 端仍保留。如需切回 OpenAI，在 `.env` 中配置：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4o
```

然后重启后端。

## 9. 当前尚未支持

以下能力已经预留工程位置，但还没有真实接入：

- PostgreSQL 数据库。
- Redis / Celery 任务队列。
- Telegram / Email 提醒。
- DICOM 真实科研数据分析。
- 更多正式检验类型和出版级图表导出增强。
- PubMed / Crossref 文献检索。
- Word / PDF 论文生成。
- 真实医院 SSO、密码重置邮件和正式医学数据脱敏流程。

## 10. 常见问题

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
