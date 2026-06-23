# 当前模块进度表

更新日期：2026-06-23

## 总体判断

当前项目已经推进到“可带公开医学/放疗样例数据跑通论文写作、后端版本归档、真实审稿意见映射、目标期刊规则校验、Reviewer 收尾验收、第一版高级统计模型拟合、statsmodels Cox/MixedLM 生产化优先路径和外部验证计划导出”的阶段。整体完成度约 **98.8%**；如果只看 5 个核心智能体能力，平均完成度约 **90%**。

当前主链路已经闭环：

```text
Mentor 选题与引用
→ Vera Protocol 研究方案
→ Data Lin 数据质控、统计草案、高级模型计划、线性/Logistic/Cox/Mixed-effects 模型拟合与外部验证计划
→ Alex Writer 英文论文草稿、投稿材料、后端版本库
→ Helena Reviewer 投稿前审查、真实审稿意见映射、英文回复草稿
```

## 五个智能体进度

| 智能体 | 完成度 | 当前状态 |
|---|---:|---|
| Prof. RadOnc Mentor | 76% | 可生成课题推荐、加载预备真实引用、复核候选引用、导出引用清单，并将推荐写入方案；下一阶段重点是扩展真实放疗论文引用源与主题证据链 |
| Dr. Vera Protocol | 80% | 可编辑/保存研究方案，生成方案草案和执行计划草案，完成方案质量检查、方案-数据一致性检查、方案版本快照与导出；下一阶段重点是真实伦理/数据字典字段适配 |
| Dr. Data Lin | 99.2% | 可上传 CSV、选择预备 DATA、做质控/隐私检查/统计草案/图表/审计、一键联调 Writer，生成自主分析计划、高级模型计划和高级模型外部验证计划；当前可执行 exploratory linear/logistic，并优先使用 statsmodels PHReg / MixedLM 执行 Cox 与 mixed-effects，失败时回退内部近似路径；Cox / mixed-effects 已补充结构化诊断交接字段和前端外部复核交接展示 |
| Alex Writer | 99% | 可生成英文 Introduction、Methods / Results、Discussion、Abstract、Cover Letter、投稿包检查清单、目标期刊模板和 Author Guidelines URL 抓取/本地规则校验，并支持放疗计划质量字段解读、高级模型结果来源、pending external validation 英文边界提示、后端版本归档、恢复 Introduction、版本差异查看、历史章节复制、全文恢复逐字段编辑和 Reviewer 修改提醒 |
| Rev. Dr. Helena Skov | 99% | 可生成投稿前规则清单、深度审稿意见、Response to Reviewers 草稿，并支持放疗专科风险检查、高级模型 OR/HR/Mixed-effects 报告边界检查、高级模型外部验证缺口检查、AI 写作痕迹/模板化风险检查、复杂审稿信规则增强拆分、目标期刊专属审稿维度、真实审稿意见导入、逐条映射、英文回复导出、返修写作清单和章节归属持久化修正；下一阶段以真实 UI 验收和小问题修正为主 |

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
- 新增 Cox 生存分析样例 CSV：16 行脱敏模拟随访记录，覆盖 follow-up time、event/status、剂量学协变量、计划复杂度和治疗部位字段，用于 HR 输出联调。
- 新增 mixed-effects 重复测量样例 CSV：24 行脱敏模拟重复观测记录，覆盖 case_code cluster、fraction_index、剂量学协变量、计划复杂度和治疗部位字段，用于 cluster 输出联调。
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
  - 若当前已有统计草案和高级模型结果，一键联调会直接切换到 Writer，并保留高级模型输出与外部验证提示。

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
- 高级模型外部验证计划：
  - 根据推荐或已执行模型生成 linear/logistic/Cox/mixed-effects 专属验证清单。
  - Logistic 覆盖事件编码、events per variable、separation、calibration、ROC 和 cross-validation。
  - Cox 覆盖事件/删失编码、ties、event count、比例风险假设和 Schoenfeld residuals。
  - Mixed-effects 覆盖 cluster、random intercept/slope、ML/REML、收敛、残差和 ICC。
  - Linear 覆盖 residuals、normality、heteroscedasticity、influential points 和 collinearity。
  - 可导出 `advanced-model-validation-plan.md`。
  - 导出后页面会显示文件名确认；如果浏览器未自动下载，可复制验证计划内容作为兜底。
