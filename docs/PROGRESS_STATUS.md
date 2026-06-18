# 当前模块进度表

更新日期：2026-06-18

## 总体判断

当前项目已经形成“单用户本地科研助手原型”，其中 Dr. Data Lin 数据分析工作区完成度最高；Prof. RadOnc Mentor、Alex Writer、Rev. Dr. Helena Skov 仍以角色定义和局部原型为主，离完整路线目标还有明显差距。

## 分模块进度

### 1. Prof. RadOnc Mentor（虚拟导师）

- 已完成：
  - 角色定义
  - Agent 注册与基础对话入口
  - 本地静态趋势库
  - 2019-2024 趋势快照展示
  - 2025-2030 机会判断与方向提示
  - 能力问卷
  - 设备、数据、时间投入和发文经验画像分析
  - 2-3 个课题推荐卡
  - 每张推荐卡包含研究问题、数据路径、方法路线、统计建议、风险提示、首轮里程碑和建议期刊
  - 《研究方向建议书》Markdown 导出
  - 课题推荐卡可一键写入 Project Protocol，自动生成研究问题、研究假设、终点、数据需求、实验流程、统计路线、目标期刊和 Rhea 里程碑
  - 写入 Project Protocol 前提供关键字段预览和覆盖确认，避免误覆盖当前研究方案
  - 本地文献证据模板：每张推荐卡包含检索式、证据摘要、推荐信号和局限性，可导出到《研究方向建议书》
  - Mentor Evidence Service 已独立抽象，证据项包含来源状态、检索时间和外部链接预留字段
  - PubMed Evidence Provider：`MENTOR_EVIDENCE_PROVIDER=pubmed` 时通过 NCBI ESearch / ESummary 获取 PMID、题名、期刊、年份和 DOI；失败时返回 `external_pending` 证据和 PubMed 搜索链接
  - PubMed 结果质量保护：过滤无 PMID/无题名结果，优先近 7 年候选文献，保留文献类型和 `unreviewed` 人工复核状态
  - PubMed 请求可靠性补强：新增保守请求间隔配置、响应结构防御、PMID 数字过滤、DOI/年份清洗、搜索链接 URL 编码和更明确的失败原因说明
  - PubMed 日期检索参数优化：将模板检索式末尾的 `2019:2024` 拆分为 ESearch `mindate` / `maxdate` / `datetype=pdat` 参数，避免裸年份范围导致无 PMID
  - PubMed 网络连通性已由用户本机验证：宽泛检索 `radiotherapy` 可返回真实 PMID 列表
  - `mr_linac` 主题 PubMed 真实链路已由用户本机验证通过：返回 PMID `35946325`，题名为 `Practical guidelines of online MR-guided adaptive radiotherapy.`
  - 其它 Mentor topic PubMed 首轮真实链路均已由用户本机验证可返回候选 PMID：`flash`→`38342233`，`ai_planning_qa`→`40563630`，`particle`→`35621386`，`radiomics`→`34663898`，`automation`→`39222848`，`sbrt`→`29033164`，`motion`→`39194360`
  - PubMed 候选排序相关性增强：为各 Mentor topic 增加轻量关键词画像，在近 7 年优先的基础上按题名、期刊和文献类型关键词命中分排序，使泛题名候选不再优先于贴题候选
  - PubMed 候选池扩大：新增 `MENTOR_PUBMED_CANDIDATE_RETMAX`，先抓取更多候选后再按 topic 相关性排序，最终仍按 `MENTOR_PUBMED_RETMAX` 返回展示条数
  - `ai_planning_qa` PubMed 检索式轻量收紧：补充 `deep learning`、`quality assurance`、`patient-specific quality assurance` 和 `plan quality`，减少泛放疗文献优先返回
  - `ai_planning_qa` 优化后已由用户本机复测通过：首轮候选变为 PMID `38798135`、`34343412`、`31495281`，题名分别聚焦 AI 质量保证、机器/深度学习 patient-specific QA 和 AI treatment planning
  - 候选文献人工复核信息增强：项目级保存复核备注、复核人、是否已核对全文、是否用于 Introduction、是否用于 Discussion，并兼容旧 SQLite 表自动补列
  - 前端复核控件增强：每条候选证据可填写复核备注、复核人、全文核对和 Introduction / Discussion 用途，Markdown 建议书、候选引用清单和 Alex Writer 交接文本同步导出这些字段
  - 前端候选文献人工复核：可将推荐依据标记为“待复核 / 确认可用 / 排除”，并同步到 Markdown 建议书导出
  - 候选文献复核状态持久化：项目级保存 Mentor 推荐依据的复核状态，重新生成推荐卡后可按 PMID / DOI / 本地证据键恢复
  - 候选引用清单：自动汇总“确认可用”的推荐依据，展示题名、期刊、年份、PMID、DOI 和来源课题，并同步导出到 Markdown
  - Alex Writer 联动：可将候选引用清单交给 Alex Writer，生成 Introduction / Discussion 写作提纲和仍需补充检索的项目清单
  - Alex Writer 写作工作区：展示基于候选引用的 Introduction / Discussion 本地提纲、候选引用列表和写作前检查清单
  - Alex Writer 写作提纲 Markdown 导出：可将本地提纲、项目研究问题、主要终点、候选引用和写作前检查清单导出为 `alex-writer-outline.md`
  - Alex Writer Introduction 聚焦模式：所有“确认可用”的候选文献默认进入 Introduction 引用池，生成背景段、研究空白段和研究目的段骨架；Discussion 暂不自动生成，等待 Dr. Data Lin 正式结果确认后再生成
  - Alex Writer Introduction 可编辑草稿：项目级保存背景段、研究空白段和研究目的段，重新打开项目后可恢复；`alex-writer-outline.md` 导出会包含当前草稿内容，空段落则回退到骨架提示
  - Introduction 引用语义插入辅助：确认可用文献可一键以保守语义句插入背景段、研究空白段或研究目的段，并保留 PMID/DOI/Vancouver 候选引用追溯；插入只更新本地草稿，需手动保存
  - Introduction 引用使用清单：从草稿中解析 PMID / DOI 追溯标记，显示引用出现段落、出现次数、重复使用提示，以及有文字但缺少追溯标记的段落
  - Introduction 正文导出：可导出 `introduction-draft.md`，分离正文草稿、实际使用的候选引用清单和待人工核对项目；未在草稿中出现的候选引用不会进入正文引用清单
  - 字段级引用映射 MVP：Alex Writer 可按背景段、研究空白段和研究目的段分别解析 PMID / DOI 追溯标记，匹配当前确认可用候选文献，显示全文核对状态、Introduction 用途状态、未匹配标记和缺少追溯标记提示，并同步导出到 `introduction-draft.md`
  - 可编辑引用绑定 MVP：候选引用可手动绑定到背景段、研究空白段或研究目的段，绑定结果随 Introduction 草稿保存；字段级引用映射和 `introduction-draft.md` 同时展示自动解析与手动绑定
  - Crossref 候选引用补充：PubMed 候选文献可尝试通过 Crossref 补充 DOI 链接、期刊元数据和候选引用草稿；失败时保留原 PubMed 候选并提示人工复核
  - Crossref 误匹配防护：已有 DOI 时要求 Crossref DOI 精确匹配；无 DOI 时按题名规范化词命中阈值保守合并，低相似度结果不自动生成候选引用草稿
  - Crossref 单条真实联网验证通过：已知 DOI `10.1016/j.radonc.2022.07.010` 可返回 DOI 链接和候选引用草稿
  - Crossref 批量真实联网验证通过：`mr_linac`、`ai_planning_qa`、`sbrt`、`radiomics`、`motion` 共 15 条 PubMed 候选均成功补充 Crossref/DOI 链接和候选引用草稿；默认题名阈值 `MENTOR_CROSSREF_TITLE_MATCH_MIN_SCORE=4` 暂不调整
  - Vancouver 风格候选引用导出：基于 Crossref/PubMed 的题名、期刊、年份和 DOI 生成不含作者/卷期/页码的保守候选格式，并同步到前端、Markdown 建议书和 Alex Writer 交接文本
  - Vancouver 候选引用元数据增强：从 Crossref 解析作者、卷、期、页码或 article number；作者超过 6 个时按前 6 个加 `et al` 输出，缺失字段不编造
  - 前端推荐依据、候选引用清单、Alex Writer 交接文本和 Markdown 导出已同步展示 Crossref/DOI 链接与候选引用草稿
  - Vancouver 候选引用清单独立导出 MVP：Mentor 候选引用清单新增“导出引用”入口，可将“确认可用”的候选文献按 DOI / PMID / 题名去重后导出为 `references-vancouver.md`，包含候选 Vancouver、PMID、DOI、PubMed/Crossref 链接、来源课题、全文核对状态、引用用途、复核人、复核备注和待人工核对项
