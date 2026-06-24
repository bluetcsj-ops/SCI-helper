# 使用方法

本文档说明当前本地原型的启动和基础使用方式。

## 1. 启动后端

打开 PowerShell：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

验证：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

## 2. 启动前端

打开第二个 PowerShell：

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

浏览器访问：

```text
http://127.0.0.1:3000/
```

## 3. 推荐主流程

进入“我的研究书房”后，建议按论文流程总览推进：

1. **选题与引用**：点击 Mentor。
2. **研究方案**：点击 Vera Protocol。
3. **数据与统计**：点击 Data Lin。
4. **写作草稿**：点击 Alex Writer。
5. **投稿前审查**：点击 Reviewer。

流程总览条中的每个阶段都可以点击，右侧会切换到对应智能体工作区。

## 4. 快速联调：预备 DATA

当前项目内置四个预备 DATA 样例，用于避免空跑流程：

- 放疗计划质量样例 CSV：`frontend/public/sample-data/radiotherapy_plan_quality_sample.csv`
- 公开 EHR demo CSV：`frontend/public/sample-data/mimic_iv_demo_los_sample.csv`
- Cox 生存分析样例 CSV：`frontend/public/sample-data/radiotherapy_survival_cox_sample.csv`
- Mixed-effects 重复测量样例 CSV：`frontend/public/sample-data/radiotherapy_mixed_effects_sample.csv`
- 引用：`frontend/public/sample-data/prepared_references.json`
- 说明：`shared/sample-data/README.md`

使用方式：

1. 点击 **Dr. Data Lin**。
2. 在 **预备 DATA 样例** 中选择“放疗计划质量样例”、“MIMIC-IV EHR demo”、“Cox 生存分析样例”或 “Mixed-effects 重复测量样例”。
3. 点击 **一键联调到 Writer**。
4. 系统会自动完成：
   - 加载预备 CSV
   - 生成质控报告
   - 生成统计草案
   - 保存分析记录
   - 切换到 Alex Writer
5. 在 Alex Writer 中查看 **Methods / Results 草稿**。
6. 点击 `导出结果` 下载 `methods-results-draft.md`。

Cox 生存分析样例的验收方式：

1. 选择 **Cox 生存分析样例**。
2. 点击 **加载预备 DATA**。
3. 生成统计草案后，点击 **生成模型计划**。
4. 确认推荐模型为 `Cox proportional hazards model`。
5. 点击 **运行推荐模型**，确认页面显示 `HR 输出`。
6. 点击 **导出结果** 下载 `advanced-cox-model-fit.md`。

Mixed-effects 重复测量样例的验收方式：

1. 选择 **Mixed-effects 重复测量样例**。
2. 点击 **加载预备 DATA**。
3. 生成统计草案后，点击 **生成模型计划**。
4. 确认推荐模型为 `Linear mixed-effects model`。
5. 点击 **运行推荐模型**，确认页面显示 `cluster 输出`。
6. 点击 **导出结果** 下载 `advanced-mixed-effects-fit.md`。

如果只想测试质控，不进入 Writer，可点击 **加载预备 DATA**。

## 5. Mentor 选题与引用

点击 **Prof. RadOnc Mentor** 后，可以：

- 查看趋势概览。
- 填写设备、计划系统、数据类型、科研时间和兴趣方向。
- 生成课题推荐。生成后页面会自动滚到推荐报告，并显示“已生成 X 张推荐卡”的提示条。
- 在每张推荐卡的 **Mentor 落地验收** 区域核对：
  - 最小数据字段
  - 测试落地清单
  - 写入 Protocol 来源追踪
- 点击 **加载预备引用**，快速载入真实公开数据源引用。
- 在推荐依据中查看：
  - PMID / DOI
  - PubMed / DOI 链接
  - 候选 citation
  - Vancouver 候选引用
  - 人工核验缺口
- 将候选引用标记为：
  - 待复核
  - 确认可用
  - 排除
- 标记全文核对和 Introduction / Discussion 用途。
- 导出 `references-vancouver.md`。
- 导出 Mentor brief，核对推荐卡、候选证据、最小数据字段和写入追踪是否完整。
- 点击 **交给 Alex Writer**，把确认可用的候选引用交给 Writer。
- 点击 **预览写入**，检查写入研究方案前的研究问题、数据需求、统计路线、Rhea 里程碑和 Mentor 来源追踪；数据需求中应包含最小数据字段、IRB / 脱敏、数据字典、来源系统、导出格式和计划系统追踪，再确认写入研究方案。

