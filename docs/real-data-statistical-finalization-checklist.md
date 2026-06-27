# 真实数据前统计定稿复核清单

更新日期：2026-06-28

用途：本清单用于某个 Mentor/Vera 方案被研究者选定、准备接入真实脱敏数据或投稿前统计定稿时使用。它不是 Project A / B 预设样例的完成条件，也不代表系统已经完成真实机构数据授权、IRB、脱敏、TPS/DICOM/QA 或人工统计复核。

## 使用边界

- Data Lin 当前输出仍是 exploratory draft material，不能直接作为 SCI 最终推断。
- OR、HR、CI、P 值、校准、AUC、ICC、方差成分和随机效应结论，必须在独立统计环境和人工复核后才可写入正式稿。
- 本清单应与 `docs/project-a-real-data-intake-template.md` 一起使用；真实字段字典、数据许可、伦理/脱敏和计划系统追踪未完成前，不应进入最终统计报告。
- Project A / B 仅作为流程样例工作区，不是本清单中的真实研究 protocol 来源。

## 1. 通用统计定稿项

| 项目 | 需填写/确认 | 状态 |
| --- | --- | --- |
| Final primary endpoint | [待填写] | 待确认 |
| Final secondary endpoints | [待填写] | 待确认 |
| Analysis population | [待填写] | 待确认 |
| Inclusion / exclusion lock date | [待填写] | 待确认 |
| Unit of analysis | patient / plan / fraction / lesion / other: [待填写] | 待确认 |
| Independence assumption | [待填写] | 待确认 |
| Repeated-measures or clustered structure | [待填写] | 待确认 |
| Missing-data rule | complete case / imputation / sensitivity analysis: [待填写] | 待确认 |
| Outlier definition | [待填写] | 待确认 |
| Multiplicity strategy | none / Bonferroni / FDR / hierarchical testing / other: [待填写] | 待确认 |
| Minimum sample-size rationale | [待填写] | 待确认 |
| Statistical software and version | R / Python / SAS / SPSS / Stata / other: [待填写] | 待确认 |
| Independent statistician reviewer | [待填写] | 待确认 |

## 2. Logistic Regression 定稿项

适用场景：二分类终点，例如 QA pass/fail、high-risk plan、toxicity yes/no 或其他预先定义的 binary endpoint。

| 项目 | 需确认内容 | 状态 |
| --- | --- | --- |
| Binary endpoint coding | 明确 event / non-event，记录原始字段值映射 | 待确认 |
| Events per variable | 计算事件数、非事件数和候选自变量数量 | 待确认 |
| Separation / sparse cells | 检查 complete or quasi separation、稀疏分层和极端 OR | 待确认 |
| Predictor pre-specification | 区分预设变量、探索变量和数据驱动变量 | 待确认 |
| Linearity in the logit | 连续变量是否需要 spline、分段或转换 | 待确认 |
| Multicollinearity | VIF、相关矩阵或临床冗余变量处理 | 待确认 |
| Calibration | calibration plot、calibration intercept/slope 或 Hosmer-Lemeshow 使用边界 | 待确认 |
| Discrimination | AUC / ROC、sensitivity、specificity、threshold rule | 待确认 |
| Internal validation | bootstrap / cross-validation / train-test split | 待确认 |
| External validation | 独立队列、时间外验证或机构外验证计划 | 待确认 |
| Reporting boundary | OR、CI、P 值是否仍标注 exploratory 或可正式报告 | 待确认 |

## 3. Cox Proportional Hazards 定稿项

适用场景：含随访时间和事件状态的 time-to-event 终点。

| 项目 | 需确认内容 | 状态 |
| --- | --- | --- |
| Time origin | 随访起点定义，例如治疗开始、计划批准、诊断或随访登记日 | 待确认 |
| Event definition | 事件编码、复合事件规则和 competing risk 边界 | 待确认 |
| Censoring rule | 末次随访、失访、死亡或其他删失规则 | 待确认 |
| Follow-up completeness | 中位随访时间、最短/最长随访、删失比例 | 待确认 |
| Event count adequacy | 事件数是否支持候选变量数量 | 待确认 |
| Ties handling | Breslow / Efron / exact 的选择和软件一致性 | 待确认 |
| PH assumption | proportional hazards assumption 检验结果 | 待确认 |
| Schoenfeld residuals | Schoenfeld residual plots/tests 和违背时处理 | 待确认 |
| Functional form | 连续变量是否需要 spline、log transform 或分段 | 待确认 |
| Influential observations | deviance / martingale residuals、DFBeta 等异常影响点 | 待确认 |
| Validation | optimism correction、交叉验证或外部验证计划 | 待确认 |
| Reporting boundary | HR、CI、P 值是否仍标注 exploratory 或可正式报告 | 待确认 |

## 4. Mixed-effects Model 定稿项

适用场景：同一患者多计划、同一病例多分次、同一机构/设备内聚类或重复测量。

| 项目 | 需确认内容 | 状态 |
| --- | --- | --- |
| Cluster unit | patient / plan / fraction / institution / machine / other: [待填写] | 待确认 |
| Repeated-measures structure | 每个 cluster 的观测次数、是否平衡、缺失模式 | 待确认 |
| Random-effects specification | random intercept、random slope 或嵌套/交叉结构 | 待确认 |
| Fixed-effects specification | 预设固定效应、交互项和临床必要协变量 | 待确认 |
| Estimation method | ML / REML，软件和版本 | 待确认 |
| Convergence diagnostics | 收敛状态、梯度、Hessian、boundary fit | 待确认 |
| Residual diagnostics | 残差分布、方差齐性、异常点和影响点 | 待确认 |
| ICC / variance components | ICC、随机截距方差、残差方差解释边界 | 待确认 |
| Small-sample correction | Satterthwaite / Kenward-Roger / bootstrap 或不使用的理由 | 待确认 |
| Sensitivity analysis | 简化模型、GEE、cluster-robust SE 或非参数方案 | 待确认 |
| Reporting boundary | fixed effects、variance components、ICC、CI、P 值是否可正式报告 | 待确认 |

## 5. Writer / Reviewer 交接标准

- Writer Methods 必须说明最终 analysis population、终点编码、软件版本、缺失值策略和模型诊断结果。
- Writer Results 只能在统计复核完成后报告正式 OR / HR / beta、CI 和 P 值；复核前继续使用 exploratory / pending external validation 边界。
- Reviewer 应确认稿件没有把 logistic OR、Cox HR 或 mixed-effects estimates 写成因果结论、已验证预测模型或正式随机效应推断。
- Reviewer 应复核校准、交叉验证、PH assumption、Schoenfeld residuals、random-effects structure、convergence、residual diagnostics 和样本量限制。

## 6. 完成判定

只有同时满足以下条件，Data Lin 的探索性输出才可进入正式统计报告：

1. 真实 IRB / 数据授权 / 脱敏 / 字段字典 / TPS-DICOM-QA 追踪已由人工确认。
2. 本清单中对应模型章节全部完成，并由统计复核人员签名或留痕。
3. 独立统计环境复现了主要结果，且软件版本、代码、输入数据版本和输出文件已归档。
4. Writer 和 Reviewer 均不再提示统计边界、样本量解释或模型诊断缺失。