- 未完成：
  - 联网真实趋势数据库
  - NCBI 实际限速行为验证；当前相关性排序和人工复核字段仍不等于系统综述或正式引用质量评价
  - 数据库级正式引用库、拖拽式或批量字段引用编辑、目标期刊级完整正式引用格式导出和可编辑写作草稿版本管理
  - Crossref 更大样本量验证、期刊缩写规范化和目标期刊引用格式适配
  - 根据真实文献计量结果自动更新趋势热度
  - 自动引用真实 PMID / DOI 和代表性文献
  - 字段级差异对比与选择性合并
- 当前结论：
  - 已补齐本地可用闭环，可用于早期选题和研究方向建议；但趋势数据仍是本地静态知识库，不应当视为真实文献计量结果

### 2. Project Manager Rhea（项目督促员）

- 已完成：
  - 项目面板基础结构
  - 阶段/任务/提醒原型
  - 计划草稿生成与应用
  - 风险提醒展示
- 部分完成：
  - 项目进度仪表盘
  - 提醒刷新与归档
- 未完成：
  - Telegram / Email 真实发送
  - 自动重排期
  - 双项目资源冲突计算
- 当前结论：
  - 原型可演示，但还不是完整督促系统

### 3. Dr. Data Lin（数据分析师）

- 已完成：
  - 数据需求清单
  - CSV 上传与字段覆盖检查
  - 缺失率、唯一值、数值范围质控
  - 脱敏与隐私风险检查
  - 数据操作审计日志
  - 描述统计草稿
  - 候选检验建议
  - 图表预览与 SVG 导出
  - 可复现实验脚本导出
  - 正式检验人工确认流程
  - 正式检验原型：
    - Welch t
    - 宽表配对 t
    - 长表两条件配对 t
    - 长表 Friedman
    - 单因素 ANOVA
    - Welch ANOVA
    - Kruskal-Wallis
  - 事后比较：
    - Tukey HSD 风格
    - Games-Howell 风格
    - Dunn 风格
    - 配对秩和风格
  - 多重比较校正：
    - Holm-Bonferroni
    - Benjamini-Hochberg FDR
  - 重复测量 ANOVA 设计识别与边界判断（`rm_anova`）
