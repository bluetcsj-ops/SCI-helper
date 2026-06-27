# 项目交接记录

更新时间：2026-06-26

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的本地原型工程。当前目标是建立可运行、可扩展、可带示例医学数据跑通的多智能体论文工作台，并逐步接入真实科研数据、真实文献检索、英文论文写作、审稿和投稿准备能力。

## 当前状态

当前 `main` 分支已完成 Data Lin 高级模型生产化优先路径、Writer / Reviewer 返修写作清单阶段成果、mixed-effects model 第一版可执行路径、Mentor → Vera Protocol 草案交接、项目级聊天记忆共享、按项目/智能体隔离聊天历史，以及 Mentor 自定义研究方向优先生成。最新状态：

- Data Lin 高级模型面板可显示“统计验证计划”。
- 可按 linear/logistic/Cox/mixed-effects 生成模型专属外部验证清单。
- Cox 默认优先使用 statsmodels `PHReg`，失败时回退内部 Cox partial-likelihood 近似。
- Mixed-effects 默认优先使用 statsmodels `MixedLM` random-intercept 路径，失败时回退 clustered linear approximation。
- Cox / mixed-effects fit report 已新增结构化 `diagnostic_handoff`，前端会在统计验证计划和模型结果卡片中显示样本背景、必做诊断、交接材料和 Reviewer 复核焦点。
- 可导出 `advanced-model-validation-plan.md`，用于把 exploratory 输出交给 validated statistical environment 复核。
- 导出后页面显示文件名确认，并提供“复制验证计划”兜底，便于人工验收下载是否成功。
- Writer Methods / Results 会写入 pending external validation 英文边界提示。
- Reviewer 检查清单新增“高级模型外部验证缺口”，提示残差、校准、PH assumption、Schoenfeld residuals、random effects、ICC 等模型特异核验项。
- Project A / B 现在只作为工作区容器和流程演示样例，不代表真实机构 protocol。
- Mentor 不再直接用固定 topic 模板出题，而是先根据设备、计划系统、可用数据和 Mentor 对话摘要生成自定义研究方向；预设 topic 只作为证据检索、趋势对照和目标期刊入口的辅助标签。
- 当前项目聊天记录支持项目级共享上下文；历史聊天视图按当前项目 + 当前智能体隔离展示，并支持清空当前智能体记录。

当前整体完成度约 **99.2%**。主链路已经闭环：

```text
Mentor → Vera Protocol → Data Lin → Alex Writer → Reviewer
```

## 当前核心能力

### Mentor

- 自定义研究方向候选生成。
- 预备真实引用加载。
- 本地真实放疗候选文献包：
  - MR-guided adaptive radiotherapy
  - FLASH
  - AI / Planning / QA
  - Particle therapy
  - Radiomics
  - Automation / knowledge-based planning
  - SRS / SBRT
  - Motion management
- 候选文献保留 PMID、DOI、PubMed 链接、DOI 链接、候选 citation 和 Vancouver 候选引用。
- Mentor 推荐依据卡片显示人工核验缺口，覆盖全文核对、PMID、DOI、Vancouver 候选引用、作者、期刊、年份、卷期页码和 Introduction / Discussion 用途标记。
- 候选引用复核、用途标记、全文核对。
- Vancouver 候选引用导出。
- 候选方向生成 Vera Protocol 草案；预览方案会同步研究假设、PICO/PECO、主要终点、最小数据字段、实验流程、统计路线、正式研究前确认和 Mentor 来源追踪。
- Mentor 推荐接口接收 `discussion_summary`，前端会把当前项目 Mentor 对话摘要纳入方向生成。
- 已通过烟测确认：在 `TOMO / TrueBeam + Eclipse / Accuray + DICOM RTDose / RTStruct / RTPlan` 场景下，系统返回计划剂量学、DICOM 计划复杂度、字段字典验证方向，不再误生成 MR / 在线自适应方向。

### Vera Protocol

- 结构化研究方案编辑与保存。
- 方案草案和 Rhea 执行计划草案。
- 方案质量检查。
- 方案-数据一致性检查。
- Mentor 推荐卡生成草案后可检查最小数据字段、正式研究前确认项、数据字典/导出路径和放疗计划系统边界。
- Mentor 推荐卡会合成为完整 Vera 草案，覆盖研究假设、PICO/PECO、主要/次要终点、纳排标准、数据路径、实验流程、统计边界和 Rhea 里程碑。
- 规则版 Mentor discussion brief 已接入：当前项目的 Mentor 对话、Mentor 表单和推荐报告会提取为用户倾向、限制、资源、数据线索和待确认问题，并进入 Vera 方案草案预览。
- Mentor 讨论历史可恢复：`GET /api/projects/{project_id}/chat/messages?agent_id=mentor` 返回最近历史消息，前端刷新后仍可把历史 Mentor 讨论合并进 discussion brief。
- 所有智能体聊天请求可携带项目级共享聊天摘要，Vera 后续回复能看到 Mentor 方向讨论、用户限制和已确认资源。
- 方案-数据一致性检查可显示 Protocol 最小字段写入状态和 Data Lin 从方案读取到的必需字段数量。
- 正式研究前确认项可显示 5 张卡：候选字段字典、伦理与数据许可确认、计划系统与 DICOM 确认、CSV 字段映射、统计复核边界。
- 方案版本快照。
- 导出：
  - `protocol-quality-check.md`
  - `protocol-data-consistency-check.md`
  - `protocol-version-snapshot.md`

### Dr. Data Lin

- CSV 上传与质控。
- 脱敏和隐私检查。
- 描述性统计、分组比较、图表预览。
- 正式检验人工确认入口。
- 分析记录保存和恢复。
- 数据审计日志。
- 字段需求区分类展示：
  - 最小字段
  - 伦理/脱敏
  - 数据字典
  - TPS/DICOM
  - 终点/统计
  - 其他
- 每个字段需求卡显示类别标签、必需/建议状态和分类验收提示，便于核对 Mentor → Protocol 草案生成后的字段链路。
- 预备 DATA 选择和一键联调到 Writer：
  - 放疗计划质量脱敏模拟样例
  - MIMIC-IV EHR demo 样例
  - Cox 生存分析脱敏模拟样例
  - Mixed-effects 重复测量脱敏模拟样例
  - 当前已有统计草案时会直接切换到 Writer，保留高级模型拟合结果和外部验证提示；只有缺少统计草案时才重跑预备 DATA 联调。
- 自主分析计划建议。
- 高级统计模型计划：
  - linear regression
  - logistic regression
  - Cox proportional hazards model
  - linear mixed-effects model
- 高级模型外部验证计划：
  - linear：residuals、normality、heteroscedasticity、influential points、collinearity
  - logistic：events per variable、separation、calibration、ROC、cross-validation
  - Cox：event coding、censoring、PH assumption、Schoenfeld residuals
  - mixed-effects：random intercept/slope、ML/REML、convergence、residuals、ICC
- 高级模型执行：
  - multivariable linear regression
  - binary logistic regression 第一版，支持 `qa_result` 按 `Pass` vs `non-Pass` 编码
  - Cox proportional hazards model 第一版，优先使用 statsmodels `PHReg`，支持 follow-up time + event/status 字段识别和 exploratory HR 输出，失败时回退内部近似
  - linear mixed-effects model 第一版，优先使用 statsmodels `MixedLM` random-intercept 路径，支持 repeated-measures field + cluster grouping 识别和 exploratory fixed-effect / ICC 输出，失败时回退 clustered linear approximation
  - 正式确认项未完成时不阻塞 exploratory model fit，但会在 warnings 中提示人工核验边界
