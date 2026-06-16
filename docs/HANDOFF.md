# 项目交接记录

更新时间：2026-06-17

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的原型工程。当前目标是先建立一个可运行、可扩展的多智能体平台骨架，再逐步接入真实科研数据分析、文献检索、论文生成、审稿和提醒服务。

## 当前完成进度

### 2026-06-16 补充更新

- 新增独立进度总表：`docs/PROGRESS_STATUS.md`
  - 汇总 Prof. RadOnc Mentor、Rhea、Dr. Data Lin、Alex Writer、审稿官和平台基础设施的已完成/未完成状态
  - 明确说明 Dr. Data Lin 仍有高阶统计缺口，但不构成当前全局主阻塞
- Prof. RadOnc Mentor 继续增强为本地可用闭环：
  - 推荐响应新增资源诊断
  - 课题推荐卡新增研究问题、数据路径、方法路线、统计建议、风险提示和首轮里程碑
  - 前端虚拟导师工作区展示完整推荐卡
  - Markdown《研究方向建议书》同步导出完整路线
  - 推荐卡新增“写入研究方案”按钮，可将选题路线保存为当前项目的 Project Protocol，并刷新 Dr. Data Lin 数据需求
  - 写入前新增关键字段预览和覆盖确认，避免误覆盖已有 Project Protocol
  - 新增本地文献证据模板：推荐卡展示检索式、证据摘要、推荐信号和局限性，并同步导出到 Markdown 建议书
  - 新增独立 `mentor_evidence_service.py`，证据项已标注 `local_template` 状态、检索时间和外部链接预留字段，后续可替换为 PubMed / Crossref 实现
  - 新增 PubMed provider 和环境开关 `MENTOR_EVIDENCE_PROVIDER`；`pubmed` 模式会调用 NCBI ESearch / ESummary 解析 PMID、题名、期刊、年份和 DOI，失败时返回 `external_pending` 与 PubMed 搜索链接
  - PubMed provider 增加质量保护：过滤无 PMID/无题名结果，优先近 7 年候选文献，保留文献类型和 `unreviewed` 人工复核状态
  - 前端新增候选文献复核按钮：待复核、确认可用、排除；状态可导出到 Markdown，并已持久化到项目级 SQLite 记录
  - Mentor 候选文献复核状态已新增项目级 SQLite 持久化；重新生成推荐卡后，可按 PMID / DOI / 本地证据键恢复“待复核 / 确认可用 / 排除”
  - 前端新增候选引用清单：自动汇总“确认可用”的推荐依据，展示题名、期刊、年份、PMID、DOI、来源课题和 PubMed 链接，并同步导出到 Markdown
  - 候选引用清单可交给 Alex Writer，生成 Introduction / Discussion 写作提纲、段落引用建议和仍需补充检索/阅读全文确认的项目
  - Alex Writer 新增写作工作区，基于“确认可用”的候选引用展示 Introduction / Discussion 本地提纲、候选引用和写作前检查清单
  - Alex Writer 写作工作区可导出 `alex-writer-outline.md`，包含项目研究问题、主要终点、Introduction / Discussion 提纲、候选引用和写作前检查清单
  - 当前仍未完成联网环境下的真实 PubMed 实测、速率限制策略、人工质量复核流程和 Crossref 自动证据检索；工具沙箱内真实请求会触发 WinError 10013，联网审批未返回
- Prof. RadOnc Mentor 已补齐最小可用版本（MVP）：
  - 后端新增 `GET /api/mentor/trends`
  - 后端新增 `POST /api/mentor/recommendations`
  - 前端新增虚拟导师工作区：趋势快照、能力问卷、兴趣方向勾选、课题推荐卡
  - 支持导出本地 Markdown《研究方向建议书》
  - 当前趋势数据仍为本地静态快照，不是联网真实趋势数据库
- Dr. Data Lin 新增：
  - 长表 `rm_anova` 重复测量 ANOVA 设计识别与边界判断
  - 平衡重复测量设计返回 `needs_external_review`
  - 不完整重复测量设计返回阻断或明确警告，提示 mixed-effects model 更合适

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
  - 正式检验结果审计：确认项缺失、隐私风险或复杂设计会阻止执行并写日志；两组独立样本数值结局可执行 Welch t 检验，宽表两列配对测量和长表 `subject_id + condition + outcome` 两条件配对测量可执行配对 t 检验，长表三条件及以上重复测量可执行 Friedman 检验，多组独立样本数值结局可根据样本量、偏态信号、方差差异和样本量不均衡执行单因素 ANOVA、Welch ANOVA 或 Kruskal-Wallis 检验，并附带 Tukey HSD、Games-Howell、Dunn 或配对秩和风格事后比较，支持 Holm-Bonferroni 或 Benjamini-Hochberg FDR 校正；安装 SciPy 后会优先使用 SciPy 的分布与秩检验路径，未安装时保留原型近似兜底
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

本次新增的 Dr. Data Lin 数据工作区已通过不落盘语法检查和前端 TypeScript `--noEmit` 检查。正式检验接口既有临时 SQLite 验证覆盖人工确认与 Welch t 检验；新增的宽表两列配对 t 检验、长表对象 ID + 条件列两条件配对 t 检验、长表三条件及以上 Friedman 检验、单因素 ANOVA、Welch ANOVA、Kruskal-Wallis 检验，以及 Tukey HSD、Games-Howell、Dunn、配对秩和风格事后比较，已通过服务层临时 CSV 验证；事后比较支持 Holm-Bonferroni 和 Benjamini-Hochberg FDR 两种校正。`backend/requirements.txt` 已新增 `scipy>=1.13.0`；安装 SciPy 后，P 值会优先使用 SciPy 的 t/F/卡方/正态分布、studentized range、Friedman 和 Wilcoxon 计算路径，当前沙箱网络未放行安装，因此本轮本地烟测覆盖的是无 SciPy 兜底路径。正式检验会写入 `formal_test_blocked` 与 `formal_test_executed` 审计日志。配对检验当前覆盖同一行两列数值测量，以及长表中一个对象 ID、一个条件列和一个数值结局列的两条件或三条件及以上重复测量；多组检验当前只覆盖独立样本数值结局。当前按单用户本地工具使用，不启用登录、SSO 和成员管理；`/api/users/me` 默认返回 `user-primary`。用户本机已验证前端 `npm.cmd run build` 可通过；工具沙箱内完整 Vite build 会因临时文件写入权限报 `EPERM`。

虚拟导师本轮新增验证：

- 后端：`python -m py_compile app/agents/mentor_models.py app/agents/mentor_service.py app/api/routes/mentor.py`
- 前端：`.\node_modules\.bin\tsc.cmd --noEmit`
- 服务层烟测：
  - 趋势快照可返回至少 6 个方向
  - 问卷提交后可返回 2-3 个推荐卡
  - 可导出本地 Markdown 建议书

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

1. 继续增强正式统计可信度，例如重复测量 ANOVA、混合效应模型，以及 Dunn 检验的专用库复核。
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
