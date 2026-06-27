# 当前模块进度表

更新日期：2026-06-27

## 总体判断

当前项目已经推进到“可带公开医学/放疗样例数据跑通论文写作、后端版本归档、真实审稿意见映射、目标期刊规则校验、Reviewer 收尾验收、第一版高级统计模型拟合、statsmodels Cox/MixedLM 生产化优先路径、外部验证计划导出、Mentor → Vera Protocol 草案生成、Vera 正式研究前确认项、Data Lin 字段分类展示、Writer 数据与方案交接摘要、项目级聊天记忆共享、按项目/智能体隔离聊天历史、Mentor 自定义研究方向优先生成”的阶段。整体完成度约 **99.2%**；如果只看 5 个核心智能体能力，平均完成度约 **97.4%**。

重要边界：Project A / B 是工作区和预设样例，不代表真实机构 protocol；Mentor 现在优先根据设备、计划系统、可用数据和 Mentor 对话摘要生成自定义研究方向，预设 topic 只作为证据检索、趋势对照和目标期刊入口的辅助标签。真实 IRB、数据授权、脱敏、TPS/DICOM/QA 和字段字典只作为真实数据接入或投稿前的人工确认项。

2026-06-26 Stage A 验收补充：已用预备引用、预备 DATA、Data Lin 高级模型、Writer 交接、Reviewer 映射和关键导出路径跑完一轮真实样例 UI 验收；`npm.cmd run build`、后端 `compileall app` 和内存 SQLite import smoke 均通过，当前未发现阻塞性问题。

2026-06-26 Reviewer / Writer 返修链路增强补充：已完成英文回复草稿 concern 抽取、主题化 manuscript change、章节自动识别关键词扩展和 Project B 临时 UI 目视复核；临时 Reviewer 记录已清理，未留下测试数据。

2026-06-28 GitHub 同步收口补充：`main` 分支已推送到 `origin/main` 并完成同步；本批覆盖 Vera 剂量学方向 synthesis 边界修复、Rhea Plan v2 应用记录、Project A/B 卡片双监控、Project B 样例计划重排、Project B 卡片 Protocol 覆盖边界修复和同步前进度文档收口。验证通过：`npm run build`、浏览器 Project B 选中态 UI 复核、控制台 error/warn 复核、`git diff --check origin/main..HEAD`。本轮仍不改变总体完成度百分比，Project A / B 继续只作为预设样例工作区和流程演示容器，不代表真实机构 protocol 或真实数据准备完成。

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
| Prof. RadOnc Mentor | 98% | 可生成自定义研究方向候选、加载预备真实引用、复核候选引用、导出引用清单，并将候选方向生成 Vera Protocol 草案；已内置按主题分布的真实放疗候选文献包，覆盖 MR-guided adaptive RT、FLASH、AI/QA、粒子治疗、影像组学、自动化计划、SRS/SBRT 和运动管理；现在先根据用户资源和 Mentor 对话摘要出题，预设 topic 只作为辅助参考标签；推荐卡已补最小数据字段、测试落地清单和 Protocol 来源追踪，预览方案会把这些内容带入 Protocol 数据需求、PICO/PECO、实验流程、统计路线和 Rhea 里程碑 |
| Dr. Vera Protocol | 92% | 可编辑/保存研究方案，生成方案草案和执行计划草案，完成方案质量检查、方案-数据一致性检查、方案版本快照与导出；Mentor 自定义方向卡现在会合成为完整 Vera 草案，覆盖研究假设、PICO/PECO、主要/次要终点、纳排标准、数据路径、实验流程、统计边界、正式研究前确认项和 Rhea 里程碑；后端 Vera 回复抽取已支持“正式研究前确认”；下一阶段重点是让 Vera 草案生成后进一步驱动 Rhea 计划和 Data Lin 字段预检查 |
| Dr. Data Lin | 99.3% | 可上传 CSV、选择预备 DATA、做质控/隐私检查/统计草案/图表/审计、一键联调 Writer，生成自主分析计划、高级模型计划和高级模型外部验证计划；当前可执行 exploratory linear/logistic，并优先使用 statsmodels PHReg / MixedLM 执行 Cox 与 mixed-effects，失败时回退内部近似路径；Cox / mixed-effects 已补充结构化诊断交接字段和前端外部复核交接展示；字段需求区已按最小字段、伦理/脱敏、数据字典、TPS/DICOM、终点/统计分类展示，便于逐项测试 Protocol 草案生成结果 |
| Alex Writer | 99.1% | 可生成英文 Introduction、Methods / Results、Discussion、Abstract、Cover Letter、投稿包检查清单、目标期刊模板和 Author Guidelines URL 抓取/本地规则校验，并支持放疗计划质量字段解读、高级模型结果来源、pending external validation 英文边界提示、Protocol/Data Lin 数据与方案交接摘要、后端版本归档、恢复 Introduction、版本差异查看、历史章节复制、全文恢复逐字段编辑和 Reviewer 修改提醒 |
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