- 导出：
  - `analysis-plan-suggestion.md`
  - `advanced-model-plan.md`
  - `advanced-linear-model-fit.md`
  - `advanced-logistic-model-fit.md`
  - `advanced-cox-model-fit.md`
  - `advanced-mixed-effects-fit.md`
  - `advanced-model-validation-plan.md`
  - analysis parameters JSON
  - reproducible script

### Alex Writer

- 英文 Introduction 草稿、引用映射和引用质控。
- Methods / Results 草稿。
  - Writer Methods / Results 区显示“数据与方案交接摘要”，汇总 Protocol 正式研究前确认、Data Lin 字段分类、CSV 覆盖与隐私、方案-数据一致性写作边界。
  - `methods-results-draft.md` 导出包含该交接摘要，便于人工核对字段、伦理、DICOM/TPS 和统计复核风险后再改写英文正文。
  - 可识别放疗计划质量字段，补充 target coverage、OAR dose、patient-specific QA、delivery time、monitor units 和 plan complexity 的英文专科提示。
  - 可读取高级模型拟合结果，显示高级模型来源与人工核验提示。
  - Logistic 输出会标注 OR-based exploratory model，提醒复核事件编码、事件数、收敛、CI、P 值和样本量限制。
  - Cox 输出会标注 HR-based exploratory survival model，提醒复核随访起点、事件编码、删失、比例风险假设、CI、P 值和样本量限制。
  - Mixed-effects 输出会标注 clustered exploratory mixed-effects approximation，提醒复核 cluster 分组、随机效应结构、收敛、残差诊断、CI、P 值和样本量限制。
  - 高级模型输出会写入 pending external validation 提示，提醒不要把 exploratory fit 当作最终 SCI 推断。
- Discussion 草稿。
- Abstract 草稿。
- Cover Letter 草稿。
- 投稿声明占位模板：
  - Ethics / IRB
  - Consent
  - Conflict of interest
  - Funding
  - Data availability
  - Generative AI assistance disclosure
- 投稿包检查清单。
- 目标期刊模板。
- Author Guidelines 本地规则校验：
  - 粘贴目标期刊 URL / 来源备注和指南关键文本
  - 从普通 HTML Author Guidelines URL 抓取标题和正文文本，并自动填入本地规则校验框
  - 提取摘要字数、关键词、伦理、利益冲突、资助、数据可用性、图表和引用格式信号
  - 对照当前 Abstract、Cover Letter、投稿包和引用质控状态
- 后端版本库：
  - 保存当前英文稿件快照
  - 查看版本列表
  - 恢复版本的 Introduction
  - 查看当前稿件与历史快照的章节差异
  - 复制历史版本中的派生章节
  - 恢复全文草稿第一版：Introduction 写回后端，其他章节作为历史恢复内容优先显示
  - 逐字段编辑历史恢复的 Methods / Results、Discussion、Abstract、Cover Letter，并可纳入新的版本快照
  - 清除历史恢复内容，回到自动生成草稿
- Reviewer 修改提醒：
  - 按章节显示真实审稿意见的未解决修改项
  - 读取 Reviewer 侧持久化修正后的章节归属
  - 不自动改写论文正文
- 导出：
  - `alex-writer-outline.md`
  - `introduction-draft.md`
  - `methods-results-draft.md`
  - `discussion-draft.md`
  - `abstract-draft.md`
  - `cover-letter-draft.md`
  - `submission-package-checklist.md`
  - `journal-submission-template.md`
  - `journal-guideline-check.md`
  - `draft-version-snapshot.md`

### Reviewer

- 投稿前规则型审稿清单。
- 放疗专科风险检查：
  - PTV/OAR dose metric 定义
  - patient-specific QA 与 gamma criteria
  - treatment planning system version、dose calculation algorithm 和计划审批流程
- 高级模型 OR/HR 报告边界检查：
  - 确认 Logistic OR 未被写成因果结论或已验证预测模型
  - 确认 Cox HR 未被写成因果结论或已验证预后模型
- 高级模型 Mixed-effects 报告边界检查：
  - 确认 mixed-effects approximation 未被写成正式随机效应推断
  - 核对 cluster 数、重复观测、随机截距/随机斜率设定、收敛、残差诊断、CI、P 值和样本量限制
- 高级模型外部验证缺口检查：
  - 提示当前模型仍需 validated statistical environment 复核
  - 按模型类型提示 residuals、calibration、ROC、PH assumption、Schoenfeld residuals、random effects、ICC 等关键核验项
- AI 写作痕迹与模板化风险检查：
  - 检查未替换占位符、过度宣传或因果化表述、AI 模板语、非英文残留
  - 联动投稿包中的 Generative AI assistance disclosure 复核项
- 目标期刊专属审稿维度：
  - 读取目标期刊模板和 Author Guidelines 本地规则校验结果
  - 生成摘要与关键词、伦理与声明、图表/引用/投稿材料三类 Reviewer 检查项
  - Reviewer 面板统计、导出清单和流程总览使用通用 + 期刊专属合并清单
- 目标期刊专属检查人工对照验收：
  - Reviewer 面板显示目标期刊模板、Author Guidelines 来源、已识别规则数量和目标期刊检查状态
  - 提供从 Writer 规则校验到 Reviewer 目标期刊检查的人工核验路径
- 期刊社群/栏目专属审稿口径：
  - Medical Physics / JACMP 相近口径：放疗物理方法学、QA、TPS/算法、剂量学指标和可复现性
  - Frontiers-style：开放科学声明、article type、结构化摘要、关键词和补充材料
  - General oncology：临床队列、伦理边界、主要终点和临床解释谨慎性
- 深度审稿意见。
- Response to Reviewers 草稿。
- 真实审稿意见导入。
- 真实审稿意见 UI 验收辅助：
  - Reviewer 面板可一键填入模拟 decision letter 样例，但不会自动导入
  - 面板内显示人工验收路径，覆盖拆分、类型/状态保存、章节归属持久化、Writer 修改提醒和导出核验
- 复杂审稿信规则增强拆分：
  - 先识别 Editor / Reviewer 分块
  - 再按 Major / Minor / Editorial、Comment / Point / Concern、数字或字母编号拆分条目
  - 保留 Reviewer 标签，供英文 response draft、状态管理和章节映射复用
- 复杂 decision letter 异常拆分提示：
  - 导入时识别长信只拆出 1 条、过短碎片、Reviewer 标签缺失等风险
  - 前端导入提示和单条审稿意见卡片显示人工核验提示
- Major / Minor / Editorial 初分。
- 逐条英文 response draft。
- Response to Reviewers 定位占位：
  - 新导入条目的英文 response draft 包含 Page、Lines、Manuscript location 人工占位
  - Reviewer 卡片显示返修信定位需人工补齐提示
  - `response-to-reviewers-mapped.md` 导出会为旧数据补齐定位占位，并列出人工必须补齐项
- 条目状态管理。
- 风险分级。
- 返修写作清单：
  - 按章节聚合真实审稿意见
  - 支持人工修正并持久化保存每条意见的影响章节
  - 显示状态、response draft 和 manuscript change
  - 导出 `writer-revision-checklist.md`
- 导出：
  - `pre-submission-review.md`
  - `reviewer-deep-comments.md`
  - `response-to-reviewers-draft.md`
  - `response-to-reviewers-mapped.md`
  - `writer-revision-checklist.md`

Reviewer 收尾验收方向：

