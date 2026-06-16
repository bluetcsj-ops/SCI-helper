# 当前模块进度表

更新日期：2026-06-17

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
  - 前端候选文献人工复核：可将推荐依据标记为“待复核 / 确认可用 / 排除”，并同步到 Markdown 建议书导出
  - 候选文献复核状态持久化：项目级保存 Mentor 推荐依据的复核状态，重新生成推荐卡后可按 PMID / DOI / 本地证据键恢复
  - 候选引用清单：自动汇总“确认可用”的推荐依据，展示题名、期刊、年份、PMID、DOI 和来源课题，并同步导出到 Markdown
  - Alex Writer 联动：可将候选引用清单交给 Alex Writer，生成 Introduction / Discussion 写作提纲和仍需补充检索的项目清单
  - Alex Writer 写作工作区：展示基于候选引用的 Introduction / Discussion 本地提纲、候选引用列表和写作前检查清单
  - Alex Writer 写作提纲 Markdown 导出：可将本地提纲、项目研究问题、主要终点、候选引用和写作前检查清单导出为 `alex-writer-outline.md`
- 未完成：
  - 联网真实趋势数据库
  - PubMed 联网环境下的真实请求实测和速率限制策略；当前沙箱网络会触发访问套接字权限错误，联网审批未返回
  - 字段级引用管理、正式引用格式导出和可编辑写作草稿保存
  - Crossref 等外部证据自动检索和结果解析
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
  - Introduction / Methods / Discussion 全链路写作
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