### 2. Mentor 真实放疗引用与证据链

- Mentor 本地证据库新增真实放疗候选文献包，默认不依赖外网即可用于 UI 验收。
- 覆盖主题：
  - MR-guided adaptive radiotherapy：online MR-guided adaptive RT practical guidelines、real-time adaptive MR-guided RT 技术挑战。
  - FLASH：超高剂量率 FLASH 转化研究经典文献。
  - AI / Planning / QA：AAPM TG-218、VMAT plan complexity 与 measurement-based QA 研究。
  - Particle therapy：proton therapy range uncertainties 与 Monte Carlo 综述。
  - Radiomics：Radiomics 方法学经典论文。
  - Automation / knowledge-based planning：automated 4π planning 和 knowledge-based planning model evaluation。
  - SRS / SBRT：AAPM TG-101。
  - Motion management：AAPM TG-76。
- 每条真实候选文献保留 PMID、DOI、PubMed 链接、DOI 链接、候选 citation 和 Vancouver 候选引用。
- 前端 Mentor 推荐依据卡片会显示“人工核验缺口”，包括全文核对、PMID、DOI、Vancouver 候选引用、作者、期刊、年份、卷期页码和用途标记。
- Mentor 推荐卡新增最小数据字段、测试落地清单和 Protocol 来源追踪，覆盖数据字段、真实数据边界、首轮样例数据和统计复核边界。
- 生成课题推荐或加载预备引用后，前端会自动滚动到 Mentor 推荐报告，并在报告顶部提示每张推荐卡内的“Mentor 落地验收”位置。
- 标记“确认可用”后，候选引用清单、Vancouver 导出和 Alex Writer 引用质控可以直接读取这些真实放疗候选文献。
- 本地接口验收已覆盖推荐生成、文献复核保存/读取、推荐生成 Protocol 草案、Project A protocol 恢复和测试复核记录清理。
- 仍保留原有本地检索式模板，便于后续扩展 PubMed/Crossref 自动检索。

Mentor 当前完成标准：

- 推荐生成后每张卡必须同时显示研究问题、数据路径、统计路线、风险提示、最小数据字段、落地清单、写入追踪和候选证据。
- 候选证据必须能显示 PMID / DOI / PubMed / DOI 链接、候选 citation、Vancouver 候选引用和人工核验缺口。
- 用户能将证据标记为确认可用、全文已核对、Introduction / Discussion 用途，并在候选引用清单中看到同步结果。
- 用户能导出 Mentor brief 与 Vancouver 引用清单，并把确认可用引用交给 Alex Writer。
- 用户能在生成方案草案预览中看到 Mentor 来源追踪，然后确认生成 Vera Protocol 草案。

### 2.1 Vera Protocol 本地验收补充

- Protocol 顶部按钮已区分为“方案草案”和“计划草案”，便于手动测试时区分生成方案与生成执行计划。
- Mentor 推荐卡生成 Protocol 草案预览时，数据需求会包含最小数据字段、数据字典草案、来源系统、导出格式和真实数据边界；IRB / 脱敏 / TPS / QA 等只作为正式研究前人工确认项。
- Protocol 方案质量检查新增四个落地项：最小数据字段是否可追踪、正式研究前确认项是否说明、数据字典与导出路径是否明确、放疗计划系统追踪边界是否明确。
- 方案-数据一致性检查新增“Protocol 最小字段写入”，用于显示 Data Lin 从 Protocol 读取到的必需字段数量和落地信号命中数。
- Vera Protocol 页面新增“正式研究前确认项”，把候选字段字典、伦理与数据许可确认、计划系统与 DICOM 确认、CSV 字段映射和统计复核边界拆成 5 张卡片；导出一致性报告也包含该清单。
- `protocol/draft` 已验收：Project A 已有方案内容时返回现有方案，不覆盖当前字段。
- `plan/drafts/from-protocol` 已验收：可从当前方案生成 7 个阶段和 10 个任务；测试 draft 已清理。
- `data/requirements` 已验收：当前 Project A 数据需求来自研究方案，可生成 22 个字段需求项。