- 高级模型执行第一版：
  - 可作为 exploratory draft material 执行；如果正式确认项未完成，会在 warnings 中写入人工核验提示。
  - 当前支持 multivariable linear regression。
  - 输出英文 Methods / Results 草稿、系数表、R-squared、adjusted R-squared、警示项和导出 `advanced-linear-model-fit.md`。
  - 当前支持 binary logistic regression 第一版。
  - 放疗样例中 `qa_result` 会按 `Pass` vs `non-Pass` 编码，输出 exploratory odds ratio、95% CI、P 值、收敛/稀疏事件警示和导出 `advanced-logistic-model-fit.md`。
  - 已完成浏览器 UI 验收：生成模型计划后可运行推荐 Logistic 模型，并显示 `Binary logistic regression` / OR 输出。
  - 当前支持 Cox proportional hazards model 第一版生产化优先路径。
  - CSV 中存在 follow-up time 和 event/status 字段时，优先使用 statsmodels `PHReg` 生成 exploratory hazard ratio、95% CI、P 值、事件数、删失/ties/比例风险假设复核提示，并导出 `advanced-cox-model-fit.md`；若 statsmodels 不可用或拟合失败，会回退内部 Cox partial-likelihood 近似。
  - Cox fit report 已新增结构化 `diagnostic_handoff`，覆盖 complete cases、events、censored records、time/event columns、Schoenfeld residuals、PH assumption、事件数限制和 HR 交接材料；API 与浏览器 UI 验收通过。
  - 当前支持 linear mixed-effects model 第一版生产化优先路径。
  - CSV 中存在重复测量字段和 cluster 分组时，优先使用 statsmodels `MixedLM` random-intercept 路径生成 fixed-effect estimate、random intercept variance、residual variance、ICC、cluster 数和收敛/随机效应复核提示，并导出 `advanced-mixed-effects-fit.md`；若 MixedLM 不可用或拟合失败，会回退 clustered linear approximation。
  - Mixed-effects fit report 已新增结构化 `diagnostic_handoff`，覆盖 clusters、singleton clusters、median cluster size、ICC、random-effect structure、singular fit、residual diagnostics 和 variance components 交接材料；API 与浏览器 UI 验收通过。

当前仍未完成：

- Cox 和 mixed-effects 已接入 statsmodels 优先拟合路径，但正式 SCI 报告前仍需要独立统计复核，包括 PH assumption、Schoenfeld residuals、random-effects 结构、收敛、残差诊断和样本量限制。
- lifelines、R survival、R lme4/nlme、SAS PROC MIXED 等外部软件尚未被系统自动调用；当前仍通过 `advanced-model-validation-plan.md` 提供交接清单。
- 真实放疗专科数据接入和数据许可核对。

### 4. Alex Writer

- 英文 Introduction 草稿可编辑和保存。
- 候选引用可插入背景段、研究空白段和目的段。
- 字段级引用映射和引用质控。
- Methods / Results 草稿和导出 `methods-results-draft.md`。
  - 可读取高级模型拟合结果，并显示高级模型来源与人工核验提示。
  - Logistic 输出会标注 OR-based exploratory model，提醒复核事件编码、事件数、收敛、CI、P 值和样本量限制。
  - Cox 输出会标注 HR-based exploratory survival model，提醒复核随访起点、事件编码、删失、比例风险假设、CI、P 值和样本量限制。
  - Mixed-effects 输出会标注 clustered exploratory mixed-effects approximation，提醒复核 cluster 分组、随机效应结构、收敛、残差诊断、CI、P 值和样本量限制。
  - 所有高级模型输出会加入 pending external validation 英文边界提示，避免把探索性输出写成最终 SCI 推断。
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
- 高级模型 OR/HR/Mixed-effects 报告边界检查：确认 Logistic OR、Cox HR 或 mixed-effects approximation 未被写成因果结论、已验证预测/预后模型或正式随机效应推断，并核对事件编码、事件数、收敛、删失、比例风险假设、cluster 数、重复观测、随机效应结构、CI、P 值和样本量限制。
- 高级模型外部验证缺口检查：Reviewer 会提示当前模型仍需 validated statistical environment 复核，并按模型列出残差/校准/PH/random-effects 等关键核验项。
- AI 写作痕迹与模板化风险检查：检查未替换占位符、过度宣传或因果化表述、AI 模板语、非英文残留和 Generative AI assistance disclosure 是否未确认。
- 目标期刊专属审稿维度：
  - 读取目标期刊模板和 Author Guidelines 本地规则校验结果。
  - 新增摘要与关键词、伦理与声明、图表/引用/投稿材料三类 Reviewer 检查项。
  - Reviewer 面板统计、导出清单和流程总览使用合并后的通用 + 期刊专属检查清单。
