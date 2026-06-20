# 项目交接记录

更新时间：2026-06-20

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的本地原型工程。当前目标是建立可运行、可扩展、可带示例医学数据跑通的多智能体论文工作台，并逐步接入真实科研数据、真实文献检索、英文论文写作、审稿和投稿准备能力。

## 当前状态

当前 `main` 分支已提交 Data Lin 高级模型执行第一版，以及 Writer / Reviewer 返修写作清单阶段成果。本轮新增未提交改动主要是 Reviewer 返修清单章节归属持久化编辑：

- 每条真实审稿意见可人工修正影响章节，并通过后端字段持久化保存。
- Reviewer 返修写作清单和 Writer 修改提醒同步读取人工修正后的章节归属。
- 导出 `writer-revision-checklist.md` 时写入最终章节归属，并提示章节归属需人工确认。
- 旧 SQLite 表会在仓库层自动补 `manual_revision_sections_json` 列。

当前整体完成度约 **97%**。主链路已经闭环：

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
- 自主分析计划建议。
- 高级统计模型计划：
  - linear regression
  - logistic regression
  - Cox proportional hazards model
  - linear mixed-effects model
- 导出：
  - `analysis-plan-suggestion.md`
  - `advanced-model-plan.md`
  - analysis parameters JSON
  - reproducible script

### Alex Writer

- 英文 Introduction 草稿、引用映射和引用质控。
- Methods / Results 草稿。
  - 可识别放疗计划质量字段，补充 target coverage、OAR dose、patient-specific QA、delivery time、monitor units 和 plan complexity 的英文专科提示。
- Discussion 草稿。
- Abstract 草稿。
- Cover Letter 草稿。
- 投稿包检查清单。
- 目标期刊模板。
- Author Guidelines 本地规则校验：
  - 粘贴目标期刊 URL / 来源备注和指南关键文本
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
- 深度审稿意见。
- Response to Reviewers 草稿。
- 真实审稿意见导入。
- Major / Minor / Editorial 初分。
- 逐条英文 response draft。
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
  - 人工确认不完整时阻止执行。
  - CSV 含疑似直接身份标识时阻止执行。
  - 最新审计日志返回 `raw_data_saved=false`。

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
   - Deep review comments
   - Response to Reviewers
   - 真实审稿意见导入
   - 逐条英文回复草稿
   - 返修清单章节归属人工修正
   - 返修写作清单
8. 逐项测试主要导出按钮。

## 当前限制

- 当前预备 CSV 包含放疗计划质量脱敏模拟样例和 MIMIC-IV EHR demo；前者用于放疗字段流程联调，后者用于公开医学 EHR 流程联调，二者都不代表正式课题结论。
- 高级模型执行第一版已支持 linear regression；logistic regression、Cox 和 mixed-effects 仍只停留在计划/待开发阶段。
- Linear regression 输出是探索性拟合结果，仍需要人工统计复核，不应直接作为最终 SCI 结论。
- Writer 版本库当前恢复 Introduction；派生章节可作为历史恢复内容优先显示、逐字段编辑、预览、diff、复制、导出，并可纳入新的版本快照，但不会直接写回后端全文字段。
- Reviewer 真实意见拆分是规则型，复杂 decision letter 仍需人工校正。
- Reviewer 到 Writer 的章节映射支持人工修正和持久化保存，但仍需人工对照原始 decision letter 最终确认。
- 当前 Author Guidelines 校验第一版依赖用户粘贴文本，不自动抓取官网页面；正式投稿仍需在投稿系统中最终核对。
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

1. 人工跑完整 UI 验收。
2. 完成 Data Lin linear regression UI 验收后，再决定是否阶段性提交本轮改动。
3. 后续补真实高级统计模型拟合：
   - logistic regression
   - survival analysis
   - mixed-effects model
4. 接入真实放疗专科样例数据。
5. 做目标期刊官网规则自动抓取。