### 2.2 本轮同步批次

- 已上传 GitHub 的上一批提交：`0f4ee78 Complete Mentor protocol handoff`，覆盖 Mentor 真实证据包、推荐卡三块落地内容、Protocol 草案交接和 Protocol 质量检查补强。
- 本批本地开发新增 Vera Protocol 正式研究前确认项，Data Lin 字段需求分类展示，以及 Writer 数据与方案交接摘要。
- 本批继续推进 Mentor/Vera 自主方案生成：前端推荐卡合成为完整 Vera protocol 草案，预览显示研究假设、PICO/PECO、主要终点、实验方案、统计路线、正式研究前确认和 Rhea 里程碑；后端 Vera 抽取器新增正式研究前确认字段。
- 本批新增规则版 Mentor discussion brief：前端会从当前项目的 Mentor 对话、Mentor 表单和推荐报告中提取用户倾向、限制、资源、数据线索和待确认问题，并写入 Vera 草案预览、实验流程和 Rhea 里程碑。
- 本批新增 Mentor 讨论历史恢复：后端提供项目级 chat history 读取接口，前端刷新或切换项目后会加载最近 Mentor 历史消息，discussion brief 不再只依赖当前页面内存。
- 本批新增导出覆盖：
  - `protocol-data-consistency-check.md` 包含正式研究前确认清单。
  - `methods-results-draft.md` 包含 Writer 数据与方案交接摘要。
- 本批验证：`npm.cmd run build` 通过，`git diff --check` 通过；浏览器插件对 localhost 有拦截，需在本机浏览器手动刷新 `http://127.0.0.1:3000/` 做最终 UI 目视复核。

### 2.3 2026-06-25 Mentor 自定义方向与项目级聊天记忆

- Project A / B 明确降级为工作区容器和演示样例，不再被当作真实 protocol 来源。
- Mentor 推荐接口新增 `discussion_summary` 入参，前端会把当前项目 Mentor 对话摘要带入方向生成。
- Mentor 生成逻辑从“固定 topic 推荐卡”切换为“自定义研究方向优先”：
  - 标题、研究问题、数据路径、方法路线和最小字段优先由设备、计划系统、可用数据和对话摘要生成。
  - 预设 topic 只作为辅助参考标签，用于证据检索、趋势对照和目标期刊入口。
  - 若资源中没有真实 MR-Linac / Unity / MRIdian / ViewRay 等平台信号，即使对话中提到“不要套用 MR 自适应预设”，也不会误生成 MR 自适应方向。
- 针对 `TOMO / TrueBeam + Eclipse / Accuray + DICOM RTDose / RTStruct / RTPlan` 的烟测结果，返回 3 个候选方向：
  - `TOMO / TrueBeam 计划剂量学质量与 OAR 约束达成度评估`
  - `基于 RTDose / RTStruct / RTPlan 的计划复杂度与剂量指标一致性研究`
  - `Eclipse / Accuray 计划导出字段完整性与可复现数据字典验证`
- 聊天系统新增项目级共享记忆：
  - 后端支持读取项目聊天历史，并可按 `agent_id` 过滤。
  - 前端会把当前项目全局对话摘要作为上下文传给后续智能体，便于 Mentor、Vera、Data Lin、Writer、Reviewer 共享项目背景。
  - UI 增加“当前聊天 / 历史聊天 / 清空”视图；历史聊天只显示当前项目 + 当前智能体记录，共享记忆不直接混在历史聊天里展示。
  - 清空聊天只清除当前项目当前智能体记录，不影响其他项目或其他智能体。