- 目标期刊专属检查人工对照验收：
  - Reviewer 面板显示目标期刊模板、Author Guidelines 来源、已识别规则数量和目标期刊检查状态。
  - 提供从 Writer 规则校验到 Reviewer 目标期刊检查的人工核验路径。
- 期刊社群/栏目专属审稿口径：
  - Medical Physics / JACMP 相近口径：放疗物理方法学、QA、TPS/算法、剂量学指标和可复现性。
  - Frontiers-style：开放科学声明、article type、结构化摘要、关键词和补充材料。
  - General oncology：临床队列、伦理边界、主要终点和临床解释谨慎性。
- 返修写作清单：
  - 按 Introduction、Methods / Results、Discussion、Abstract、Cover Letter / Submission 聚合真实审稿意见。
  - 可人工修正每条审稿意见的影响章节，并通过后端字段持久化保存。
  - Reviewer 和 Writer 两侧同步读取最终章节归属。
  - 在 Writer 面板显示各章节未解决修改提醒。
  - 导出 `writer-revision-checklist.md`，并注明章节归属需人工确认。

当前仍未完成：

- Reviewer 进入收尾验收阶段，后续以真实样例 UI 验收和小问题修正为主。
- Response to Reviewers 的默认英文回复仍偏模板化、生硬；后续需要改为更自然的 point-by-point 回复语气，并根据审稿意见内容生成更具体的回应。
- 真实审稿意见目前主要按规则拆分和章节映射；后续需要增强自动识别段落、具体内容类型和对应稿件位置的能力，减少人工分配章节和定位的负担。

## 当前优先级建议

1. 真实样例 UI 验收：
   - 使用预备 DATA、预备引用、模拟 decision letter 和目标期刊 Author Guidelines 跑完整链路。
   - 重点确认 Reviewer 导入、章节归属、Writer 修改提醒、导出文件和 Page / Lines / Manuscript location 占位。
   - 重点观察英文审稿回复是否过于生硬，以及系统是否能把意见映射到合适章节和具体内容。
   - 2026-06-24 已完成导出/复制兜底修复验收：高级模型验证计划在剪贴板不可用时会显示只读文本框，关键 Markdown 导出会显示文件名提示。
2. Data Lin 下一阶段：
   - 在现有 statsmodels PHReg / MixedLM 优先路径基础上，补充更系统的诊断输出与外部复核交接：PH assumption、Schoenfeld residuals、convergence、singular fit、random-effects 结构、ICC 和样本量限制。
3. 真实放疗专科数据适配：
   - 建立正式数据字典、字段映射和数据许可核对清单。
   - 将 TPS 版本、剂量计算算法、gamma criteria、结构命名规则纳入数据需求。
4. Writer 下一阶段：
   - 写作风格学习与目标期刊英文表达偏好。
   - Response to Reviewers 语气润色：降低模板感，让回复更像真实作者逐条回应。
   - 更稳定的 PDF / 强 JS Author Guidelines 处理方案。
5. Mentor / Protocol 下一阶段：
   - 扩展真实放疗论文引用源。
   - 将研究假设、PECO/PICO、伦理材料和数据字段进一步绑定。

## 下一阶段路线图

### 阶段 A：验收与稳定化

- 跑完整 UI 验收清单。
- 修复真实样例中暴露的小问题。
- 已完成导出/复制兜底小修复：验证计划复制失败时提供页面内手动复制文本框，Data Lin / Writer / Reviewer 关键导出路径统一下载 helper。
- 当前本地开发节奏调整为先完成一个完整功能模块再考虑上传；正在收口 Reviewer / Writer 返修链路增强模块，包括更具体的英文回复骨架、章节归属、Writer 返修聚合提醒和导出验收。
- 确认页面中文、论文正文/投稿材料英文的规则在所有导出中稳定执行。
- 收集真实审稿意见样例，评估 Response to Reviewers 默认回复的自然度和具体性。

### 阶段 B：真实数据适配

- 从模拟放疗计划质量 DATA 过渡到可授权的真实脱敏样例。
- 完成字段字典、缺失值策略、隐私筛查、审计记录和数据许可核对。

### 阶段 C：高级统计扩展

- Cox survival analysis 和 mixed-effects model 已完成第一轮诊断交接增强：fit report、验证计划导出和前端结果卡片均显示外部复核材料。
- 后续继续强化专用统计库验证路径、交叉验证/校准和更细粒度的人工统计复核提示。

### 阶段 D：投稿前生产化

- 扩展 Author Guidelines PDF / 强 JS 页面处理。
- 完成目标期刊风格化英文写作和 Response to Reviewers 定稿辅助。
- 增强真实审稿意见的段落识别、内容类型识别和稿件位置推荐，支持更精确的返修定位。
