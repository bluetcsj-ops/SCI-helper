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
  - PubMed provider 增加可靠性保护：支持 `MENTOR_PUBMED_REQUEST_INTERVAL_SECONDS` 请求间隔配置，默认无 API key 时按保守间隔节流；同时补强响应结构防御、PMID 数字过滤、DOI/年份清洗、搜索链接 URL 编码和失败原因说明
  - PubMed provider 增加日期检索参数优化：模板检索式末尾的 `2019:2024` 会在请求时拆分为 ESearch `mindate` / `maxdate` / `datetype=pdat` 参数，保留原始检索式用于展示和人工复核
  - 用户本机已验证 PubMed API 可联网返回真实 PMID：宽泛检索 `radiotherapy` 返回 `['28902591', '40737738', '32671760']`
  - 用户本机已验证 `mr_linac` 主题 PubMed 完整链路：返回 `pubmed 35946325 Practical guidelines of online MR-guided adaptive radiotherapy.`；该结果仍按候选文献处理，需人工复核后才进入正式引用
  - 用户本机已验证其它 Mentor topic PubMed 首轮链路均可返回候选 PMID：`flash`→`38342233`，`ai_planning_qa`→`40563630`，`particle`→`35621386`，`radiomics`→`34663898`，`automation`→`39222848`，`sbrt`→`29033164`，`motion`→`39194360`
  - PubMed 候选排序增加 topic 关键词相关性评分：近 7 年候选仍优先，同一近期范围内按题名、期刊和文献类型中的 topic 关键词命中分排序；不联网烟测已覆盖 `ai_planning_qa` 泛题名候选被贴题候选后置
  - PubMed 候选池扩大：新增 `MENTOR_PUBMED_CANDIDATE_RETMAX`，ESearch 先抓更多候选，排序后仍只返回 `MENTOR_PUBMED_RETMAX` 条；不联网烟测已确认内部候选池扩大且最终展示条数不变
  - `ai_planning_qa` 检索式已轻量收紧，补充 `deep learning`、`quality assurance`、`patient-specific quality assurance` 和 `plan quality`，用于减少泛放疗文献优先返回
  - 用户本机已验证 `ai_planning_qa` 优化后首轮候选明显贴题：返回 PMID `38798135`、`34343412`、`31495281`，覆盖 AI 质量保证、机器/深度学习 patient-specific QA 和 AI treatment planning
  - Mentor 候选文献人工复核信息已增强：后端模型、API payload 和 SQLite 记录支持 `review_note`、`reviewer`、`full_text_checked`、`use_in_introduction`、`use_in_discussion`，旧 SQLite 表会在首次读写复核记录时自动补列
  - 前端候选证据卡新增复核备注、复核人、全文核对和 Introduction / Discussion 用途控件；研究方向建议书、候选引用清单和 Alex Writer 交接文本会同步这些复核字段
  - 前端新增候选文献复核按钮：待复核、确认可用、排除；状态可导出到 Markdown，并已持久化到项目级 SQLite 记录
  - Mentor 候选文献复核状态已新增项目级 SQLite 持久化；重新生成推荐卡后，可按 PMID / DOI / 本地证据键恢复“待复核 / 确认可用 / 排除”
  - 前端新增候选引用清单：自动汇总“确认可用”的推荐依据，展示题名、期刊、年份、PMID、DOI、来源课题和 PubMed 链接，并同步导出到 Markdown
  - 候选引用清单可交给 Alex Writer，生成 Introduction / Discussion 写作提纲、段落引用建议和仍需补充检索/阅读全文确认的项目
  - Alex Writer 新增写作工作区，基于“确认可用”的候选引用展示 Introduction / Discussion 本地提纲、候选引用和写作前检查清单
  - Alex Writer 写作工作区可导出 `alex-writer-outline.md`，包含项目研究问题、主要终点、Introduction / Discussion 提纲、候选引用和写作前检查清单
  - Alex Writer 已调整为 Introduction 聚焦模式：所有“确认可用”的候选文献默认进入 Introduction 引用池，生成背景段、研究空白段和研究目的段骨架；Discussion 暂不自动生成，等待 Dr. Data Lin 正式结果确认后再生成
  - Alex Writer Introduction 可编辑草稿已接入：项目级保存背景段、研究空白段和研究目的段，重新打开项目后恢复；只读项目禁用保存；`alex-writer-outline.md` 导出当前草稿内容，空段落回退到骨架提示
  - Introduction 引用语义插入辅助已接入：每条确认可用文献可插入到背景段、研究空白段或研究目的段；插入内容为保守语义模板句，保留 PMID/DOI/Vancouver 候选引用追溯，不自由改写、不自动保存
  - Introduction 引用使用清单已接入：前端从草稿文本解析 PMID / DOI 标记，展示引用所在段落和出现次数；重复出现只提示不阻止；有文字但无追溯标记的段落会提示人工补引用
  - Introduction 正文导出已接入：可导出 `introduction-draft.md`，内容分为正文草稿、实际使用的候选引用清单和待人工核对项目；只导出草稿中实际出现过 PMID / DOI 的引用，未使用候选引用不进入正文引用清单
  - Crossref 候选引用补充已接入：PubMed 候选文献会尝试补充 Crossref/DOI 链接、期刊元数据和候选引用草稿；Crossref 失败时不阻断 PubMed 候选证据，只在局限性中提示人工复核
  - Crossref 误匹配防护已接入：已有 DOI 时要求 Crossref DOI 精确匹配；无 DOI 时按题名规范化词命中阈值保守合并，低相似度结果不自动生成候选引用草稿
  - Crossref 单条真实联网验证通过：已知 DOI `10.1016/j.radonc.2022.07.010` 返回 `https://doi.org/10.1016/j.radonc.2022.07.010` 和候选引用草稿 `Practical guidelines of online MR-guided adaptive radiotherapy. Radiotherapy and Oncology. 2022. doi:10.1016/j.radonc.2022.07.010.`
  - Crossref 批量真实联网验证通过：`mr_linac`、`ai_planning_qa`、`sbrt`、`radiomics`、`motion` 共 15 条 PubMed 候选均成功补充 Crossref/DOI 链接和候选引用草稿，未出现 API 失败或阈值误拦截；默认题名阈值 `MENTOR_CROSSREF_TITLE_MATCH_MIN_SCORE=4` 暂不调整
  - Vancouver 风格候选引用导出已接入：基于题名、期刊、年份和 DOI 生成不含作者/卷期/页码的保守候选格式，并同步到推荐依据、候选引用清单、Alex Writer 交接文本、《研究方向建议书》和 `alex-writer-outline.md`
  - Vancouver 候选引用元数据增强已接入：从 Crossref 解析作者、卷、期、页码或 article number；作者超过 6 个时输出前 6 个加 `et al`，缺失字段会跳过而不是编造
  - 前端推荐依据、候选引用清单、Alex Writer 交接文本、《研究方向建议书》和 `alex-writer-outline.md` 已同步导出 Crossref/DOI 链接与候选引用草稿
  - 当前仍未完成 NCBI 实际限速行为验证、正式引用格式导出、字段级引用管理和 Crossref 真实联网批量验证；当前相关性排序、Crossref 候选元数据和人工复核字段仍不等于系统综述或正式引用质量评价
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