- Project 卡片展示已改为读取当前保存的 Vera Protocol / 项目计划状态，避免左侧卡片长期停留在 Project A 旧预设标题和阶段。
- 新增 `docs/project-a-real-data-intake-template.md`，作为真实研究前 IRB、数据授权、脱敏、字段字典、TPS/DICOM/QA 和统计定稿确认模板；该模板只在选定真实研究后使用，不是 Project A 的预设必填项。
- 本批验证：
  - `npm.cmd run build` 通过。
  - `.venv\Scripts\python.exe -m compileall app` 通过。
  - `git diff --check` 通过。
  - 后端 `/health` 正常；本地 8000 服务最后确认 PID 为 `32324`。
  - Mentor 推荐接口烟测确认非 MR 资源不会再返回 MR / 在线自适应候选方向。

### 3. 预备 DATA 联调包

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
- 本地 API smoke 已覆盖放疗计划质量样例、Cox 生存样例和 mixed-effects 重复测量样例的质控、统计草案、高级模型计划和拟合接口。

### 4. Dr. Data Lin

- CSV 上传与质控。
- 脱敏与隐私检查。
- 数据需求字段覆盖检查。
  - 字段需求区显示分类统计：最小字段、伦理/脱敏、数据字典、TPS/DICOM、终点/统计和其他。
  - 每个字段需求卡显示类别标签、必需/建议状态和分类验收提示，便于核对 Protocol 写入后的最小字段链路。
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
- 2026-06-24 本地 API smoke 结果：Logistic 返回 20 个 complete cases / 9 个系数项；Cox 返回 `advanced-cox-statsmodels-v1` / 16 个 complete cases / 5 项诊断交接要求；mixed-effects 返回 `advanced-mixed-effects-statsmodels-v1` / 24 个 complete cases / 5 项诊断交接要求。

当前仍未完成：

- Cox 和 mixed-effects 已接入 statsmodels 优先拟合路径，但正式 SCI 报告前仍需要独立统计复核，包括 PH assumption、Schoenfeld residuals、random-effects 结构、收敛、残差诊断和样本量限制。
- lifelines、R survival、R lme4/nlme、SAS PROC MIXED 等外部软件尚未被系统自动调用；当前仍通过 `advanced-model-validation-plan.md` 提供交接清单。
- 真实放疗专科数据接入和数据许可核对。

### 5. Alex Writer

- 英文 Introduction 草稿可编辑和保存。
- 候选引用可插入背景段、研究空白段和目的段。
- 字段级引用映射和引用质控。
- Methods / Results 草稿和导出 `methods-results-draft.md`。
  - Writer Methods / Results 区新增“数据与方案交接摘要”，读取 Protocol 正式研究前确认状态、Data Lin 字段分类、CSV 覆盖与隐私状态、方案-数据一致性动作。
  - `methods-results-draft.md` 导出新增 Writer 数据与方案交接摘要，避免写作阶段丢失字段字典、伦理/脱敏、TPS/DICOM 或统计复核风险。
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
- 本地 API smoke 已覆盖 Introduction 草稿保存、Writer 版本创建/恢复/清理和原草稿恢复。

当前仍未完成：

- 目标期刊官网规则自动抓取仍为 HTML 第一版；PDF、登录、强 JS 或反爬页面仍需手动粘贴。
- 写作风格学习。

### 6. Rev. Dr. Helena Skov

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
- 本地 API smoke 已覆盖复杂审稿信导入、4 条意见拆分、状态更新、章节归属保存和测试意见清理。

当前仍未完成：

- Reviewer 已完成一轮真实样例 UI 验收和 Reviewer / Writer 返修链路增强，后续以更多真实 decision letter 样例复核和小问题修正为主。
- Response to Reviewers 默认回复已完成第一轮主题化和具体 concern 抽取增强；后续继续用更多真实审稿信评估语气自然度和逐条回应细节。
- 真实审稿意见仍是规则型拆分和章节映射；本轮已增强统计、放疗方法、因果化、page/line/location 等关键词，后续继续增强段落级定位和内容类型识别。

## 当前优先级建议

1. Stage A 验收后收口：
   - 2026-06-26 已使用预备引用、预备 DATA、模拟 decision letter 和 Reviewer 映射路径跑完整链路。
   - 已确认 Data Lin 高级模型、Writer Methods / Results 交接、Reviewer mapped response / checklist 和关键 Markdown 导出来源可用。
   - 2026-06-26 Reviewer / Writer 返修链路增强已完成：后端单测 7 项通过，`compileall app`、`npm.cmd run build` 和 UI 目视复核通过。
   - 2026-06-28 已完成 GitHub 同步收口：本批本地提交已推送到 `origin/main`，文件范围集中，Project A/B 样例边界文案未越界。
   - 下一步进入新一轮本地小功能推进；后续仍按“小功能本地提交、阶段复盘后再推送 GitHub”的节奏执行。
   - 2026-06-24 已完成导出/复制兜底修复验收：高级模型验证计划在剪贴板不可用时会显示只读文本框，关键 Markdown 导出会显示文件名提示。