1. 使用模拟 decision letter 和真实审稿意见跑完整 UI 验收。
2. 将发现的小问题按导入、映射、Writer 提醒和导出分组修正。
3. 记录到的后续增强意见：
   - 当前 Response to Reviewers 默认回复偏生硬、模板化，后续应增强语气自然度和针对具体审稿意见的回应细节。
   - 后续应增加自动识别段落和内容的能力，例如识别审稿意见对应的稿件章节、具体段落、内容类型和需要修改的位置。
4. 如需进一步增强，可增加更多期刊模板或将页码/行号改为结构化字段。

Reviewer / Writer 返修链路增强模块完成标准：

1. 审稿意见导入：
   - 能识别 Editor / Reviewer 分块，并按 Major / Minor / Editorial 或编号条目拆分。
   - 复杂 decision letter 若只拆出 1 条、条目过短或缺少 Reviewer 标签，必须显示人工核验提示。
2. 英文回复草稿：
   - 真实导入的逐条回复应按统计/模型、数据/隐私、方法、伦理/投稿、图表/引用、语言/格式等主题生成更具体的英文骨架。
   - 规则型 `Response to Reviewers` 草稿也应减少重复模板句式，保留 `Specific revision target` 或 `Working item`，并避免把 exploratory OR/HR/mixed-effects 写成因果或已验证预测结论。
   - 所有回复必须保留 Page / Lines / Manuscript location 人工占位。
3. 章节归属与 Writer 联动：
   - Reviewer 侧应显示自动章节归属，并支持人工修正和持久化保存。
   - Writer 侧应按章节显示未解决返修提醒，并展示类型分布和状态分布，方便逐章处理。
4. 导出：
   - `response-to-reviewers-mapped.md` 必须包含原始审稿意见、英文回复、manuscript change、状态和定位占位。
   - `writer-revision-checklist.md` 必须按章节聚合真实审稿意见，并标注章节归属需人工确认。
5. 本地开发节奏：
   - 本模块完成前只做本地修复和本地验收；完成一个完整功能模块后，再统一考虑提交和上传。

## 当前验证记录

最近验证通过：

2026-06-27 GitHub 同步与 Mentor/Vera 样例边界收尾：

- 最新提交：`ad57058 Isolate mentor sample history from recommendations`，已推送到 `origin/main`。
- 当前进度快照：总体 `15%`，Project A `5%`，Project B `25%`。
- Project A / B 均已确认只作为预设样例工作区和流程演示容器，不代表真实机构 protocol，不得作为真实研究方案来源。
- Mentor 推荐生成已隔离历史样例对话：`discussion_summary` 不再参与资源匹配和 topic 排序，只作为追踪记录；当前候选方向依据 Mentor 表单资源、可用数据和辅助参考标签生成。
- Vera 方案预览已隔离历史 Mentor 来源摘录：主方案依据只来自当前候选方向、Mentor 表单和推荐报告；历史 Mentor 对话只保留为追踪/边界提示，不作为新 protocol 的研究依据、资源证据或真实机构材料。
- 回归测试新增 `backend/tests/test_mentor_sample_boundaries.py`，覆盖 Project A / MR 历史样例不能覆盖当前 `TOMO / TrueBeam + Eclipse / Accuray + DICOM RTDose / RTStruct / RTPlan + QA summary` 输入。
- 验证通过：`backend/.venv/Scripts/python.exe -m unittest tests.test_mentor_sample_boundaries tests.test_reviewer_comment_responses`、`backend/.venv/Scripts/python.exe -m compileall app tests`、`frontend/npm.cmd run build`、`git diff --check`。
- 最终 UI 验收通过：重启后端加载最新逻辑后，同一组非 MR + QA 样例输入的第一候选为“基于计划参数与 QA 结果的患者特异性质控风险分层研究”，MR 在线自适应候选未优先出现；Vera 预览无“来源摘录 / Mentor 讨论摘录”，无 Project A / MR 历史泄漏，仍保留 Project A/B 样例工作区边界提示；刷新后的新 console error/warn 为 0。
- 本轮没有确认生成或覆盖真实 protocol；真实 IRB、数据授权、脱敏、字段字典、TPS/DICOM/QA、统计复核仍必须由研究者人工确认。
- 下一轮建议：优先进入 Data Lin / Rhea 流程验收，确认 Vera 草案中的最小字段、数据字典、正式研究前确认项能稳定传递到字段需求、Rhea 里程碑和 Writer handoff；或继续细化 Mentor/Vera 预览文案，把“讨论依据”标签改为更准确的“当前候选依据”。

2026-06-27 Data Lin / Rhea / Writer / Reviewer 样例链路验收补充：

- Data Lin / Rhea 验收通过：Vera 当前方案质量检查 `100%`；方案-数据一致性检查能从 Protocol 读取 `29` 个必需字段并命中 `8` 类落地信号；正式研究前确认项包含候选字段字典、伦理/授权/脱敏、计划系统/DICOM/QA 和统计复核边界。
- Data Lin 字段需求承接通过：当前显示 `38` 个字段需求，来自研究方案，并按最小字段 `12`、伦理/脱敏 `6`、数据字典 `1`、TPS/DICOM `8`、终点/统计 `11` 分类展示。
- Rhea 任务链路验收通过：展开后 10 项任务覆盖研究问题锁定、伦理/数据审批、字段字典/导出路径、首批 10 例数据质控、全量清洗、统计图表、Methods/Results、全文初稿和投稿文件包。
- Data Lin → Writer handoff 验收通过：加载预备 DATA `radiotherapy_plan_quality_sample.csv` 后，流程总览“数据与统计”变为“已有质控报告 / 进行中”；Writer 出现“数据与方案交接摘要”，包含 Protocol 正式研究前确认、Data Lin 字段分类、CSV 覆盖与隐私、Methods / Results 写作边界。
- Writer Methods / Results 样例草稿保留边界：当前输出是 exploratory statistical draft，未执行 formal hypothesis testing，不报告 P 值或显著性结论；advanced regression 尚未完成，不报告回归估计。
- Reviewer / 投稿前风险联动验收通过：重新加载预备 DATA 并联调 Writer 后，Reviewer 清单显示高风险 `5`、需复核 `8`、已通过 `2`；Reviewer 能读取数据源 `radiotherapy_plan_quality_sample.csv`、`20 行 / 18 列`、原始 CSV 未持久化保存、Results 不得写 P 值或显著性结论、字段覆盖和隐私风险等边界。
- Reviewer 放疗专科风险识别通过：PTV/OAR 剂量指标定义、gamma criteria、TPS version、dose calculation algorithm、machine/MLC model 和计划审批流程进入检查；Ethics / IRB、Data availability、Generative AI assistance disclosure 等投稿声明占位被识别。
- Reviewer 导出按钮验收：`导出清单`、`导出深度意见`、`导出回复` 均可点击且无新应用 console error/warn；当前浏览器仍未显示导出文件名提示，需按既有下载事件限制处理。
- 当前仍需人工处理：预备 DATA 仅用于流程验收，字段覆盖显示 `Matched required fields: 5`、`Missing required fields: 24`；正式研究仍需补齐真实字段、正式统计检验、引用全文核验、投稿声明、Rhea 逾期任务和目标期刊 Author Guidelines 人工核对。

2026-06-27 高级模型计划 / 验证边界验收补充：

