# 当前模块进度表

更新日期：2026-06-20

## 总体判断

当前项目已经推进到“可带公开医学示例数据跑通论文写作、后端版本归档、真实审稿意见映射和高级统计模型计划，并可执行第一版线性回归模型拟合”的阶段。整体完成度约 **97%**；如果只看 5 个核心智能体能力，平均完成度约 **86%**。

当前主链路已经闭环：

```text
Mentor 选题与引用
→ Vera Protocol 研究方案
→ Data Lin 数据质控、统计草案、高级模型计划、线性/Logistic 回归拟合
→ Alex Writer 英文论文草稿、投稿材料、后端版本库
→ Helena Reviewer 投稿前审查、真实审稿意见映射、英文回复草稿
```

## 五个智能体进度

| 智能体 | 完成度 | 当前状态 |
|---|---:|---|
| Prof. RadOnc Mentor | 74% | 可生成课题推荐、加载预备真实引用、复核候选引用、导出引用清单，并将推荐写入方案 |
| Dr. Vera Protocol | 78% | 可编辑/保存研究方案，生成方案草案和执行计划草案，完成方案质量检查、方案-数据一致性检查、方案版本快照与导出 |
| Dr. Data Lin | 95% | 可上传 CSV、选择预备 DATA、做质控/隐私检查/统计草案/图表/审计、一键联调 Writer，生成自主分析计划和高级模型计划，并可执行第一版 exploratory linear/logistic regression |
| Alex Writer | 99% | 可生成英文 Introduction、Methods / Results、Discussion、Abstract、Cover Letter、投稿包检查清单、目标期刊模板和 Author Guidelines URL 抓取/本地规则校验，并支持放疗计划质量字段解读、高级模型结果来源与人工核验提示、后端版本归档、恢复 Introduction、版本差异查看、历史章节复制、全文恢复逐字段编辑和 Reviewer 修改提醒 |
| Rev. Dr. Helena Skov | 98% | 可生成投稿前规则清单、深度审稿意见、Response to Reviewers 草稿，并支持放疗专科风险检查、高级模型 OR 报告边界检查、AI 写作痕迹/模板化风险检查、复杂审稿信规则增强拆分、目标期刊专属审稿维度、真实审稿意见导入、逐条映射、英文回复导出、返修写作清单和章节归属持久化修正 |

## 已完成的关键闭环

### 1. 工作台与流程导航

- Project A / B 横向排列。
- 5 个智能体横向排列。
- 左侧工作区固定为：角色对话、当前任务、Rhea 监控。
- 右侧显示当前智能体主工作区。
- “论文流程总览”可显示：
  - 高级分析已规划
  - Writer 版本已归档
  - Reviewer 返修映射中
- “主流程快捷操作”支持：
  - 加载预备引用
  - 加载预备 DATA
  - 一键联调到 Writer
  - 高级模型计划
  - 保存 Writer 版本
  - 导入/查看审稿意见映射

### 2. 预备 DATA 联调包

- 新增放疗计划质量样例 CSV：20 行脱敏模拟计划记录，覆盖剂量学、QA、计划复杂度和治疗技术字段。
- Writer Methods / Results 可识别放疗字段并生成 target coverage、OAR dose、QA gamma pass rate、delivery time 和 plan complexity 相关英文专科提示。
- Reviewer 可提示 PTV/OAR 指标定义、gamma criteria、TPS 版本、剂量计算算法和计划审批流程等放疗专科风险。
- 保留公开医学示例 CSV：`MIMIC-IV Clinical Database Demo v2.2` 派生 50 行样本。
- 新增预备引用 JSON 和说明文档。
- Data Lin 可一键完成：
  - 选择并加载预备 CSV
  - 生成质控报告
  - 生成统计草案
  - 保存分析记录
  - 切换到 Alex Writer

### 3. Dr. Data Lin

- CSV 上传与质控。
- 脱敏与隐私检查。
- 数据需求字段覆盖检查。
- 描述性统计草案。
- 分组比较草案。
- 图表预览与导出。
- 正式检验人工确认入口。
- 分析记录保存和恢复。
- 数据审计日志。
- 自主分析计划建议和导出 `analysis-plan-suggestion.md`。
- 高级统计模型计划：
  - linear regression
  - logistic regression
  - Cox proportional hazards model
  - mixed-effects model
- 高级模型计划导出 `advanced-model-plan.md`。
- 高级模型执行第一版：
  - 可作为 exploratory draft material 执行；如果正式确认项未完成，会在 warnings 中写入人工核验提示。
  - 当前支持 multivariable linear regression。
  - 输出英文 Methods / Results 草稿、系数表、R-squared、adjusted R-squared、警示项和导出 `advanced-linear-model-fit.md`。
  - 当前支持 binary logistic regression 第一版。
  - 放疗样例中 `qa_result` 会按 `Pass` vs `non-Pass` 编码，输出 exploratory odds ratio、95% CI、P 值、收敛/稀疏事件警示和导出 `advanced-logistic-model-fit.md`。
  - 已完成浏览器 UI 验收：生成模型计划后可运行推荐 Logistic 模型，并显示 `Binary logistic regression` / OR 输出。

当前仍未完成：

- 生存分析、混合效应模型拟合。
- SciPy / statsmodels / lifelines 等专用统计库完整生产路径。
- 真实放疗专科数据接入和数据许可核对。

### 4. Alex Writer

- 英文 Introduction 草稿可编辑和保存。
- 候选引用可插入背景段、研究空白段和目的段。
- 字段级引用映射和引用质控。
- Methods / Results 草稿和导出 `methods-results-draft.md`。
  - 可读取高级模型拟合结果，并显示高级模型来源与人工核验提示。
  - Logistic 输出会标注 OR-based exploratory model，提醒复核事件编码、事件数、收敛、CI、P 值和样本量限制。