## 6. Vera Protocol 研究方案

点击 **Dr. Vera Protocol** 后，可以：

- 编辑并保存结构化方案字段。
- 点击 **方案草案** 生成或读取方案草案。
- 点击 **计划草案** 生成 Rhea 执行计划草案。
- 应用计划草案到当前项目。
- 查看 **方案质量检查**：
  - 完成度百分比
  - 已通过 / 需补充 / 高风险
  - 下一步建议
  - 最小数据字段是否可追踪
  - 伦理/数据许可是否标明
  - 数据字典与导出路径是否明确
  - 放疗计划系统追踪是否明确
- 导出 `protocol-quality-check.md`。
- 查看 **方案-数据一致性检查**，重点核对 **Protocol 最小字段写入** 是否显示 Data Lin 已从 Protocol 读取必需字段，并导出 `protocol-data-consistency-check.md`。
- 查看 **Protocol version snapshot** 并导出 `protocol-version-snapshot.md`。

方案字段包括：

- 研究问题
- 研究假设
- 研究类型
- 主要终点
- 次要终点
- 纳入标准
- 排除标准
- 数据需求
- 实验流程
- 统计路线
- 目标期刊
- Rhea 里程碑

## 7. Data Lin 数据工作区

点击 **Dr. Data Lin** 后，可以：

- 上传脱敏 CSV。
- 加载预备 DATA。
- 一键联调到 Writer。
- 查看字段需求；如果刚从 Mentor 写入 Protocol，应能看到来自 Protocol 的最小字段、伦理/脱敏、数据字典和计划系统追踪相关需求。
- 查看 CSV 质控报告。
- 查看脱敏与隐私检查。
- 选择分组列和结局列。
- 生成描述性统计草案。
- 查看图表预览并导出 SVG / PNG / 打印视图。
- 导出可复现参数 JSON。
- 下载可复现实验脚本。
- 在人工确认后执行正式检验。
- 保存和恢复分析记录。
- 查看数据审计日志。

注意：

- 当前不会保存原始 CSV。
- 保存分析记录只保存报告 JSON。
- 红色隐私风险会阻止统计草案。
- 未执行正式检验时，Writer 不会编造 P 值。

## 8. Alex Writer 写作工作区

点击 **Alex Writer** 后，可以：

- 查看 Introduction 段落骨架。
- 编辑并保存 Introduction 草稿。
- 插入候选引用。
- 手动绑定引用到背景段、研究空白段或目的段。
- 查看字段级引用映射。
- 查看引用质控摘要。
- 查看 Methods / Results 草稿。
- 导出：
  - `alex-writer-outline.md`
  - `introduction-draft.md`
  - `methods-results-draft.md`

Methods / Results 草稿来自 Data Lin 的质控、统计、图表和正式检验状态。未执行正式检验时，系统会明确提示不能写 P 值或显著性结论。

## 9. Reviewer 投稿前审查

点击 **Rev. Dr. Helena Skov** 后，可以查看投稿前审稿清单。

检查维度：

- 研究方案完整性
- 数据真实性与脱敏
- 统计结果边界
- Methods / Results 一致性
- Introduction 引用追溯
- 执行风险与里程碑

可以导出：

```text
pre-submission-review.md
```

该清单是规则型自查，不替代真实同行评审。

## 10. Swagger API

接口测试页面：

```text
http://127.0.0.1:8000/docs
```

常用接口：

- `GET /health`
- `GET /api/projects/`
- `GET /api/dashboard/`
- `GET /api/mentor/trends`
- `POST /api/mentor/recommendations`
- `GET /api/projects/{project_id}/protocol`
- `PUT /api/projects/{project_id}/protocol`
- `GET /api/projects/{project_id}/data/requirements`
- `POST /api/projects/{project_id}/data/quality-report`
- `POST /api/projects/{project_id}/data/statistics-report`
- `POST /api/projects/{project_id}/data/formal-test-report`
- `POST /api/projects/{project_id}/data/analysis-records`

## 11. 当前尚未完成

- 自然语言驱动的自主分析计划选择器。
- Discussion / Abstract / Cover letter。
- 目标期刊格式模板。
- 深度审稿意见和 Response to Reviewers。
- 更高级统计模型，如混合效应模型、生存分析和回归建模。
- Telegram / Email 真实提醒。
- 正式医院级脱敏流程。
