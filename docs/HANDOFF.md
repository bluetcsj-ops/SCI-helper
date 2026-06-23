# 项目交接记录

更新时间：2026-06-23

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的本地原型工程。当前目标是建立可运行、可扩展、可带示例医学数据跑通的多智能体论文工作台，并逐步接入真实科研数据、真实文献检索、英文论文写作、审稿和投稿准备能力。

## 当前状态

当前 `main` 分支已提交 Data Lin 高级模型生产化优先路径、Writer / Reviewer 返修写作清单阶段成果和 mixed-effects model 第一版可执行路径。最新高级模型状态：

- Data Lin 高级模型面板可显示“统计验证计划”。
- 可按 linear/logistic/Cox/mixed-effects 生成模型专属外部验证清单。
- Cox 默认优先使用 statsmodels `PHReg`，失败时回退内部 Cox partial-likelihood 近似。
- Mixed-effects 默认优先使用 statsmodels `MixedLM` random-intercept 路径，失败时回退 clustered linear approximation。
- 可导出 `advanced-model-validation-plan.md`，用于把 exploratory 输出交给 validated statistical environment 复核。
- 导出后页面显示文件名确认，并提供“复制验证计划”兜底，便于人工验收下载是否成功。
- Writer Methods / Results 会写入 pending external validation 英文边界提示。
- Reviewer 检查清单新增“高级模型外部验证缺口”，提示残差、校准、PH assumption、Schoenfeld residuals、random effects、ICC 等模型特异核验项。

当前整体完成度约 **98.8%**。主链路已经闭环：

```text
Mentor → Vera Protocol → Data Lin → Alex Writer → Reviewer
```

## 当前核心能力

### Mentor

- 课题推荐。
- 预备真实引用加载。
- 候选引用复核、用途标记、全文核对。
- Vancouver 候选引用导出。
- 推荐卡写入研究方案。

### Vera Protocol

- 结构化研究方案编辑与保存。
- 方案草案和 Rhea 执行计划草案。
- 方案质量检查。
- 方案-数据一致性检查。
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

## 当前验证记录

最近验证通过：

```powershell
cd "D:\SCI helper\SCI-helper\frontend"
.\node_modules\.bin\tsc.cmd --noEmit
npm run build
```

后端验证通过：

```powershell
cd "D:\SCI helper\SCI-helper\backend"
$env:DATABASE_URL='sqlite:///:memory:'
.\.venv\Scripts\python.exe -c "from app.main import app; print('backend app memory db ok')"
```

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
- Data Lin mixed-effects model fit：
  - 含 repeated-measures 字段与 cluster 分组的 CSV 可推荐 `mixed_effects`。
  - 优先走 statsmodels `MixedLM` random-intercept 路径，返回 exploratory fixed-effect estimates、random intercept variance、residual variance、ICC、cluster 数和重复观测/随机效应结构复核提示。
  - 前端会显示 `Linear mixed-effects model` / cluster 输出、`advanced-mixed-effects-statsmodels-v1`，并可导出 `advanced-mixed-effects-fit.md`。

本轮验收发现并修复：

- 实际 SQLite `data_audit_logs.raw_data_saved` 列是 `VARCHAR(8)`，旧 ORM Boolean 映射会把字符串 `"0"` 读成 `true`。
- 已改为按字符串 `"0"/"1"` 写入，并在仓库层显式转换为布尔值，保证页面显示“未保存原始 CSV”与接口字段一致。

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
5. 在 Data Lin 中检查：
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
6. 在 Alex Writer 中检查：
   - 英文 Methods / Results
   - Discussion
   - Abstract
   - Cover Letter
   - 目标期刊规则校验
   - 后端版本库保存、恢复 Introduction、恢复全文草稿、逐字段编辑历史恢复内容、版本 diff、历史章节复制和清除恢复
   - Reviewer 修改提醒
7. 在 Reviewer 中检查：
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
8. 逐项测试主要导出按钮。

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
cd "D:\SCI helper\SCI-helper\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd "D:\SCI helper\SCI-helper\frontend"
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

## 下一步建议

1. 先跑完整 UI 验收：
   - 预备引用
   - 预备 DATA
   - Data Lin 高级模型
   - Writer 英文稿件与版本库
   - Reviewer 样例 decision letter、章节归属、Writer 修改提醒和导出
2. 下一阶段优先级：
   - Cox survival analysis 和 mixed-effects model 诊断增强与外部统计软件复核交接
   - 真实放疗专科数据适配与数据许可核对
   - Writer 写作风格学习和目标期刊英文表达偏好
   - Reviewer / Writer 返修链路增强：让英文审稿回复更自然，并自动识别审稿意见对应的章节、段落和内容类型
   - Author Guidelines PDF / 强 JS 页面处理
3. 稳定化原则：
   - 页面和交互继续保持中文
   - 论文正文、投稿材料、Response to Reviewers 和导出稿件继续保持英文
   - 高级统计和 Reviewer 输出继续标注人工核验边界
4. Git 节奏：
   - 小功能本地阶段性提交
   - 一组完整大功能或阶段复盘后再推送 GitHub
