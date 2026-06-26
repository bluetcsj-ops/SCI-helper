# 正式研究前真实数据接入确认清单

用途：本模板只在某个 Mentor/Vera 方案被选定、准备进入真实脱敏数据分析或投稿准备时使用；它不是 Project A / B 预设样例的必填材料，也不代表系统已经拥有真实机构 protocol。所有 `[待填写]` 项必须由研究者、机构伦理/数据管理负责人或统计复核人员提供，不能由系统自动编造。

当前状态：protocol-draft-ready，real-data-not-started，not submission-ready。

## 0. 使用原则

- 不上传含姓名、住院号、门诊号、身份证号、电话、完整日期或可回溯自由文本的 CSV。
- 不把 Project A / B 或当前预备样例 `radiotherapy_plan_quality_sample.csv` 当作真实研究证据。
- 不在伦理、数据授权、TPS/DICOM/QA 和统计复核未完成前生成最终 SCI 结论。
- 如果某项暂时不可获得，请填写“不可获得 + 原因 + 替代字段/处理策略”，不要留空。

## 1. 投稿阻塞项

这些字段未完成时，任何由 Mentor/Vera 生成的研究草案都不应进入投稿版 manuscript。

### 1.1 Ethics / IRB / Consent

| 字段 | 填写内容 |
| --- | --- |
| IRB 或伦理委员会名称 | [待填写] |
| 批准编号 | [待填写] |
| 批准日期 | [待填写] |
| 如为豁免，豁免依据 | [待填写] |
| 知情同意要求 | [待填写] |
| 如免除知情同意，免除理由 | [待填写] |
| 如不属于人体研究，判定依据 | [待填写] |
| 机构批准的英文伦理表述 | [待填写] |

验收标准：

- Writer 的 Ethics / Consent statement 能替换占位文本。
- Reviewer 不再提示伦理和知情同意声明缺失。
- 投稿系统所需声明与 manuscript、cover letter、submission checklist 一致。

### 1.2 Target Journal Declarations

| 字段 | 填写内容 |
| --- | --- |
| 目标期刊 | [待填写] |
| Article type | [待填写] |
| Abstract word limit | [待填写] |
| Keyword limit | [待填写] |
| Ethics statement | [待填写] |
| Consent statement | [待填写] |
| Funding statement | [待填写] |
| Conflict of interest statement | [待填写] |
| Data availability statement | [待填写] |
| Code availability statement | [待填写] |
| Author contribution statement | [待填写] |
| Acknowledgments | [待填写] |
| Generative AI assistance disclosure | [待填写] |

验收标准：

- Writer 可生成目标期刊投稿包。
- Reviewer 的目标期刊规则检查不再停留在缺声明状态。
- 所有声明可被通讯作者和机构要求接受。

## 2. 数据分析前必须项

这些字段未完成时，不应上传最终真实 CSV 或执行正式统计检验。

### 2.1 Data Authorization And Privacy

| 字段 | 填写内容 |
| --- | --- |
| 数据拥有科室或负责人 | [待填写] |
| 数据使用批准编号或记录 | [待填写] |
| 被批准的数据使用者角色 | [待填写] |
| 数据访问位置 | [待填写] |
| 数据保留期限 | [待填写] |
| 脱敏方法 | [待填写] |
| 已移除的直接身份标识 | [待填写] |
| 已复核的间接身份标识 | [待填写] |
| 日期处理规则 | [待填写] |
| 原始 CSV 保存规则 | [待填写] |
| 原始 DICOM 保存规则 | [待填写] |
| 数据销毁或归档政策 | [待填写] |

验收标准：

- Data Lin 能确认上传 CSV 是最终脱敏数据，而不是流程样例。
- 隐私检查不出现红色阻断项。
- Methods 可清楚说明数据来源、脱敏方式和原始数据保存边界。

### 2.2 Field Dictionary

每个纳入字段都应填写一行。

| 中文字段名 | English column name | 单位 | 来源系统 | 导出格式 | 缺失值编码 | 派生规则 | 必需/建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [待填写] | [待填写] | [待填写] | [待填写] | [待填写] | [待填写] | [待填写] | [待填写] |

最低建议覆盖：

- 匿名病例或计划 ID。
- 治疗部位。
- 治疗技术。
- 处方剂量和分割次数。
- PTV / OAR 剂量学指标。
- QA 结果或 gamma pass rate。
- 计划复杂度或 MU / delivery time。
- TPS/计划系统版本。
- 剂量计算算法。
- 主要终点和次要终点。

验收标准：

- Vera Protocol 的数据需求可追踪到真实字段。
- Data Lin 字段需求卡能正确显示最小字段、伦理/脱敏、数据字典、TPS/DICOM、终点/统计分类。
- Writer 的 Methods / Results 不再丢失字段来源、单位和派生规则。

### 2.3 CSV Export Path / SOP