- 未完成：
  - SciPy 安装后的精度路径实测
  - 完整 repeated-measures ANOVA 统计量计算
  - 混合效应模型
  - 更强专用统计库复核
- 是否影响整体使用：
  - 不构成当前全局主阻塞
  - 影响的是统计严谨度上限，不影响原型继续向虚拟导师和写作助手扩展
- 当前结论：
  - 这是目前最成熟的一条产品线

### 4. Alex Writer（SCI 写作助手）

- 已完成：
  - 与数据分析结果的基础衔接
  - Results 摘要交接原型
- 未完成：
  - 写作风格学习
  - 文献真实检索与引用管理
  - Methods / Discussion 全链路写作，以及 Introduction 草稿的风格润色与版本管理
  - 期刊模板排版与投稿清单
- 当前结论：
  - 仍处于早期原型阶段

### 5. Rev. Dr. Helena Skov（审稿官）

- 已完成：
  - 角色定义
  - Agent 注册与基础对话入口
- 未完成：
  - 模拟审稿报告
  - AI 痕迹审查
  - Response to Reviewers 草稿
- 当前结论：
  - 基本尚未落地

### 6. 平台与基础设施

- 已完成：
  - 前后端原型
  - SQLite 持久化
  - 项目权限原型
  - 本地单用户使用路径
- 部分完成：
  - DeepSeek / OpenAI 可切换的基础调用结构
- 未完成：
  - PostgreSQL / Redis / Celery
  - Telegram / Email
  - 真实文献检索
  - 代码执行沙箱产品化
- 当前结论：
  - 当前更接近“可运行原型”，还不是完整平台

## 当前优先级建议

1. 增强 Prof. RadOnc Mentor 的真实文献证据能力：PubMed / Crossref 检索、趋势计量、PMID / DOI 引用和代表文献复核
2. 再补 Alex Writer 的 Methods / Results 连贯草稿能力
3. 最后回到 Dr. Data Lin 的高阶统计增强：完整 repeated-measures ANOVA、mixed effects model、SciPy 精度复核