- Data Lin 高级模型计划验收通过：加载 `radiotherapy_plan_quality_sample.csv` 后先生成描述性统计草案，再生成高级模型计划；候选模型包含 `Binary logistic regression`、`Multivariable linear regression`、`Cox proportional hazards model` 和 `Linear mixed-effects model`。
- 推荐模型与缺口边界正确：当前推荐 `Binary logistic regression`，结局为 `qa_result`；Cox 显示缺少 `follow-up time` 与 `event indicator`；mixed-effects 显示需要 `repeated-measures design confirmation`。
- 外部验证计划验收通过：高级模型面板显示 `pending external validation`、外部软件清单、模型核验清单，并解锁 `导出验证计划` / `复制验证计划`；计划文本明确不得在外部验证前定稿 OR、CI、P 值、calibration、AUC 或预测模型结论。
- 推荐模型运行验收通过：`运行推荐模型` 生成 `advanced-logistic-v1` exploratory logistic 输出，`20` 个完整病例、`13` 个事件，OR/CI/P 值均被标注为人工统计复核前的草稿素材；警告包含未完成正式检验确认、样本量小、可能分离/稀疏单元、收敛复核和统计计划一致性复核。
- Writer 联动验收通过：Data Lin → Writer 后，Methods / Results 中新增高级模型来源与人工核验内容，保留 `exploratory`、`External validation status: pending`、P values / confidence intervals / manual review 边界，未把 OR 输出写成最终推断或已验证预测结论。
- Reviewer 联动验收通过：切到 Reviewer 后清单显示高风险 `5`、需复核 `10`、已通过 `2`；新增“高级模型 OR 报告边界”和“高级模型外部验证缺口”，要求核对 event coding、events per variable、separation、calibration、ROC/AUC、validation design、CI、P 值和样本量限制。
- 控制台复核：本轮高级模型验收期间未见新的应用 console error/warn；浏览器中仍有一组早于本轮的旧 `ReferenceError: allLines is not defined` 记录，时间戳为 `2026-06-26T18:58:25.949Z`，需后续另行排查 Mentor discussion brief 旧错误来源。

2026-06-27 Mentor / Vera 自主方案生成预览验收补充：

- Mentor 候选生成验收通过：点击 `生成研究方向候选` 后生成 `3` 个研究方向候选，首选为 `TOMO / TrueBeam 计划剂量学质量与 OAR 约束达成度评估`，不是历史 MR 自适应方向。
- 资源匹配边界正确：候选说明基于设备/计划系统待补充、可用数据 `DICOM RTDose, RTStruct, RTPlan` 和辅助参考标签生成；页面明确 `不依赖 Project A/B 预设 protocol`，并写明 Project A/B 只作为样例工作区，不作为真实 protocol 来源。
- Vera 预览验收通过：点击首个候选 `预览方案` 后出现 Vera Protocol 草案预览和 `确认生成` 按钮；本轮未点击 `确认生成`，未覆盖当前 Vera 方案。
- 草案边界完整：预览内容包含真实数据前人工确认项，包括 IRB、数据授权、脱敏规则、原始数据保存边界、字段字典/数据字典、TPS/DICOM/QA 追踪、统计复核和 Rhea 里程碑。
- 历史泄漏复核通过：预览中历史 Mentor 对话只作为追踪记录，不作为资源证据；未把 Project A/B 或旧 MR 自适应样例写成真实方案来源。
- 控制台复核：Mentor/Vera 预览验收期间未见新的应用 console error/warn；浏览器日志仍只保留同一组旧 `ReferenceError: allLines is not defined` 记录，时间戳为 `2026-06-26T18:58:25.949Z`。

2026-06-27 Vera synthesis 剂量学方向修复与 Data Lin 验收补充：

- 修复原因：首个 Mentor 候选为计划剂量学/OAR/RTDose 方向，但 Vera synthesis 的 population、exposure、comparator、secondary endpoints 会被候选卡中“不是沿用 Project A 的 MR 自适应题目”等否定边界里的 `adaptive / 自适应` 关键词误触发。
- 代码修复：在 `frontend/src/App.tsx` 中新增 `isDosimetricPlanQualityCard`，并让剂量学计划质量方向优先生成 PICO/PECO、主要终点、暴露、比较组和二级终点；Project A/B 样例边界、真实 IRB/授权/脱敏/字段字典边界保持不变。
- 构建验证：`npm run build` 通过，包含 `tsc && vite build`。
- UI 复验通过：重新从 Mentor 生成 `3` 个候选，点击首个候选 `预览方案` 并执行 `确认生成` 后，Vera PICO/PECO 显示 Population 为已完成外照射计划并可追踪 `RTDose / RTStruct / RTPlan`、PTV/OAR 指标；Exposure 为治疗部位、设备平台、计划技术、处方剂量、分割次数、计划复杂度和 DICOM 剂量/结构/计划参数；Comparator 为治疗部位、设备平台、计划技术、计划策略或预定义风险层级形成的剂量学分组；Outcome 为 `PTV D95% / V95%`、`OAR Dmax/Dmean`、剂量梯度、适形指数或计划复杂度。
- 泄漏复核通过：最终 Vera 表单未再出现正向 `MR-guided adaptive RT`、在线自适应计划、adaptive workflow 暴露或 adaptive workflow 可执行性；仅保留 Project A/B 样例边界和“不是沿用 Project A 的 MR 自适应题目”这类否定来源说明。
- Data Lin 字段读取验收通过：切到 Data Lin 后显示 `52` 个字段需求，分类为最小字段 `27`、伦理/脱敏 `5`、数据字典 `1`、TPS/DICOM `11`、终点/统计 `8`。
- 展开字段后确认包含：匿名病例或计划 ID、治疗部位、计划系统和版本、处方剂量与分割次数、主要终点字段、设备平台、`RTDose / RTStruct / RTPlan` 导出标识、PTV 覆盖指标、关键 OAR 约束指标、数据字典草案、真实数据边界、Project A/B 样例工作区边界、伦理/授权/脱敏、TPS/DICOM/QA 追踪和统计复核责任人。
- 控制台复核：本轮修复复验期间未见新的应用 console error/warn；Statsig 网络超时仍为外部噪声，浏览器日志仍保留旧 `ReferenceError: allLines is not defined` 记录，时间戳为 `2026-06-26T18:58:25.949Z`。

2026-06-27 新 Vera 方案下游 Writer / Reviewer 联动验收补充：

- Data Lin 预备 DATA 复验通过：在新 Vera 方案下加载 `radiotherapy_plan_quality_sample.csv` 后生成质控报告，仍显示 `52` 个字段需求；预备 DATA 为 `20 行 / 18 列`，字段覆盖更严格，Writer 侧显示 `Matched required fields: 5`、`Missing required fields: 42`。
- Data Lin 字段展开复核通过：确认字段需求包含匿名病例或计划 ID、治疗部位、计划系统和版本、处方剂量与分割次数、主要终点字段、设备平台、`RTDose / RTStruct / RTPlan` 导出标识、PTV 覆盖指标、关键 OAR 约束指标、数据字典草案、真实数据边界、Project A/B 样例工作区边界、伦理/授权/脱敏、TPS/DICOM/QA 追踪和统计复核责任人。
- Writer handoff 验收通过：`一键联调到 Writer` 后出现“数据与方案交接摘要”，字段分类显示最小字段 `27`、伦理/脱敏 `5`、数据字典 `1`、TPS/DICOM `11`；Methods / Results 继续保持 descriptive / exploratory 边界，不报告 P 值、显著性、CI 或高级模型估计。
- Writer 内容边界通过：Writer 可见 `RTDose / RTStruct / RTPlan`、PTV/OAR 和缺失字段提示；当前预备 DATA 只作为流程样例，正式研究仍需补齐真实字段、伦理/授权/脱敏、TPS/DICOM/QA 和统计复核材料。
- Reviewer 联动验收通过：切到 Reviewer 后清单为高风险 `5`、需复核 `8`、已通过 `2`；深度意见继续包含 PTV/OAR 剂量学指标定义、gamma criteria、TPS version、dose calculation algorithm、machine/MLC model、计划审批流程、字段覆盖和 P 值/显著性边界。
- 泄漏复核通过：Data Lin、Writer、Reviewer 下游页面均未出现正向 `MR-guided adaptive RT`、在线自适应计划、adaptive workflow 暴露或 adaptive workflow 可执行性。
- 控制台复核：本轮下游联动验收期间未见新的应用 console error/warn；Statsig 网络超时仍为外部噪声，浏览器日志仍保留旧 `ReferenceError: allLines is not defined` 记录，时间戳为 `2026-06-26T18:58:25.949Z`。