Mentor evidence：

```text
MENTOR_EVIDENCE_PROVIDER=local 或 pubmed 或 crossref
PUBMED_BASE_URL=https://eutils.ncbi.nlm.nih.gov/entrez/eutils
PUBMED_API_KEY=
PUBMED_EMAIL=
CROSSREF_BASE_URL=https://api.crossref.org
CROSSREF_MAILTO=你的邮箱，可选但建议填写
MENTOR_PUBMED_RETMAX=3
MENTOR_PUBMED_CANDIDATE_RETMAX=12
MENTOR_CROSSREF_RETMAX=1
MENTOR_CROSSREF_TITLE_MATCH_MIN_SCORE=4
MENTOR_EVIDENCE_TIMEOUT_SECONDS=6
MENTOR_PUBMED_REQUEST_INTERVAL_SECONDS=-1
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

Crossref 候选引用补充验证：

- 后端：`python -B -c "import app.agents.mentor_models; import app.agents.mentor_evidence_service; import app.core.config"`
- 前端：`.\node_modules\.bin\tsc.cmd --noEmit`
- 服务层不联网烟测：伪造 Crossref work 后，`CrossrefEvidenceProvider.enrich_evidence` 可生成 `pubmed_crossref` 状态、Crossref/DOI 链接和候选引用草稿
- 误匹配防护不联网烟测：高相似题名可合并；低相似题名会保留 PubMed 候选、不生成候选引用草稿，并在局限性中提示相似度不足
- 真实联网单条验证：`10.1016/j.radonc.2022.07.010` 可返回 DOI 链接和候选引用草稿
- 真实联网批量验证：`mr_linac`、`ai_planning_qa`、`sbrt`、`radiomics`、`motion` 共 15 条 PubMed 候选均成功补充 Crossref/DOI 链接和候选引用草稿，未调整默认题名阈值
- 正式引用仍需人工核对全文、DOI 页面和目标期刊格式

Vancouver 候选引用验证：

- 后端：`python -B -c "import app.agents.mentor_models; import app.agents.mentor_evidence_service; import app.core.config"`
- 前端：`.\node_modules\.bin\tsc.cmd --noEmit`
- 服务层不联网烟测：伪造 Crossref work 后，`CrossrefEvidenceProvider.enrich_evidence` 可生成 `vancouver_citation`
- 服务层不联网烟测已覆盖：1-3 个作者、超过 6 个作者触发 `et al`、缺卷期页码时不产生异常标点
- 当前 Vancouver 字段属于候选写作辅助格式，不是最终投稿格式；期刊缩写和目标期刊格式仍需人工核对

Alex Writer Introduction 草稿验证：

- 后端：`.\.venv\Scripts\python.exe -B -c "import app.db.models; import app.projects.models; import app.projects.writer_drafts; import app.api.routes.projects"`
- 前端：`.\node_modules\.bin\tsc.cmd --noEmit`
- Repository 烟测：使用内存 SQLite 保存并读取背景段、研究空白段和研究目的段
- 权限边界：API 路由按项目权限读取；保存需要 `editor` 权限，前端只读项目禁用保存按钮
- 前端类型检查覆盖引用语义插入逻辑；插入按钮仅更新本地草稿，仍需手动保存
- 前端类型检查覆盖引用使用清单逻辑；重复引用和无追溯段落为提示性质，不自动修改草稿
- 前端类型检查覆盖 `introduction-draft.md` 导出逻辑；导出引用清单只包含正文草稿中实际出现的 PMID / DOI 标记

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