| 字段 | 填写内容 |
| --- | --- |
| 真实 CSV 导出路径或 SOP 名称 | [待填写] |
| 导出负责人 | [待填写] |
| 导出时间戳规则 | [待填写] |
| 文件命名规则 | [待填写] |
| 版本控制规则 | [待填写] |
| 上传到系统前的人工检查人 | [待填写] |

验收标准：

- Data Lin 上传的是最终脱敏 CSV。
- 审计记录可说明文件来源和版本。
- 后续结果可复现到同一批数据。

## 3. 放疗计划与 QA 追踪

这些字段决定 Methods 的放疗物理可复现性，也是 Reviewer 高风险检查重点。

### 3.1 TPS / DICOM / QA Traceability

| 字段 | 填写内容 |
| --- | --- |
| TPS 或在线自适应计划系统 | [待填写] |
| 软件版本 | [待填写] |
| 在线自适应软件版本，如适用 | [待填写] |
| 剂量计算算法 | [待填写] |
| Calculation grid | [待填写] |
| Dose reporting convention | [待填写] |
| 治疗机器型号 | [待填写] |
| MLC 型号 | [待填写] |
| 影像系统 | [待填写] |
| RTPLAN 导出规则 | [待填写] |
| RTDOSE 导出规则 | [待填写] |
| RTSTRUCT 导出规则 | [待填写] |
| 结构命名规则 | [待填写] |
| Target 命名规则 | [待填写] |
| OAR 命名规则 | [待填写] |
| QA 测量设备 | [待填写] |
| Gamma criterion | [待填写] |
| Dose threshold | [待填写] |
| Passing-rate threshold | [待填写] |
| QA failure handling | [待填写] |

验收标准：

- Reviewer 不再提示 TPS version、dose calculation algorithm、gamma criteria、structure naming 缺失。
- Writer Methods 有足够技术细节描述计划生成、剂量计算、结构命名和 QA 流程。
- Data Lin 可把真实 DICOM/QA 字段映射到 Protocol 需求。

## 4. 统计定稿

这些字段完成后，才能把 exploratory workflow 输出转为正式统计报告。

### 4.1 Statistical Finalization

| 字段 | 填写内容 |
| --- | --- |
| Final primary endpoint | [待填写] |
| Final secondary endpoints | [待填写] |
| Final grouping variable | [待填写] |
| 观察值是否独立 | [待填写] |
| 是否存在同一患者多计划或重复测量 | [待填写] |
| Missing-data handling | [待填写] |
| Outlier definition | [待填写] |
| QA failure binary endpoint definition | [待填写] |
| Distribution check method | [待填写] |
| Variance check method | [待填写] |
| Multiplicity correction | [待填写] |
| 统计复核人员 | [待填写] |
| P values / confidence intervals 最终报告策略 | [待填写] |

验收标准：

- Data Lin 可在人工确认后重新运行质控、描述统计和正式检验。
- Cox / mixed-effects 如被使用，需完成 PH assumption、Schoenfeld residuals、random-effects 结构、收敛、残差诊断和样本量限制复核。
- Writer Results 不再把探索性输出写成最终推断。
- Reviewer 不再提示统计边界和样本量解释缺失。

## 5. 可后补但需追踪项

这些内容不一定阻止首轮真实数据质控，但需要在投稿前完成。

| 项目 | 当前状态 | 负责人 | 目标日期 | 备注 |
| --- | --- | --- | --- | --- |
| 文献全文人工核验 | [待填写] | [待填写] | [待填写] | PMID / DOI / Vancouver 格式需最终核对 |
| 目标期刊 Author Guidelines PDF 或强 JS 页面核对 | [待填写] | [待填写] | [待填写] | 系统当前主要支持 HTML 或手动粘贴 |
| Response to Reviewers 语气润色 | [待填写] | [待填写] | [待填写] | 降低模板感，补充具体 page / line |
| Writer 风格学习材料 | [待填写] | [待填写] | [待填写] | 可用既往英文论文或目标期刊范文 |

## 6. 推荐执行顺序

1. 完成第 1 节 Ethics / IRB / Consent 和 Target Journal Declarations 的机构批准文本。
2. 完成第 2 节 Data Authorization、脱敏规则、字段字典和 CSV 导出 SOP。
3. 完成第 3 节 TPS / DICOM / QA Traceability。
4. 准备最终脱敏 CSV，并用 Data Lin 重新跑 quality control。
5. 根据第 4 节统计定稿信息重新生成统计草案和正式检验。
6. 将最终分析记录恢复到 Writer，保存新的 Writer version。
7. 重新运行 Reviewer，确认没有 high-risk submission blockers。

## 7. 当前缺口摘要

- 当前 Project A / B 使用的是流程验证样例，不是正式机构数据。
- 当进入真实数据接入时，所有真实机构字段仍需人工填写。
- 当前统计输出可以作为 exploratory draft material，不能直接作为 SCI 最终结论。
- 当前最优下一步是先让 Mentor/Vera 生成可讨论的研究方案和实验方案；只有选定真实研究后，才按本模板第 1-3 节补齐真实机构材料并上传最终脱敏 CSV。