- Discussion 草稿和导出 `discussion-draft.md`。
- Abstract 草稿和导出 `abstract-draft.md`。
- Cover Letter 草稿和导出 `cover-letter-draft.md`。
- 投稿包检查清单和导出 `submission-package-checklist.md`。
  - 可生成 Ethics / IRB、Consent、Conflict of interest、Funding、Data availability 和 Generative AI assistance disclosure 英文占位声明。
  - 投稿包规则检查会把上述声明拆成独立复核项，避免 Author Guidelines 校验长期停留在缺材料状态。
- 目标期刊模板和导出 `journal-submission-template.md`。
- Author Guidelines 本地规则校验：
  - 可粘贴目标期刊 Author Guidelines URL / 来源备注和关键文本。
  - 可从普通 HTML Author Guidelines URL 抓取标题和正文文本，自动填入本地规则校验框。
  - 提取 abstract word limit、keywords、ethics / IRB、conflict of interest、funding、data availability、figures / tables、reference style 等规则信号。
  - 与当前 Abstract、Cover Letter、投稿包和引用质控状态对照。
  - 导出 `journal-guideline-check.md`。
- 后端版本库：
  - 保存当前英文稿件快照
  - 查看历史版本
  - 恢复 Introduction
  - 查看当前稿件与历史快照的章节差异
  - 复制历史版本中的派生章节
  - 恢复全文草稿第一版：Introduction 写回后端，其他章节作为历史恢复内容优先显示
  - 历史恢复的 Methods / Results、Discussion、Abstract、Cover Letter 可逐字段编辑，并可纳入新的版本快照
  - 清除历史恢复内容，回到自动生成草稿
  - 导出 `writer-version-diff.md`
- 版本快照导出 `draft-version-snapshot.md`。

当前仍未完成：

- 目标期刊官网规则自动抓取仍为 HTML 第一版；PDF、登录、强 JS 或反爬页面仍需手动粘贴。
- 写作风格学习。

### 5. Rev. Dr. Helena Skov

- 投稿前规则型审稿清单。
- 风险分级：高风险 / 需复核 / 已通过。
- 深度审稿意见和导出 `reviewer-deep-comments.md`。
- Response to Reviewers 草稿和导出 `response-to-reviewers-draft.md`。
- 真实审稿意见导入。
- 真实审稿意见 UI 验收辅助：
  - Reviewer 面板可一键填入模拟 decision letter 样例，但不会自动导入。
  - 面板内显示人工验收路径，覆盖拆分、类型/状态保存、章节归属持久化、Writer 修改提醒和导出核验。
- 复杂审稿信规则增强拆分：
  - 先识别 Editor / Reviewer 分块。
  - 再按 Major / Minor / Editorial、Comment / Point / Concern、数字或字母编号拆分条目。
  - 拆分后保留 Reviewer 标签，并用于英文 response draft、状态管理和章节映射。
- 复杂 decision letter 异常拆分提示：
  - 导入时识别长信只拆出 1 条、过短碎片、Reviewer 标签缺失等风险。
  - 前端导入提示和单条审稿意见卡片显示醒目的人工核验提示。
- Major / Minor / Editorial 自动初分。
- 逐条英文 response draft。
- Response to Reviewers 定位占位：
  - 新导入条目的英文 response draft 包含 Page、Lines、Manuscript location 人工占位。
  - Reviewer 卡片显示返修信定位需人工补齐提示。
  - `response-to-reviewers-mapped.md` 导出会为旧数据补齐定位占位，并列出人工必须补齐项。
- 条目状态管理：草稿、处理中、已解决、暂缓。
- 映射回复导出 `response-to-reviewers-mapped.md`。
- 高级模型 OR 报告边界检查：确认 Logistic OR 未被写成因果结论或已验证预测模型，并核对 `Pass` vs `non-Pass` 编码、事件数、收敛、CI、P 值和样本量限制。
- AI 写作痕迹与模板化风险检查：检查未替换占位符、过度宣传或因果化表述、AI 模板语、非英文残留和 Generative AI assistance disclosure 是否未确认。
- 目标期刊专属审稿维度：
  - 读取目标期刊模板和 Author Guidelines 本地规则校验结果。
  - 新增摘要与关键词、伦理与声明、图表/引用/投稿材料三类 Reviewer 检查项。
  - Reviewer 面板统计、导出清单和流程总览使用合并后的通用 + 期刊专属检查清单。
- 返修写作清单：
  - 按 Introduction、Methods / Results、Discussion、Abstract、Cover Letter / Submission 聚合真实审稿意见。
  - 可人工修正每条审稿意见的影响章节，并通过后端字段持久化保存。
  - Reviewer 和 Writer 两侧同步读取最终章节归属。
  - 在 Writer 面板显示各章节未解决修改提醒。
  - 导出 `writer-revision-checklist.md`，并注明章节归属需人工确认。

当前仍未完成：

- Reviewer 98% 收尾清单：
  - 更细颗粒度的期刊社群/栏目专属审稿口径，例如 Medical Physics、JACMP、Frontiers 不同栏目规则。
  - 目标期刊专属 Reviewer 检查与 Author Guidelines 抓取结果的人工对照验收。

## 当前优先级建议

1. 人工完整跑一遍 UI 验收清单。
2. 阶段性提交当前大功能集合。
3. 后续优先补：
   - 真实高级统计模型拟合
   - 真实放疗专科数据适配
   - 目标期刊 PDF / 强 JS 页面规则抓取