2026-06-27 Rhea Plan v2 应用验收补充：

- Rhea 计划草案生成通过：基于当前新 Vera Protocol 点击 `计划草案` 后生成 `Plan v2`，显示 `7` 个阶段、`10` 项任务，初始状态为 `未应用`。
- Rhea 任务覆盖通过：展开 `Plan v2` 后 10 项任务包含锁定研究问题/PICO/PECO、文献矩阵与目标期刊、伦理/数据审批、字段字典与导出路径、首批 10 例数据导出与质量核查、全量数据收集与清洗、统计分析和论文图表、Methods/Results、全文初稿、模拟审稿与投稿文件包。
- Rhea Plan v2 应用通过：点击 `应用该草案` 并确认后，Project A 任务列表替换为新计划任务，首批任务截止日期更新为 `07/04`、`07/11`、`07/21`，旧 `06/23` / `06/30` 逾期节点不再出现。
- Rhea 监控重算通过：应用后 Rhea 监控中心显示 `正常`、`0 条提醒`、`0 个逾期`、`0 个受阻`，提示当前没有需要处理的提醒。
- 方案边界仍保留：任务说明中继续包含新研究问题、RTDose/RTStruct/RTPlan、PTV/OAR、真实数据阶段脱敏和字段字典确认、Project A/B 样例流程边界。
- 泄漏复核通过：Plan v2 和 Rhea 监控未出现正向 `MR-guided adaptive RT`、在线自适应计划、adaptive workflow 暴露或 adaptive workflow 可执行性。

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
.\node_modules\.bin\tsc.cmd --noEmit
npm run build
```

后端验证通过：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
$env:DATABASE_URL='sqlite:///:memory:'
.\.venv\Scripts\python.exe -c "from app.main import app; print('backend app memory db ok')"
```

2026-06-26 Stage A 完整 UI / 导出 / 构建验收补充：

- UI smoke 通过：前端和后端均可加载，本地 app 控制台未见应用错误，核心工作区可见。
- 主流程通过：预备引用 + 预备 DATA → Data Lin 质控/统计草案/模型计划/模型拟合 → Writer handoff → Reviewer 映射。
- 导出来源通过：验证计划复制兜底可显示完整内容，Writer Methods / Results、Reviewer mapped response 和 checklist 均能保留对应来源内容。
- 高级模型分支通过：Cox 样例显示 `Cox proportional hazards model`、HR、PH assumption、Schoenfeld、statsmodels/PHReg 和外部验证提示；mixed-effects 样例显示 `Linear mixed-effects model`、cluster、random intercept、ICC、convergence、residual diagnostics 和外部验证提示。
- Writer / Reviewer 边界通过：Cox 与 mixed-effects 输出仍保留 exploratory / pending external validation 边界，没有写成已验证 SCI 结论。
- 构建和 smoke 通过：`npm.cmd run build`、`backend/.venv/Scripts/python.exe -m compileall app`、后端 app 内存 SQLite import smoke 均通过。
- 本轮未发现阻塞性问题；Codex in-app browser 不支持 download event，因此导出按钮以页面文件名提示、来源内容和复制兜底进行校验。

2026-06-26 Reviewer / Writer 返修链路增强与 UI 目视复核补充：

- 后端增强通过：Reviewer 导入生成的英文回复草稿会抽取具体 reviewer concern，并按统计/模型、数据隐私、放疗方法、引用、投稿声明、图表和语言主题生成更具体的 `manuscript_change`。
- 前端增强通过：`inferReviewerRevisionSections` 已补充 endpoint coding、QA failure、gamma、TPS、causal wording、exploratory、page/line/manuscript location 等关键词。
- Project B 临时 UI 复核通过：导入 1 条包含 QA failure、gamma pass rate、binary endpoint、causal wording 和 page/line/location 的样例后，Reviewer 卡片显示具体英文 concern、Page / Lines / Manuscript location 占位和主题化修改建议。
- Writer 联动通过：同一条样例按自动识别显示在 Methods / Results、Discussion 和 Cover Letter / Submission 的 Reviewer 修改提醒中，并保留类型/状态统计。
- 导出来源复核通过：`导出映射回复` 和 `导出写作清单` 按钮可点击，页面来源内容包含 Reviewer 1、具体 concern 和 Page 占位；当前浏览器仍不支持直接捕获 download event。
- 清理通过：Project B 临时 Reviewer 记录已删除，复查为空；本地 app 控制台无 error / warning。
- 验证命令通过：`PYTHONPATH=. .\.venv\Scripts\python.exe tests\test_reviewer_comment_responses.py`、`.\.venv\Scripts\python.exe -m compileall app`、`npm.cmd run build`、`git diff --check`。

服务级闭环曾验证：

- Writer version create/list/restore。
- Reviewer comment import/update。
- Data Lin advanced model plan。
- Data Lin linear regression model fit：
  - 正向 CSV 返回 `linear_regression`、8 个完整病例、R-squared 0.9977、4 个系数项。
  - 人工确认不完整时允许 exploratory fit，并在 warnings 中提示缺失确认项。
  - CSV 含疑似直接身份标识时阻止执行。
  - 最新审计日志返回 `raw_data_saved=false`。
- Data Lin logistic regression model fit：
  - 放疗样例推荐 `logistic_regression`。
  - `qa_result` 自动按 `Pass` vs `non-Pass` 编码。
  - 返回 odds ratio、95% CI、P 值和收敛/稀疏事件警示。
  - 浏览器 UI 已验收：生成模型计划后可运行推荐模型，并显示 `Binary logistic regression` / OR 输出。
- Data Lin Cox survival model fit：
  - 含 follow-up time 与 event/status 的 CSV 可推荐 `cox_ph`。
  - 优先走 statsmodels `PHReg`，返回 hazard ratio、95% CI、P 值、事件数、删失/ties/比例风险假设复核提示。
  - 前端会显示 `Cox proportional hazards model` / HR 输出、`advanced-cox-statsmodels-v1`，并可导出 `advanced-cox-model-fit.md`。
  - 本地 API 与浏览器验收通过：Cox fit report 返回 `diagnostic_handoff`，页面显示 Complete cases、Events、Censored records、Schoenfeld / PH assumption 诊断和 HR 交接材料。
- Data Lin mixed-effects model fit：
  - 含 repeated-measures 字段与 cluster 分组的 CSV 可推荐 `mixed_effects`。
  - 优先走 statsmodels `MixedLM` random-intercept 路径，返回 exploratory fixed-effect estimates、random intercept variance、residual variance、ICC、cluster 数和重复观测/随机效应结构复核提示。
  - 前端会显示 `Linear mixed-effects model` / cluster 输出、`advanced-mixed-effects-statsmodels-v1`，并可导出 `advanced-mixed-effects-fit.md`。
  - 本地 API 与浏览器验收通过：mixed-effects fit report 返回 `diagnostic_handoff`，页面显示 cluster 数、singleton clusters、median cluster size、ICC、singular fit / residual diagnostics 和 variance components 交接材料。

