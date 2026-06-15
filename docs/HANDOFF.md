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
- Dr. Data Lin 数据工作区：
  - 基于 Project Protocol 生成数据需求清单
  - CSV 上传原型
  - 字段覆盖检查
  - 缺失率、唯一值和数值列范围质控
  - 生成可交给 Alex Writer 的结果摘要
  - 描述性统计和分组比较草案
  - 基础图表预览：数值分布、分类构成和分组均值
  - 一键交给 Alex Writer 生成 Results 段落草稿
  - 保存和恢复分析记录；只保存报告 JSON，不保存原始 CSV
  - 图表预览可导出为 SVG 矢量文件
  - 可复现参数快照：文件名、分组列、结局列、规则版本、图表 ID，可导出 JSON
  - 图表样式模板：期刊蓝、单色、高对比；支持 SVG、PNG 和打印另存 PDF
  - 变量分布检查、候选检验建议和 P 值计算边界提示；统计草案阶段不自动计算 P 值
  - 正式假设检验人工确认：确认人、研究设计、终点、脱敏、缺失值、统计假设和多重比较
  - 正式检验结果审计：确认项缺失、隐私风险或复杂设计会阻止执行并写日志；两组数值结局当前可执行 Welch t 检验
  - 脱敏与隐私检查：识别直接身份标识、编码标识符、日期标识符和高唯一文本列
  - 数据操作审计日志：记录质控、统计、隐私阻止和保存分析记录事件；不保存原始 CSV
  - 红色隐私风险会阻止统计草案生成
  - 可复现实验脚本导出：标准库 Python 脚本，本地读取脱敏 CSV，复现描述性统计、分组摘要和基础图表数据；不自动计算 P 值
- 用户与项目权限边界：
  - `users`、`project_access` 表
  - 默认演示用户 `user-primary`
  - 当前按单用户本地工具使用，不启用登录、SSO 和成员管理
  - `X-SCI-User-Id` 请求头仅保留给 Swagger 调试
  - `viewer/editor/owner` 三档项目权限
  - 项目列表、仪表盘、聊天上下文、研究方案、提醒和数据工作区均检查项目授权
  - 前端显示当前用户和项目权限；只读项目禁用写操作

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

本次新增的 Dr. Data Lin 数据工作区已通过不落盘语法检查和前端 TypeScript `--noEmit` 检查。正式检验接口已用临时 SQLite 验证：未完成人工确认时返回 400，全部确认后返回 Welch t 检验结果，并写入 `formal_test_blocked` 与 `formal_test_executed` 审计日志。当前按单用户本地工具使用，不启用登录、SSO 和成员管理；`/api/users/me` 默认返回 `user-primary`。用户本机已验证前端 `npm.cmd run build` 可通过；工具沙箱内完整 Vite build 会因临时文件写入权限报 `EPERM`。

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

建议下一阶段继续深化科研功能薄切片：

1. 扩展更多正式检验类型，例如多组 ANOVA、非参数检验、配对设计和多重比较校正。
2. 优化单用户体验：本地配置、项目归档、数据导入模板和一键导出。

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