2. Data Lin 下一阶段：
   - 在已完成 statsmodels PHReg / MixedLM 诊断交接基础上，下一步优先考虑独立统计环境复核、校准/交叉验证和真实数据前统计定稿清单。
3. Mentor / Vera 下一阶段：
   - Vera 剂量学方向 synthesis 已修复否定边界中的 adaptive / 自适应关键词误触发；后续继续观察更多真实候选输入下的 PICO/PECO、终点和 Rhea 里程碑稳定性。
   - 保持 Project A / B 作为工作区样例，不再要求预设项目自带真实 IRB、数据授权、TPS/DICOM/QA 或字段字典。
4. Writer 下一阶段：
   - 写作风格学习与目标期刊英文表达偏好。
   - Response to Reviewers 语气润色：降低模板感，让回复更像真实作者逐条回应。
   - 更稳定的 PDF / 强 JS Author Guidelines 处理方案。
5. 真实数据前确认：
   - 当某个 Mentor/Vera 方案被用户选定后，再建立真实机构字段命名、正式数据字典、字段映射和数据许可核对清单。
   - 如研究需要真实计划数据，再用真实 TPS 导出路径核对计划系统版本、剂量计算算法、gamma criteria、结构命名规则和 DICOM RTDose / RTStruct / RTPlan 字段。
   - 将研究假设、PECO/PICO 与真实数据许可和字段字典在正式研究前绑定。

## 下一阶段路线图

### 阶段 A：验收与稳定化

- 2026-06-26 已完成一轮完整 UI 验收清单：预备引用、预备 DATA、Data Lin 高级模型、Writer 交接、Reviewer 映射和关键导出来源均已覆盖。
- 2026-06-26 已完成 Reviewer / Writer 返修链路增强与 UI 目视复核：Project B 临时导入样例可生成具体英文 concern、主题化修改建议、自动章节归属和 Writer 修改提醒；临时记录已清理。
- 本轮未发现阻塞性问题；后续只修复真实样例中暴露的小问题。
- 已完成导出/复制兜底小修复：验证计划复制失败时提供页面内手动复制文本框，Data Lin / Writer / Reviewer 关键导出路径统一下载 helper。
- 当前本地开发节奏保持为先完成一个完整功能模块再考虑上传；Reviewer / Writer 返修链路增强模块已完成第一轮实现、自动化验证和 UI 目视复核；2026-06-28 本批提交已推送到 `origin/main`，后续进入下一轮本地小功能推进。
- 确认页面中文、论文正文/投稿材料英文的规则在所有导出中稳定执行。
- 收集真实审稿意见样例，评估 Response to Reviewers 默认回复的自然度和具体性。

### 阶段 B：Mentor/Vera 自主方案生成

- 从 Mentor 讨论内容自动形成 protocol 草案和实验方案草案，而不是依赖 Project A 的预设字段。
- 当前已修复剂量学计划质量方向被 MR/adaptive 否定边界误触发的问题；继续保持 Project A/B 样例来源隔离。
- 将研究方向、候选引用、最小字段、统计路线、实验流程和 Rhea 里程碑串成一条可编辑链路。

### 阶段 C：真实数据接入前确认

- 从模拟放疗计划质量 DATA 过渡到可授权的真实脱敏样例。
- 完成字段字典、缺失值策略、隐私筛查、审计记录和数据许可核对。

### 阶段 D：高级统计扩展

- Cox survival analysis 和 mixed-effects model 已完成第一轮诊断交接增强：fit report、验证计划导出和前端结果卡片均显示外部复核材料。
- 后续继续强化专用统计库验证路径、交叉验证/校准和更细粒度的人工统计复核提示。

### 阶段 E：投稿前生产化

- 扩展 Author Guidelines PDF / 强 JS 页面处理。
- 完成目标期刊风格化英文写作和 Response to Reviewers 定稿辅助。
- 增强真实审稿意见的段落识别、内容类型识别和稿件位置推荐，支持更精确的返修定位。