本轮验收发现并修复：

- 实际 SQLite `data_audit_logs.raw_data_saved` 列是 `VARCHAR(8)`，旧 ORM Boolean 映射会把字符串 `"0"` 读成 `true`。
- 已改为按字符串 `"0"/"1"` 写入，并在仓库层显式转换为布尔值，保证页面显示“未保存原始 CSV”与接口字段一致。

2026-06-24 导出/复制兜底修复：

- 最新提交：`39a1a48 Improve export and validation-plan copy fallback`，已推送到 `origin/main`。
- 前端已为关键 Markdown 导出复用统一下载 helper，覆盖高级模型结果、验证计划、Writer 正文/Methods-Results/版本快照、Reviewer 映射回复和返修写作清单。
- Data Lin `复制验证计划` 已增加只读文本框兜底；当浏览器剪贴板不可用时，页面会显示完整 `advanced-model-validation-plan.md` 内容，便于手动复制。
- 已通过 `npm run build`。
- 浏览器验收通过：加载预备 DATA、生成统计草案、生成高级模型计划后，`复制验证计划` 会显示兜底文本框；文本包含 `Advanced Model External Validation Plan`、`Binary logistic regression`、events per variable、calibration、ROC 和 separation 等核验项。
- 浏览器验收通过：`导出验证计划` 显示 `advanced-model-validation-plan.md` 下载提示，运行推荐模型后 `导出结果` 显示 `advanced-logistic-model-fit.md` 下载提示；前端控制台无应用错误。

2026-06-24 Mentor 真实放疗引用包收尾：

- 后端 `mentor_evidence_service` 新增 `curated_reference` 本地真实放疗候选文献，覆盖 MR-guided adaptive RT、FLASH、AI/QA、粒子治疗、影像组学、自动化计划、SRS/SBRT 和运动管理。
- 本地 provider 保留每条候选文献的 `curated_reference` 状态、PMID、DOI、PubMed 链接和 DOI 链接，不再强行覆盖为 `local_template`。
- 前端 Mentor 推荐依据卡片新增“人工核验缺口 / 基础元数据完整”提示，便于测试全文核对、用途标记和引用导出前的剩余工作。
- 前端 Mentor 推荐卡新增“最小数据字段 / 测试落地清单 / 写入追踪”，便于在生成 Protocol 草案前核对字段、真实数据边界、样例数据和统计复核边界。
- 后端函数验收通过：`mr_linac`、`ai_planning_qa`、`sbrt` 推荐卡返回 `curated_reference`，PMID / DOI 正常。
- 前端 `npm run build` 通过。

2026-06-24 Mentor / Protocol 本地接口验收补充：

- Mentor 推荐接口验收通过：`project-a` 测试载荷返回 3 张推荐卡，首条证据为 `curated_reference`，PMID `35946325`，DOI `10.1093/jrr/rrac048`。
- Mentor 文献复核保存/读取闭环通过：`reviewed`、全文核对和 Introduction 用途标记可通过项目复核接口读回；测试记录已清理。
- Mentor 推荐生成 Protocol 草案验收通过：先备份 Project A protocol，再生成推荐卡字段，确认研究问题、数据路径和统计路线保存成功，随后已恢复测试前方案。
- Project A protocol 已复核为正常中文 Unicode 状态，避免 PowerShell 控制台编码造成的显示误判。
- Vera Protocol 计划草案接口验收通过：可从当前方案生成 7 个阶段和 10 个任务；测试 draft 已删除，原 draft 数量恢复。
- Vera Protocol 方案草案接口验收通过：已有方案内容时返回现有方案，不覆盖 Project A。
- Data requirement 接口验收通过：当前 Project A 数据需求来自研究方案，可生成 22 个字段项。
- 前端 Protocol 顶部按钮已区分为“方案草案”和“计划草案”，避免手动测试时两个按钮都显示“草案”。

2026-06-24 主链路 API smoke 验收补充：

- Data Lin 放疗计划质量样例通过：`radiotherapy_plan_quality_sample.csv` 返回 20 行 / 18 列，隐私风险为 orange，统计草案生成 4 张图表。
- Data Lin 高级模型计划/拟合通过：
  - 放疗计划质量样例推荐并运行 `logistic_regression`，返回 `Binary logistic regression`、`advanced-logistic-v1`、20 个 complete cases 和 9 个系数项。
  - Cox 生存样例推荐并运行 `cox_ph`，返回 `Cox proportional hazards model`、`advanced-cox-statsmodels-v1`、16 个 complete cases、3 个系数项和 5 项诊断交接要求。
  - Mixed-effects 重复测量样例推荐并运行 `mixed_effects`，返回 `Linear mixed-effects model`、`advanced-mixed-effects-statsmodels-v1`、24 个 complete cases、7 个系数项和 5 项诊断交接要求。
- Writer Introduction 草稿保存、Writer 版本创建、版本恢复和原草稿恢复通过；测试版本已删除。
- Reviewer 复杂审稿信导入通过，测试文本拆分为 4 条意见；状态更新和章节归属保存通过；测试意见已删除。

2026-06-24 Mentor 95% 收口：

- 后端 `MentorRecommendationCard` 新增 `minimum_data_fields`、`readiness_checklist` 和 `protocol_trace`。
- MentorService 会按主题生成最小数据字段、真实数据边界提醒、首轮样例数据建议、统计复核边界和 Protocol 来源追踪。
- 前端推荐卡展示新增三块：最小数据字段、测试落地清单、写入追踪。
- 前端生成课题推荐或加载预备引用后会自动滚到推荐报告，并在报告顶部提示每张推荐卡内的“Mentor 落地验收”包含上述三块。
- Mentor brief 导出包含上述三块内容，生成方案草案预览也显示 Mentor 来源追踪。
- 后端函数验收通过：首张推荐卡返回 10 个最小字段、4 条落地清单、5 条写入追踪，首条证据仍为 `curated_reference`。

2026-06-24 Mentor → Protocol 主线补强：

- 前端 `mentorCardToProtocolUpdate` 会把推荐卡的最小数据字段写入 Protocol `data_requirements`，并补充数据字典草案、来源系统、导出格式和真实数据边界；IRB / 脱敏 / TPS / QA 等只进入正式研究前人工确认项，不作为 Project A / B 预设样例输入。
- 前端 synthesis 会把推荐卡合成为完整 Vera Protocol 草案：研究假设、PICO/PECO、主要/次要终点、纳排标准、数据路径、实验流程、统计边界、正式研究前确认和 Rhea 里程碑。
- 前端新增规则版 `buildMentorDiscussionBrief`，把当前项目 Mentor 自由对话、表单和推荐报告转成讨论依据，写入 Vera 草案的 hypothesis、study_type、data_requirements、experiment_workflow、institutional_field_mapping 和 rhea_milestones。
- 前端新增 `getProjectChatMessages` 加载 Mentor 历史消息，并与当前页面新消息去重合并，避免刷新后 discussion brief 丢失。
- 推荐卡的测试落地清单和 Mentor 写入追踪会进入 Protocol `experiment_workflow`，并同步到 `rhea_milestones` 的验收/追踪节点。
- Protocol 质量检查新增四项：最小数据字段是否可追踪、正式研究前确认项是否说明、数据字典与导出路径是否明确、放疗计划系统追踪边界是否明确。
- 后端 Vera 回复抽取器已支持 `institutional_field_mapping`，未配置 LLM 的 Vera 模拟回复也会输出可抽取的结构化草案。
- 方案-数据一致性检查新增“Protocol 最小字段写入”，显示 Data Lin 当前可从 Protocol 读取的必需字段数量和落地信号命中数。
- Data Lin 后端 `_split_requirement_text` 已支持项目符号字段，忽略“最小数据字段”等纯标题，避免把标题误当字段。
- 验收结果：`npm.cmd run build` 通过；字段拆分小样本返回 `匿名病例或计划 ID`、`治疗部位`、`TPS/计划系统版本` 和数据字典要求；浏览器中 3 张 Mentor 推荐卡均显示三块落地内容，预览方案中可见最小数据字段、数据字典草案、真实数据边界和 Mentor 来源追踪，未执行确认生成。

2026-06-24 Vera Protocol 正式研究前确认项：

- 前端新增 `buildProtocolRealWorldReadiness`，从 Protocol 文本、Data Lin 字段需求和 CSV 质控状态生成正式研究前确认项。
- 清单包含 5 张卡：候选字段字典、伦理与数据许可确认、计划系统与 DICOM 确认、CSV 字段映射、统计复核边界。
- “导出一致性”Markdown 已包含正式研究前确认清单，便于线下逐项验收。
- 验收结果：`npm.cmd run build` 通过；浏览器在 `http://127.0.0.1:3000/` 可见 5 张清单卡，当前无横向溢出。

2026-06-24 Data Lin 字段需求分类展示：

- 前端新增 Data Requirement 分类逻辑，按最小字段、伦理/脱敏、数据字典、TPS/DICOM、终点/统计和其他归类。
- Data Lin 字段需求区顶部显示分类统计条；每张字段卡显示类别标签、必需/建议状态和分类验收提示。
- 验收结果：`npm.cmd run build` 通过；浏览器 Data Lin 页面可见分类统计，字段卡显示类别标签，当前无横向溢出。

2026-06-24 Writer 数据与方案交接摘要：

- 前端新增 `buildWriterDataHandoffSummary`，从 Protocol 正式研究前确认项、方案-数据一致性检查、Data Lin 字段分类和 CSV 质控状态生成写作前交接摘要。
- Alex Writer 的 Methods / Results 区显示 4 张交接卡：Protocol 正式研究前确认、Data Lin 字段分类、CSV 覆盖与隐私、Methods / Results 写作边界。
- `methods-results-draft.md` 导出新增 Writer 数据与方案交接摘要；英文正文生成器本身未自动混入未确认风险，仍由摘要层提示人工核对。
- 验收结果：`npm.cmd run build` 通过；源码位置已确认。浏览器插件本轮拦截 localhost 打开，需在本机浏览器手动刷新 `http://127.0.0.1:3000/` 复核 UI。

2026-06-25 Mentor 自定义方向与项目聊天记忆：

- 后端 `MentorQuestionnaireRequest` 新增 `discussion_summary`，前端 Mentor 表单提交时会带入当前项目 Mentor discussion brief。
- `MentorService` 已从固定 topic 卡片生成改为自定义方向生成：
  - 方向标题、研究问题、数据路径、方法路线、统计路线和最小字段由资源与对话摘要生成。
  - topic 库只作为辅助参考标签，用于证据、趋势和期刊入口。
  - MR 自适应方向只有在设备/系统/数据里出现 MR-Linac、Unity、MRIdian、ViewRay 等真实平台信号时才会生成。
- 针对非 MR 资源的接口烟测通过：`TOMO / TrueBeam + Eclipse / Accuray + DICOM RTDose / RTStruct / RTPlan` 返回计划剂量学质量、RTDose/RTStruct/RTPlan 一致性、Eclipse/Accuray 字段字典验证三类方向，没有返回 MR / 在线自适应方向。
- 聊天系统支持项目级共享记忆和按项目/智能体过滤历史；前端新增“当前聊天 / 历史聊天 / 清空”，清空范围限定为当前项目 + 当前智能体。
- Project 卡片展示已改为读取当前保存的 Vera Protocol / 项目状态，避免长期显示 Project A 旧预设。
- 新增 `docs/project-a-real-data-intake-template.md`，记录真实研究前 IRB、数据授权、脱敏、字段字典、TPS/DICOM/QA 和统计定稿确认项；该模板不是 Project A / B 预设样例输入。
- 验收结果：`npm.cmd run build` 通过，`.venv\Scripts\python.exe -m compileall app` 通过，`git diff --check` 通过，后端 `/health` 正常；最后确认 8000 服务 PID 为 `32324`。

## 手动验收清单

建议在浏览器中按以下顺序手动验收：

1. 打开 `http://127.0.0.1:3000/`。
2. 确认 Project A / Project B 横向排列。
3. 确认 5 个智能体横向排列。
4. 使用“主流程快捷操作”：
   - 加载预备引用
   - 加载预备 DATA
   - 一键联调到 Writer
   - 高级模型计划
   - 保存 Writer 版本
   - 导入/查看审稿意见映射
5. 在 Mentor 中检查：
   - 选择 MR-guided adaptive RT、AI / Planning / QA、SRS / SBRT 等任意兴趣方向并生成课题推荐。
   - 生成后应自动滚动到推荐报告，并显示“已生成 X 张推荐卡”的提示条。
   - 每张推荐卡应显示最小数据字段、测试落地清单和写入追踪。
   - 推荐依据中显示“本地核准候选文献”和 PMID / DOI / PubMed / DOI 链接。
   - 人工核验缺口随“全文已核对”、Introduction / Discussion 用途标记变化。
   - 将 1-2 条候选文献标记为“确认可用”，确认候选引用清单出现。
   - 导出 `references-vancouver.md`，确认包含去重数量、Vancouver 候选引用和人工核验清单。
   - 导出 Mentor brief，确认包含最小数据字段、测试落地清单、写入追踪和候选证据。
   - 点击“交给 Alex Writer”，确认 Writer 侧能看到候选引用并可插入 / 绑定到 Introduction 字段。
   - 点击“预览方案”并确认生成方案草案，检查 Protocol 研究问题、数据需求、统计路线、Rhea 里程碑和 Mentor 来源追踪。
6. 在 Vera Protocol 中检查：
   - 顶部按钮显示“方案草案”“计划草案”“保存”，用途清晰可区分。
   - 点击“方案草案”时，已有方案不应被空草案覆盖。
   - 点击“计划草案”后，计划草案列表应出现 7 阶段 / 10 任务结构。
   - 检查方案质量面板包含“最小数据字段是否可追踪”“正式研究前确认项是否说明”“数据字典与导出路径是否明确”“放疗计划系统追踪边界”。
   - 检查方案-数据一致性面板包含“Protocol 最小字段写入”。
   - 检查“正式研究前确认项”显示 5 张卡，并确认状态随 Protocol 和 CSV 质控结果变化。
   - 检查方案质量、方案-数据一致性和版本快照三个面板，并分别导出 Markdown。
   - 检查 Data Lin 数据需求卡片显示“来自研究方案”和当前字段需求数量。
7. 在 Data Lin 中检查：
   - 字段需求区顶部显示分类统计条。
   - 每张字段卡显示“最小字段 / 伦理/脱敏 / 数据字典 / TPS/DICOM / 终点/统计”等类别标签和必需/建议状态。
   - 自主分析计划
   - 质控报告
   - 统计报告
   - 高级模型计划
   - 运行线性回归
   - 导出 `advanced-linear-model-fit.md`
   - 对含生存字段的 CSV 运行 Cox 模型并导出 `advanced-cox-model-fit.md`
   - 对含重复测量字段的 CSV 运行 mixed-effects 模型并导出 `advanced-mixed-effects-fit.md`
   - 查看“统计验证计划”并导出 `advanced-model-validation-plan.md`
   - 正式检验确认区
8. 在 Alex Writer 中检查：
   - Methods / Results 草稿上方显示“数据与方案交接摘要”。
   - 交接摘要包含 Protocol 正式研究前确认、Data Lin 字段分类、CSV 覆盖与隐私、Methods / Results 写作边界。
   - 导出 `methods-results-draft.md`，确认 Markdown 中包含 Writer 数据与方案交接摘要。
   - 英文 Methods / Results
   - Discussion
   - Abstract
   - Cover Letter
   - 目标期刊规则校验
   - 后端版本库保存、恢复 Introduction、恢复全文草稿、逐字段编辑历史恢复内容、版本 diff、历史章节复制和清除恢复
   - Reviewer 修改提醒
9. 在 Reviewer 中检查：
   - 投稿前审稿清单
   - AI 写作痕迹与模板化风险顶部卡片
   - 目标期刊对照验收卡片
   - 目标期刊专属 Reviewer 检查项
   - Deep review comments
   - Response to Reviewers
   - 真实审稿意见导入
   - 填入模拟 decision letter 样例，确认不会自动导入
   - 复杂 decision letter 是否拆成多条独立意见
   - 逐条英文回复草稿
   - 返修清单章节归属人工修正
   - 返修写作清单
   - 规则型 `Response to Reviewers` 草稿不再重复旧模板句式，并能按统计/数据/方法/伦理/图表/语言主题给出更具体回复骨架。
   - Writer 面板的 Reviewer 修改提醒按章节显示类型分布和状态分布。
10. 逐项测试主要导出按钮。

## 当前限制

- 当前预备 CSV 包含放疗计划质量脱敏模拟样例、MIMIC-IV EHR demo、Cox 生存分析脱敏模拟样例和 mixed-effects 重复测量脱敏模拟样例；它们分别用于放疗字段、公开医学 EHR、HR 输出和 cluster 输出流程联调，都不代表正式课题结论。
- 高级模型执行第一版已支持 linear regression、logistic regression、Cox proportional hazards model 和 mixed-effects model，并可导出外部验证计划。
- Linear/logistic/Cox/mixed-effects 输出是探索性拟合结果，仍需要人工统计复核，不应直接作为最终 SCI 结论。
- Cox 当前优先使用 statsmodels `PHReg`，失败时回退内部 partial-likelihood 近似；正式报告前仍需要用 lifelines、R survival 或独立 statsmodels/R 流程复核 PH assumption、Schoenfeld residuals 和事件/删失定义。
- Mixed-effects 当前优先使用 statsmodels `MixedLM` random-intercept 路径，失败时回退 clustered linear approximation；正式报告前仍需要用 R lme4/nlme、SAS PROC MIXED 或独立 statsmodels 流程复核随机效应结构、收敛、残差诊断和 ICC。
- 当前系统已自动调用 statsmodels 作为 Cox/Mixed 的第一生产化拟合路径，但 lifelines、R survival、R lme4/nlme 和 SAS PROC MIXED 仍通过外部验证清单交接，尚未被系统自动调用。
- Writer 版本库当前恢复 Introduction；派生章节可作为历史恢复内容优先显示、逐字段编辑、预览、diff、复制、导出，并可纳入新的版本快照，但不会直接写回后端全文字段。
- Reviewer 真实意见拆分已支持 Editor / Reviewer 分块和多种编号条目，但仍是规则型，复杂 decision letter 仍需人工校正。
- Reviewer 到 Writer 的章节映射支持人工修正和持久化保存，但仍需人工对照原始 decision letter 最终确认。
- 当前 Author Guidelines 校验支持普通 HTML URL 抓取和手动粘贴；PDF、登录、强 JS 或反爬页面仍需手动粘贴，正式投稿仍需在投稿系统中最终核对。
- 目标期刊专属 Reviewer 检查是规则型本地维度，不能替代目标期刊官网、投稿系统和编辑部要求的最终人工核对。
- Reviewer 是规则型自查，不替代真实同行评审。

## 本地启动方式

后端：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

## 下一步建议

1. Stage A 验收后收口：
   - 2026-06-26 已完成预备引用、预备 DATA、Data Lin 高级模型、Writer handoff、Reviewer 映射和关键导出来源的一轮完整验收。
   - Reviewer / Writer 返修链路增强和 UI 目视复核已完成；下一步优先做提交/同步前 diff 复核。
   - 保留高级模型外部验证、人工作业边界和真实数据接入前确认清单。
2. 下一阶段优先级：
   - Mentor/Vera 自主方案生成：从研究方向讨论形成 protocol 草案和实验方案草案
   - Mentor 确认生成 Protocol 草案后，逐项测试 Data Lin 是否读取最小字段、数据字典草案和真实数据边界
   - 真实数据接入前，再核对真实字段字典、数据许可、伦理/脱敏和计划系统追踪
   - Writer 写作风格学习和目标期刊英文表达偏好
   - Reviewer / Writer 返修链路后续增强：继续用更多真实 decision letter 评估语气自然度、段落级定位和内容类型识别
   - Author Guidelines PDF / 强 JS 页面处理
3. 稳定化原则：
   - 页面和交互继续保持中文
   - 论文正文、投稿材料、Response to Reviewers 和导出稿件继续保持英文
   - 高级统计和 Reviewer 输出继续标注人工核验边界
4. Git 节奏：
   - 小功能本地阶段性提交
   - 一组完整大功能或阶段复盘后再推送 GitHub


2026-06-27 Project A/B 双监控推进补充：

- 前端 Project 卡片已补齐双监控摘要：每个 Project 都显示“流程监控”和“质量/边界监控”，不再只依赖选中项目侧栏里的单一 Rhea 监控中心。
- 流程监控基于当前项目任务计算受阻、逾期和最近未完成任务；质量/边界监控基于项目风险级别，并明确提示 Project A / B 仍是样例工作区，真实 IRB、数据、脱敏和统计边界仍需人工确认。
- Project A / Project B 都走同一套显示逻辑，符合“全程管理”要求；该改动不改变后端数据模型、不引入真实 protocol 来源，也不把 A/B 预设内容当作真实研究方案。
- 验证：前端 npm run build 通过。

2026-06-27 Project B 样例计划重排补充：

- 新增本地维护脚本 `backend/scripts/reschedule_project_b_sample_plan.py`，用于将 Project B 预设样例任务从历史逾期节点重排到当前日期之后；该脚本只处理 Project B 样例工作区，不改变 Rhea 逾期判断规则。
- 已运行脚本并更新本地 SQLite：Project B `b-task-1` 截止日改为 `2026-07-04`、`b-task-2` 截止日改为 `2026-07-11`，Project B 风险状态变为 `green`，下一节点为 `2026-07-04`。
- Rhea 提醒复核通过：Project B `active_count=0`、`overdue_count=0`、`blocked_count=0`；这只是样例计划重排，不代表真实病例来源、TPS 版本、数据授权、IRB、脱敏或统计复核已经完成。

2026-06-27 Project B 卡片 Protocol 覆盖边界修复：

- 修复 Project B 被选中后，项目卡片标题、主题和下一节点优先读取旧 Vera Protocol 草案的问题。
- Project B 仍按当前预设样例计划展示 `project.current_phase`、`project.next_milestone` 和 `project.next_due_date`，避免把旧草案里程碑误当成当前执行方案。
- 该修复只收紧前端卡片展示边界，不删除旧 Protocol、不改变后端数据模型、不代表真实 IRB、数据授权、脱敏、TPS/DICOM/QA 或统计复核已经完成。
