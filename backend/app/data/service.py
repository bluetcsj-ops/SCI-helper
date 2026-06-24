from __future__ import annotations

import csv
import json
import re
import warnings as py_warnings
from collections import Counter, defaultdict
from itertools import combinations
from io import StringIO
from math import erf, exp, isfinite, lgamma, log, pi, sqrt
from statistics import fmean, median, stdev

try:
    from scipy import stats as scipy_stats
except ImportError:  # pragma: no cover - optional precision dependency
    scipy_stats = None

try:
    import numpy as statsmodels_np
    from statsmodels.duration.hazard_regression import PHReg as StatsmodelsPHReg
    from statsmodels.regression.mixed_linear_model import MixedLM as StatsmodelsMixedLM
except ImportError:  # pragma: no cover - optional production statistics dependency
    statsmodels_np = None
    StatsmodelsPHReg = None
    StatsmodelsMixedLM = None

from app.data.models import (
    AdvancedModelCoefficient,
    AdvancedModelDiagnosticHandoff,
    AdvancedModelFitReport,
    AdvancedModelCandidate,
    AdvancedModelPlan,
    CategoricalLevel,
    CategoricalSummary,
    ChartDataPoint,
    ChartSpec,
    DataAnalysisParameters,
    DataColumnQuality,
    DataQualityIssue,
    DataQualityReport,
    DataPrivacyFinding,
    DataPrivacyReport,
    DataRequirementItem,
    DataRequirementSpec,
    DataStatisticsReport,
    DescriptiveStatistic,
    DistributionCheck,
    FormalTestConfirmation,
    FormalTestReport,
    FormalTestResult,
    GroupComparisonDraft,
    GroupStatistic,
    NumericSummary,
    PairwiseComparisonResult,
    ReproducibleAnalysisScript,
    StatisticalTestRecommendation,
)
from app.projects.models import Project, ProjectProtocol, RiskLevel


DEFAULT_REQUIREMENTS: list[tuple[str, str, str, str]] = [
    ("patient_id", "患者匿名 ID", "core", "用于脱敏追踪、去重和病例级汇总。"),
    ("treatment_site", "治疗部位", "core", "用于亚组分析和病例异质性判断。"),
    ("tps_version", "计划系统版本", "workflow", "用于记录计划来源和潜在批次差异。"),
    ("prescription_dose", "处方剂量", "dosimetry", "用于剂量学指标归一化和方法描述。"),
    ("fraction_count", "分割次数", "dosimetry", "用于解释剂量处方和等效剂量计算。"),
    ("target_volume", "靶区体积", "dosimetry", "用于解释计划复杂度和剂量覆盖。"),
    ("oar_metrics", "OAR 剂量指标", "dosimetry", "用于安全性和计划质量评价。"),
    ("primary_endpoint", "主要终点指标", "endpoint", "用于形成结果段落的核心比较对象。"),
]

FIELD_SYNONYMS: dict[str, list[str]] = {
    "患者匿名 ID": ["patient_id", "patientid", "case_id", "caseid", "subject_id", "subjectid"],
    "治疗部位": ["site", "treatment_site", "disease_site", "body_site"],
    "计划系统版本": ["tps", "tps_version", "planning_system", "system_version"],
    "处方剂量": ["prescription", "prescription_dose", "rx", "rx_dose", "dose"],
    "分割次数": ["fraction", "fractions", "fraction_count", "fx", "n_fraction"],
    "靶区体积": ["target_volume", "ptv_volume", "ctv_volume", "gtv_volume"],
    "OAR 剂量指标": ["oar", "oar_dose", "organ_at_risk", "dmax", "v20", "v30", "mean_dose"],
    "主要终点指标": ["primary_endpoint", "endpoint", "outcome", "metric"],
    "RTPLAN": ["rtplan", "plan_file"],
    "RTDOSE": ["rtdose", "dose_file"],
    "RTSTRUCT": ["rtstruct", "structure_file", "structure_set"],
}

MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--"}

PHI_HEADER_RULES: list[tuple[str, RiskLevel, tuple[str, ...], str]] = [
    (
        "direct_identifier",
        RiskLevel.red,
        (
            "name",
            "patientname",
            "姓名",
            "phone",
            "telephone",
            "mobile",
            "手机号",
            "电话",
            "email",
            "mail",
            "address",
            "地址",
            "idcard",
            "身份证",
            "mrn",
            "medicalrecord",
            "住院号",
            "门诊号",
        ),
        "移除直接身份标识，或在本地受控环境完成不可逆脱敏后再上传。",
    ),
    (
        "coded_identifier",
        RiskLevel.orange,
        (
            "patientid",
            "patient_id",
            "caseid",
            "case_id",
            "subjectid",
            "subject_id",
            "accession",
            "accessionnumber",
            "studyuid",
            "seriesuid",
            "sopinstanceuid",
            "dicomuid",
        ),
        "确认该编码已经随机化或哈希化，且不能从导出表直接回溯真实患者。",
    ),
    (
        "date_identifier",
        RiskLevel.orange,
        (
            "birthdate",
            "birthday",
            "dob",
            "出生日期",
            "studydate",
            "admissiondate",
            "admitdate",
            "treatmentdate",
            "scan_date",
            "检查日期",
            "治疗日期",
            "入院日期",
        ),
        "真实日期建议转换为相对天数、月份粒度或按方案进行日期平移。",
    ),
    (
        "free_text",
        RiskLevel.orange,
        (
            "note",
            "notes",
            "comment",
            "comments",
            "病程",
            "备注",
            "描述",
            "影像所见",
            "诊断意见",
        ),
        "自由文本可能夹带姓名、电话或病历号，建议先做人工审阅或 NLP 脱敏。",
    ),
]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^(?:\+?\d[\d -]{7,}\d)$")
CHINESE_ID_PATTERN = re.compile(r"^\d{17}[\dXx]$")


class DataWorkspaceService:
    def build_requirement_spec(
        self,
        project: Project,
        protocol: ProjectProtocol,
    ) -> DataRequirementSpec:
        items = [
            DataRequirementItem(
                id=item_id,
                label=label,
                category=category,
                source="Dr. Data Lin default",
                rationale=rationale,
            )
            for item_id, label, category, rationale in DEFAULT_REQUIREMENTS
        ]

        protocol_items = self._items_from_protocol(protocol)
        items = self._deduplicate_items([*items, *protocol_items])

        next_step = (
            "上传一份脱敏 CSV，Dr. Data Lin 会先做字段覆盖、缺失率和数值列范围检查。"
            if items
            else "先在研究方案中补充数据需求，再上传脱敏 CSV 做质量检查。"
        )

        return DataRequirementSpec(
            project_id=project.id,
            generated_from_protocol=bool(
                protocol.data_requirements.strip() or protocol.institutional_field_mapping.strip()
            ),
            protocol_data_requirements=protocol.data_requirements,
            items=items,
            next_step=next_step,
        )

    def build_quality_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        content: bytes,
    ) -> DataQualityReport:
        headers, rows = self._parse_csv(content)

        requirement_spec = self.build_requirement_spec(project=project, protocol=protocol)
        matched_fields, missing_fields = self._match_requirements(
            requirement_spec.items,
            headers,
        )

        columns = [self._analyze_column(header, rows) for header in headers]
        privacy_report = self._build_privacy_report(
            headers=headers,
            rows=rows,
            columns=columns,
        )
        issues = self._build_issues(
            row_count=len(rows),
            columns=columns,
            missing_required_fields=missing_fields,
        )
        issues.extend(self._privacy_findings_to_issues(privacy_report.findings))

        return DataQualityReport(
            project_id=project.id,
            file_name=file_name,
            row_count=len(rows),
            column_count=len(headers),
            requirement_items=requirement_spec.items,
            matched_required_fields=matched_fields,
            missing_required_fields=missing_fields,
            columns=columns,
            issues=issues,
            privacy_report=privacy_report,
            summary_for_writer=self._build_writer_summary(
                project=project,
                row_count=len(rows),
                column_count=len(headers),
                issue_count=len(issues),
                missing_required_fields=missing_fields,
            ),
        )

    def build_privacy_report_for_csv(self, content: bytes) -> DataPrivacyReport:
        headers, rows = self._parse_csv(content)
        columns = [self._analyze_column(header, rows) for header in headers]
        return self._build_privacy_report(
            headers=headers,
            rows=rows,
            columns=columns,
        )

    def build_statistics_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        content: bytes,
        group_column: str | None = None,
        outcome_columns: list[str] | None = None,
    ) -> DataStatisticsReport:
        headers, rows = self._parse_csv(content)
        if not rows:
            raise ValueError("CSV 文件没有可分析的数据行。")

        columns = [self._analyze_column(header, rows) for header in headers]
        numeric_columns = [column.name for column in columns if column.inferred_type == "numeric"]
        if not numeric_columns:
            raise ValueError("CSV 文件中没有可用于描述性统计的数值列。")

        selected_outcomes = self._select_outcome_columns(
            numeric_columns=numeric_columns,
            requested_columns=outcome_columns or [],
        )
        numeric_summaries = [
            self._describe_numeric_column(column_name=column_name, rows=rows)
            for column_name in selected_outcomes
        ]
        categorical_summaries = self._build_categorical_summaries(
            columns=columns,
            rows=rows,
            preferred_group_column=group_column,
        )
        valid_group_column = self._resolve_group_column(group_column, headers)
        group_comparisons = (
            [
                self._build_group_comparison(
                    column_name=column_name,
                    group_column=valid_group_column,
                    rows=rows,
                )
                for column_name in selected_outcomes
            ]
            if valid_group_column
            else []
        )
        distribution_checks = [
            self._build_distribution_check(
                summary=summary,
                rows=rows,
            )
            for summary in numeric_summaries
        ]
        test_recommendations = self._build_test_recommendations(
            selected_outcomes=selected_outcomes,
            group_column=valid_group_column,
            group_comparisons=group_comparisons,
            distribution_checks=distribution_checks,
        )
        chart_specs = self._build_chart_specs(
            rows=rows,
            numeric_summaries=numeric_summaries,
            categorical_summaries=categorical_summaries,
            group_comparisons=group_comparisons,
        )
        analysis_parameters = DataAnalysisParameters(
            source_file_name=file_name,
            row_count=len(rows),
            group_column=valid_group_column,
            outcome_columns=selected_outcomes,
            generated_chart_ids=[chart.id for chart in chart_specs],
            raw_csv_saved=False,
        )
        reproducible_script = self._build_reproducible_script(
            file_name=file_name,
            selected_outcomes=selected_outcomes,
            group_column=valid_group_column,
            chart_specs=chart_specs,
        )

        return DataStatisticsReport(
            project_id=project.id,
            file_name=file_name,
            row_count=len(rows),
            numeric_summaries=numeric_summaries,
            categorical_summaries=categorical_summaries,
            group_column=valid_group_column,
            group_comparisons=group_comparisons,
            distribution_checks=distribution_checks,
            test_recommendations=test_recommendations,
            chart_specs=chart_specs,
            analysis_parameters=analysis_parameters,
            reproducible_script=reproducible_script,
            methods_draft=self._build_methods_draft(
                protocol=protocol,
                selected_outcomes=selected_outcomes,
                group_column=valid_group_column,
            ),
            results_draft=self._build_results_draft(
                project=project,
                row_count=len(rows),
                numeric_summaries=numeric_summaries,
                group_comparisons=group_comparisons,
            ),
            next_step=(
                "Confirm the grouping variable and primary outcome before proceeding to formal "
                "statistical testing, figure generation, and Results drafting."
            ),
        )

    def build_advanced_model_plan(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        content: bytes,
        group_column: str | None = None,
        outcome_columns: list[str] | None = None,
    ) -> AdvancedModelPlan:
        headers, rows = self._parse_csv(content)
        if not rows:
            raise ValueError("CSV file is empty.")

        columns = [self._analyze_column(header, rows) for header in headers]
        numeric_columns = [column.name for column in columns if column.inferred_type == "numeric"]
        if not numeric_columns:
            raise ValueError("CSV file has no numeric column suitable for advanced model planning.")
        categorical_columns = [
            column.name
            for column in columns
            if column.inferred_type != "numeric" and 1 < column.unique_count <= 12
        ]
        binary_categorical_columns = [
            column.name
            for column in columns
            if column.inferred_type != "numeric" and column.unique_count == 2
        ]
        selected_outcomes = [
            column for column in (outcome_columns or []) if column in numeric_columns
        ] or numeric_columns[:3]
        binary_outcome = self._select_binary_outcome(
            requested_columns=outcome_columns or [],
            binary_columns=binary_categorical_columns,
            categorical_columns=categorical_columns,
        )
        clean_group_column = group_column if group_column in categorical_columns else None
        text_blob = " ".join(
            [
                protocol.research_question,
                protocol.primary_endpoint,
                protocol.secondary_endpoints,
                protocol.statistical_plan,
                protocol.data_requirements,
            ]
        ).lower()
        has_time_signal = any(token in text_blob for token in ["survival", "time-to-event", "follow-up", "death", "event"])
        repeated_signal = any(token in text_blob for token in ["repeated", "longitudinal", "mixed", "patient-level", "fraction"])
        repeated_field_signal = self._has_repeated_measure_signal(headers, columns, rows)
        if not clean_group_column:
            clean_group_column = self._select_mixed_effects_group_column(headers, columns, rows, None)
        survival_time_column, survival_event_column = self._select_survival_fields(headers, numeric_columns, columns)
        has_survival_fields = bool(survival_time_column and survival_event_column)
        candidate_pool = self._build_advanced_model_candidates(
            selected_outcomes=selected_outcomes,
            binary_outcome=binary_outcome,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            group_column=clean_group_column,
            has_time_signal=has_time_signal or has_survival_fields,
            repeated_signal=repeated_signal or repeated_field_signal,
            survival_time_column=survival_time_column,
            survival_event_column=survival_event_column,
        )
        recommended = (
            next(
                (
                    candidate
                    for candidate in candidate_pool
                    if candidate.model_id == "cox_ph"
                    and candidate.readiness == "ready"
                    and (has_time_signal or has_survival_fields)
                ),
                None,
            )
            or next((candidate for candidate in candidate_pool if candidate.readiness == "ready"), None)
        )
        recommended = (
            next(
                (
                    candidate
                    for candidate in candidate_pool
                    if candidate.model_id == "mixed_effects"
                    and candidate.readiness == "ready"
                    and (repeated_signal or repeated_field_signal)
                ),
                None,
            )
            or recommended
        )
        return AdvancedModelPlan(
            project_id=project.id,
            file_name=file_name,
            row_count=len(rows),
            generated_from_protocol=bool(text_blob.strip()),
            recommended_model_id=recommended.model_id if recommended else None,
            candidates=candidate_pool,
            next_step=(
                "Use this model plan as a pre-analysis checklist. Do not report regression, "
                "survival, or mixed-effects estimates until the model is fitted and reviewed in "
                "a validated statistical environment."
            ),
        )

    def build_advanced_model_fit_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        content: bytes,
        confirmation: FormalTestConfirmation,
        model_id: str = "linear_regression",
        group_column: str | None = None,
        outcome_columns: list[str] | None = None,
    ) -> AdvancedModelFitReport:
        if model_id not in {"linear_regression", "logistic_regression", "cox_ph", "mixed_effects"}:
            raise ValueError("当前高级模型执行支持 linear_regression、logistic_regression、cox_ph 和 mixed_effects。")

        missing_confirmations = self._missing_formal_test_confirmations(confirmation)
        confirmation_warning = (
            f"Formal-test confirmation is incomplete: {', '.join(missing_confirmations)}. "
            "Treat this model fit as exploratory draft material until confirmed."
            if missing_confirmations
            else None
        )

        privacy_report = self.build_privacy_report_for_csv(content)
        if privacy_report.risk_level == RiskLevel.red:
            raise ValueError("CSV 含疑似直接身份标识。请先完成脱敏，再执行高级模型。")

        headers, rows = self._parse_csv(content)
        if not rows:
            raise ValueError("CSV 文件没有可分析的数据行。")

        columns = [self._analyze_column(header, rows) for header in headers]
        numeric_columns = [column.name for column in columns if column.inferred_type == "numeric"]
        if not numeric_columns:
            raise ValueError("CSV 文件中没有可用于高级模型的数值列。")

        if model_id == "mixed_effects":
            selected_outcomes = self._select_outcome_columns(
                numeric_columns=numeric_columns,
                requested_columns=outcome_columns or [],
            )
            outcome_column = selected_outcomes[0]
            valid_group_column = self._select_mixed_effects_group_column(
                headers,
                columns,
                rows,
                self._resolve_group_column(group_column, headers),
            )
            if not valid_group_column:
                raise ValueError("mixed-effects model 需要 cluster / subject / patient 分组列。")
            numeric_predictors = [
                column
                for column in numeric_columns
                if column != outcome_column
            ][:3]
            return self._build_mixed_effects_fit_report(
                project=project,
                protocol=protocol,
                file_name=file_name,
                rows=rows,
                outcome_column=outcome_column,
                numeric_predictors=numeric_predictors,
                group_column=valid_group_column,
                confirmation=confirmation,
                confirmation_warning=confirmation_warning,
            )

        if model_id == "cox_ph":
            categorical_columns = [
                column.name
                for column in columns
                if column.inferred_type != "numeric" and 1 < column.unique_count <= 12
            ]
            time_column, event_column = self._select_survival_fields(headers, numeric_columns, columns)
            if not time_column or not event_column:
                raise ValueError("Cox survival analysis 需要 follow-up time 和 event/status 字段。")
            valid_group_column = self._resolve_group_column(group_column, headers)
            numeric_predictors = [
                column
                for column in numeric_columns
                if column not in {time_column, event_column}
            ][:3]
            if not numeric_predictors and not valid_group_column:
                raise ValueError("Cox survival analysis 至少需要一个数值协变量或分组预测变量。")
            return self._build_cox_ph_fit_report(
                project=project,
                protocol=protocol,
                file_name=file_name,
                rows=rows,
                time_column=time_column,
                event_column=event_column,
                numeric_predictors=numeric_predictors,
                group_column=valid_group_column if valid_group_column in categorical_columns else None,
                confirmation=confirmation,
                confirmation_warning=confirmation_warning,
            )

        if model_id == "logistic_regression":
            categorical_columns = [
                column.name
                for column in columns
                if column.inferred_type != "numeric" and 1 < column.unique_count <= 12
            ]
            binary_columns = [
                column.name
                for column in columns
                if column.inferred_type != "numeric" and column.unique_count == 2
            ]
            outcome_column = self._select_binary_outcome(
                requested_columns=outcome_columns or [],
                binary_columns=binary_columns,
                categorical_columns=categorical_columns,
            )
            if not outcome_column:
                raise ValueError("logistic regression 需要二分类结局列，或 qa_result 用于 Pass vs non-Pass。")
            valid_group_column = self._resolve_group_column(group_column, headers)
            numeric_predictors = [column for column in numeric_columns if column != outcome_column][:4]
            if not numeric_predictors and not valid_group_column:
                raise ValueError("logistic regression 至少需要一个数值协变量或一个分组预测变量。")
            return self._build_logistic_regression_fit_report(
                project=project,
                protocol=protocol,
                file_name=file_name,
                rows=rows,
                outcome_column=outcome_column,
                numeric_predictors=numeric_predictors,
                group_column=valid_group_column,
                confirmation=confirmation,
                confirmation_warning=confirmation_warning,
            )

        selected_outcomes = self._select_outcome_columns(
            numeric_columns=numeric_columns,
            requested_columns=outcome_columns or [],
        )
        outcome_column = selected_outcomes[0]
        valid_group_column = self._resolve_group_column(group_column, headers)
        numeric_predictors = [
            column
            for column in numeric_columns
            if column != outcome_column
        ][:4]
        if not numeric_predictors and not valid_group_column:
            raise ValueError("线性回归至少需要一个数值协变量或一个分组预测变量。")

        fit = self._fit_linear_regression(
            rows=rows,
            outcome_column=outcome_column,
            numeric_predictors=numeric_predictors,
            group_column=valid_group_column,
        )
        coefficient_count = len(fit["coefficients"])
        warnings = list(fit["warnings"])
        if confirmation_warning:
            warnings.append(confirmation_warning)
        if fit["complete_case_count"] < 20:
            warnings.append("Complete-case sample size is small; estimates should be treated as exploratory.")
        if fit["degrees_of_freedom"] <= 0:
            warnings.append("Residual degrees of freedom are not sufficient for inferential reporting.")
        if protocol.statistical_plan.strip():
            warnings.append("Confirm that this fitted model matches the pre-specified statistical plan.")
        else:
            warnings.append("The project protocol does not yet contain a finalized statistical model specification.")

        predictor_text = ", ".join(fit["predictor_columns"]) if fit["predictor_columns"] else "no predictors"
        methods_draft = (
            f"A multivariable linear regression model was fitted for {outcome_column} using complete-case "
            f"records from {file_name}. Candidate predictors were {predictor_text}. Categorical predictors "
            "were represented with indicator variables, and model outputs are reported as exploratory "
            "estimates pending expert review of assumptions, collinearity, and influential observations."
        )
        result_terms = [
            f"{coefficient.term}: beta={coefficient.estimate}"
            + (
                f", 95% CI {coefficient.confidence_interval_low} to {coefficient.confidence_interval_high}"
                if coefficient.confidence_interval_low is not None and coefficient.confidence_interval_high is not None
                else ""
            )
            + (
                f", P={self._format_p_value(coefficient.p_value)}"
                if coefficient.p_value is not None
                else ""
            )
            for coefficient in fit["coefficients"]
            if coefficient.term != "Intercept"
        ][:4]
        results_draft = (
            f"The linear regression model included {fit['complete_case_count']} complete cases "
            f"and {coefficient_count} coefficient term(s), with R-squared={fit['r_squared']} "
            f"and adjusted R-squared={fit['adjusted_r_squared']}. "
            + (
                f"Key exploratory estimates were: {'; '.join(result_terms)}."
                if result_terms
                else "No non-intercept predictor estimates were available for reporting."
            )
            + " These results require manual statistical review before manuscript-level inference."
        )
        audit_summary = (
            f"已执行 exploratory linear regression：{fit['complete_case_count']} 个完整病例，"
            f"{len(fit['predictor_columns'])} 个预测字段；未保存原始 CSV。"
        )

        return AdvancedModelFitReport(
            project_id=project.id,
            file_name=file_name,
            model_id="linear_regression",
            model_name="Multivariable linear regression",
            outcome_column=outcome_column,
            predictor_columns=fit["predictor_columns"],
            row_count=len(rows),
            complete_case_count=fit["complete_case_count"],
            excluded_row_count=len(rows) - fit["complete_case_count"],
            degrees_of_freedom=fit["degrees_of_freedom"],
            r_squared=fit["r_squared"],
            adjusted_r_squared=fit["adjusted_r_squared"],
            coefficients=fit["coefficients"],
            methods_draft=methods_draft,
            results_draft=results_draft,
            warnings=warnings,
            confirmation=confirmation,
            raw_csv_saved=False,
            audit_summary=audit_summary,
            next_step="把模型系数、置信区间和诊断边界交给 Alex Writer 写入英文 Methods/Results 前，请先完成人工统计复核。",
        )

    def _build_logistic_regression_fit_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
        confirmation: FormalTestConfirmation,
        confirmation_warning: str | None = None,
    ) -> AdvancedModelFitReport:
        fit = self._fit_logistic_regression(
            rows=rows,
            outcome_column=outcome_column,
            numeric_predictors=numeric_predictors,
            group_column=group_column,
        )
        warnings = list(fit["warnings"])
        if confirmation_warning:
            warnings.append(confirmation_warning)
        if fit["complete_case_count"] < 30:
            warnings.append("Complete-case sample size is small for logistic regression; odds ratios are exploratory.")
        if fit["event_count"] < 10:
            warnings.append("Event count is low; events-per-variable adequacy should be reviewed before reporting.")
        if protocol.statistical_plan.strip():
            warnings.append("Confirm that this fitted logistic model matches the pre-specified statistical plan.")
        else:
            warnings.append("The project protocol does not yet contain a finalized logistic model specification.")

        predictor_text = ", ".join(fit["predictor_columns"]) if fit["predictor_columns"] else "no predictors"
        event_label = str(fit["event_label"])
        non_event_label = str(fit["non_event_label"])
        methods_draft = (
            f"A binary logistic regression model was fitted for {outcome_column}, coded as "
            f"{event_label} versus {non_event_label}, using complete-case records from {file_name}. "
            f"Candidate predictors were {predictor_text}. Categorical predictors were represented with "
            "indicator variables. Odds ratios are exploratory and require manual review of coding, "
            "events per variable, separation, and model convergence before manuscript-level inference."
        )
        result_terms = [
            f"{coefficient.term}: OR={coefficient.estimate}"
            + (
                f", 95% CI {coefficient.confidence_interval_low} to {coefficient.confidence_interval_high}"
                if coefficient.confidence_interval_low is not None and coefficient.confidence_interval_high is not None
                else ""
            )
            + (
                f", P={self._format_p_value(coefficient.p_value)}"
                if coefficient.p_value is not None
                else ""
            )
            for coefficient in fit["coefficients"]
            if coefficient.term != "Intercept"
        ][:4]
        results_draft = (
            f"The logistic regression model included {fit['complete_case_count']} complete cases, "
            f"with {fit['event_count']} event(s) coded as {event_label}. "
            + (
                f"Key exploratory odds-ratio estimates were: {'; '.join(result_terms)}."
                if result_terms
                else "No non-intercept odds-ratio estimates were available for reporting."
            )
            + " These results require manual statistical review before any claim about prediction or association."
        )
        audit_summary = (
            f"已执行 exploratory logistic regression：{fit['complete_case_count']} 个完整病例，"
            f"{fit['event_count']} 个事件，{len(fit['predictor_columns'])} 个预测字段；未保存原始 CSV。"
        )
        return AdvancedModelFitReport(
            project_id=project.id,
            file_name=file_name,
            model_id="logistic_regression",
            model_name="Binary logistic regression",
            outcome_column=outcome_column,
            predictor_columns=fit["predictor_columns"],
            row_count=len(rows),
            complete_case_count=fit["complete_case_count"],
            excluded_row_count=len(rows) - fit["complete_case_count"],
            degrees_of_freedom=fit["degrees_of_freedom"],
            r_squared=None,
            adjusted_r_squared=None,
            coefficients=fit["coefficients"],
            methods_draft=methods_draft,
            results_draft=results_draft,
            warnings=warnings,
            confirmation=confirmation,
            method_version="advanced-logistic-v1",
            raw_csv_saved=False,
            audit_summary=audit_summary,
            next_step="把 odds ratio、置信区间、事件数和收敛边界交给 Alex Writer 前，请先完成人工统计复核。",
        )

    def _build_cox_diagnostic_handoff(
        self,
        fit: dict[str, object],
        time_column: str,
        event_column: str,
        method_version: str,
    ) -> AdvancedModelDiagnosticHandoff:
        complete_case_count = int(fit["complete_case_count"])
        event_count = int(fit["event_count"])
        predictor_count = len(fit["predictor_columns"])
        censored_count = max(complete_case_count - event_count, 0)
        return AdvancedModelDiagnosticHandoff(
            model_family="cox_ph",
            sample_context=[
                f"Complete cases: {complete_case_count}",
                f"Events: {event_count}",
                f"Censored records: {censored_count}",
                f"Predictor terms: {predictor_count}",
                f"Time column: {time_column}",
                f"Event column: {event_column}",
                f"Fit route: {method_version}",
            ],
            required_diagnostics=[
                "Confirm time origin, follow-up unit, event coding, and censoring definition from the source data dictionary.",
                "Recheck events per variable and tied-event handling before interpreting any hazard ratio.",
                "Run proportional-hazards diagnostics with Schoenfeld residuals in validated survival-analysis software.",
                "Inspect influential observations and functional form of continuous covariates.",
                "Compare the exploratory HR table against an independently reproduced R survival, lifelines, or statsmodels PHReg fit.",
            ],
            handoff_artifacts=[
                "Analysis-ready survival CSV with the time and event columns preserved.",
                "Data dictionary for event coding, censoring, time origin, follow-up unit, and excluded rows.",
                "Model formula and covariate coding table, including reference levels and standardized predictors.",
                "Validated HR table with 95% CI, P values, tied-event method, and PH-assumption output.",
            ],
            manuscript_boundary=(
                "Treat HR estimates as exploratory until proportional-hazards diagnostics, event/censoring coding, "
                "and independent survival-model reproduction have been reviewed."
            ),
            reviewer_focus=(
                "Reviewer should verify events per variable, censoring definition, tied events, Schoenfeld residuals, "
                "PH assumption, and whether prognostic claims remain clearly exploratory."
            ),
        )

    def _build_mixed_effects_diagnostic_handoff(
        self,
        fit: dict[str, object],
        outcome_column: str,
        group_column: str,
        method_version: str,
    ) -> AdvancedModelDiagnosticHandoff:
        return AdvancedModelDiagnosticHandoff(
            model_family="mixed_effects",
            sample_context=[
                f"Complete cases: {int(fit['complete_case_count'])}",
                f"Clusters: {int(fit['cluster_count'])}",
                f"Singleton clusters: {int(fit['singleton_cluster_count'])}",
                f"Median cluster size: {fit['median_cluster_size']}",
                f"Approximate ICC: {fit['approximate_icc']}",
                f"Outcome column: {outcome_column}",
                f"Group column: {group_column}",
                f"Fit route: {method_version}",
            ],
            required_diagnostics=[
                "Confirm cluster ID, repeated-measure ordering, independence assumptions, and long-format data structure.",
                "Reproduce the fit in validated mixed-model software and decide ML versus REML according to the analysis goal.",
                "Check convergence, singular fit, optimizer sensitivity, residual diagnostics, and fitted-value patterns.",
                "Review random-intercept versus random-slope structure before interpreting variance components or ICC.",
                "Assess influence of small clusters and singleton clusters on fixed-effect and variance estimates.",
            ],
            handoff_artifacts=[
                "Long-format analysis-ready CSV with cluster, time/fraction, outcome, and fixed-effect variables.",
                "Fixed-effect formula plus proposed random-effect structure and ML/REML decision.",
                "Validated fixed-effect table with 95% CI and P values.",
                "Variance components, ICC, convergence diagnostics, residual plots, and singular-fit notes.",
            ],
            manuscript_boundary=(
                "Treat mixed-effects estimates, variance components, and ICC as exploratory until the cluster structure, "
                "random-effect specification, convergence, and residual diagnostics have been independently reviewed."
            ),
            reviewer_focus=(
                "Reviewer should verify cluster count, repeated observations, random-effect structure, convergence, "
                "residual diagnostics, ICC, and sample-size limits before accepting mixed-model inference."
            ),
        )

    def _build_cox_ph_fit_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        rows: list[dict[str, str]],
        time_column: str,
        event_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
        confirmation: FormalTestConfirmation,
        confirmation_warning: str | None = None,
    ) -> AdvancedModelFitReport:
        fit = self._fit_cox_ph(
            rows=rows,
            time_column=time_column,
            event_column=event_column,
            numeric_predictors=numeric_predictors,
            group_column=group_column,
        )
        warnings = list(fit["warnings"])
        if confirmation_warning:
            warnings.append(confirmation_warning)
        if fit["complete_case_count"] < 30:
            warnings.append("Complete-case sample size is small for Cox survival analysis; hazard ratios are exploratory.")
        if fit["event_count"] < 10:
            warnings.append("Event count is low; hazard-ratio estimates require cautious review.")
        if protocol.statistical_plan.strip():
            warnings.append("Confirm that this Cox-style model matches the pre-specified statistical plan.")
        else:
            warnings.append("The project protocol does not yet contain a finalized survival model specification.")
        method_version = str(fit.get("method_version") or "advanced-cox-v1")
        if method_version == "advanced-cox-statsmodels-v1":
            warnings.append(
                "This Cox model fit uses statsmodels PHReg; proportional hazards diagnostics and external statistical review are still required."
            )
        else:
            warnings.append("This prototype uses a Cox partial-likelihood approximation and does not replace validated survival software.")

        predictor_text = ", ".join(fit["predictor_columns"]) if fit["predictor_columns"] else "no predictors"
        methods_draft = (
            f"An exploratory Cox proportional hazards model was fitted using {time_column} as follow-up time "
            f"and {event_column} as the event indicator from complete-case records in {file_name}. "
            f"Candidate predictors were {predictor_text}. Numeric predictors were standardized, categorical "
            "predictors were represented with indicator variables, and hazard ratios are provisional pending "
            "manual review of event coding, censoring definitions, proportional hazards assumptions, and model diagnostics."
        )
        result_terms = [
            f"{coefficient.term}: HR={coefficient.estimate}"
            + (
                f", 95% CI {coefficient.confidence_interval_low} to {coefficient.confidence_interval_high}"
                if coefficient.confidence_interval_low is not None and coefficient.confidence_interval_high is not None
                else ""
            )
            + (
                f", P={self._format_p_value(coefficient.p_value)}"
                if coefficient.p_value is not None
                else ""
            )
            for coefficient in fit["coefficients"]
        ][:4]
        results_draft = (
            f"The exploratory Cox model included {fit['complete_case_count']} complete cases and "
            f"{fit['event_count']} event(s). "
            + (
                f"Key hazard-ratio estimates were: {'; '.join(result_terms)}."
                if result_terms
                else "No hazard-ratio estimates were available for reporting."
            )
            + " These results require manual statistical review before manuscript-level inference."
        )
        diagnostic_handoff = self._build_cox_diagnostic_handoff(
            fit=fit,
            time_column=time_column,
            event_column=event_column,
            method_version=method_version,
        )
        audit_summary = (
            f"已执行 exploratory Cox survival analysis：{fit['complete_case_count']} 个完整病例，"
            f"{fit['event_count']} 个事件，{len(fit['predictor_columns'])} 个预测字段；未保存原始 CSV。"
        )
        return AdvancedModelFitReport(
            project_id=project.id,
            file_name=file_name,
            model_id="cox_ph",
            model_name="Cox proportional hazards model",
            outcome_column=f"{time_column} + {event_column}",
            predictor_columns=fit["predictor_columns"],
            row_count=len(rows),
            complete_case_count=fit["complete_case_count"],
            excluded_row_count=len(rows) - fit["complete_case_count"],
            degrees_of_freedom=fit["degrees_of_freedom"],
            r_squared=None,
            adjusted_r_squared=None,
            coefficients=fit["coefficients"],
            methods_draft=methods_draft,
            results_draft=results_draft,
            warnings=warnings,
            diagnostic_handoff=diagnostic_handoff,
            confirmation=confirmation,
            method_version=method_version,
            raw_csv_saved=False,
            audit_summary=audit_summary,
            next_step="把 hazard ratio、事件数、删失定义和比例风险假设交给 Alex Writer 前，请先完成人工统计复核。",
        )

    def _build_mixed_effects_fit_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str,
        confirmation: FormalTestConfirmation,
        confirmation_warning: str | None = None,
    ) -> AdvancedModelFitReport:
        fit = self._fit_mixed_effects(
            rows=rows,
            outcome_column=outcome_column,
            numeric_predictors=numeric_predictors,
            group_column=group_column,
        )
        warnings = list(fit["warnings"])
        if confirmation_warning:
            warnings.append(confirmation_warning)
        if fit["cluster_count"] < 5:
            warnings.append("Cluster count is small; random-effect variance estimates are unstable.")
        if fit["singleton_cluster_count"]:
            warnings.append(
                f"{fit['singleton_cluster_count']} cluster(s) have only one complete record; repeated-measures adequacy requires review."
            )
        if protocol.statistical_plan.strip():
            warnings.append("Confirm that this mixed-effects route matches the pre-specified statistical plan.")
        else:
            warnings.append("The project protocol does not yet contain a finalized mixed-effects model specification.")
        method_version = str(fit.get("method_version") or "advanced-mixed-effects-v1")
        if method_version == "advanced-mixed-effects-statsmodels-v1":
            warnings.append(
                "This mixed-effects model fit uses statsmodels MixedLM; convergence, residual diagnostics, and random-effects specification still require review."
            )
        else:
            warnings.append(
                "This is a lightweight clustered linear approximation and does not replace validated mixed-effects software."
            )

        predictor_text = ", ".join(fit["predictor_columns"]) if fit["predictor_columns"] else "fixed intercept only"
        result_terms = [
            f"{coefficient.term}: beta={coefficient.estimate}"
            + (
                f", 95% CI {coefficient.confidence_interval_low} to {coefficient.confidence_interval_high}"
                if coefficient.confidence_interval_low is not None and coefficient.confidence_interval_high is not None
                else ""
            )
            + (
                f", P={self._format_p_value(coefficient.p_value)}"
                if coefficient.p_value is not None
                else ""
            )
            for coefficient in fit["coefficients"]
            if coefficient.term != "Intercept" and not coefficient.term.startswith("Approximate")
        ][:4]
        if method_version == "advanced-mixed-effects-statsmodels-v1":
            methods_draft = (
                f"An exploratory linear mixed-effects model was fitted for {outcome_column} using {group_column} "
                f"as a random-intercept grouping variable from complete-case records in {file_name}. Fixed-effect "
                f"candidate predictors were {predictor_text}. The fit used statsmodels MixedLM with maximum "
                "likelihood; convergence, residual diagnostics, and random-effects specification require manual review."
            )
        else:
            methods_draft = (
                f"An exploratory clustered linear mixed-effects approximation was fitted for {outcome_column} "
                f"using {group_column} as the candidate random-intercept grouping variable from complete-case "
                f"records in {file_name}. Fixed-effect candidate predictors were {predictor_text}. The current "
                "prototype estimates fixed effects with a linear model and summarizes residual clustering as an "
                "approximate intraclass-correlation signal; formal mixed-effects inference requires validated "
                "maximum-likelihood or restricted-maximum-likelihood software."
            )
        results_draft = (
            f"The exploratory clustered model included {fit['complete_case_count']} complete cases across "
            f"{fit['cluster_count']} cluster(s), with median cluster size {fit['median_cluster_size']} and "
            f"approximate residual ICC={fit['approximate_icc']}. "
            + (
                f"Key fixed-effect estimates were: {'; '.join(result_terms)}."
                if result_terms
                else "No non-intercept fixed-effect estimates were available for reporting."
            )
            + " These results require manual statistical review before manuscript-level inference."
        )
        diagnostic_handoff = self._build_mixed_effects_diagnostic_handoff(
            fit=fit,
            outcome_column=outcome_column,
            group_column=group_column,
            method_version=method_version,
        )
        audit_summary = (
            f"已执行 exploratory mixed-effects model：{fit['complete_case_count']} 个完整病例，"
            f"{fit['cluster_count']} 个 cluster，{len(fit['predictor_columns'])} 个预测字段；未保存原始 CSV。"
        )
        return AdvancedModelFitReport(
            project_id=project.id,
            file_name=file_name,
            model_id="mixed_effects",
            model_name=(
                "Linear mixed-effects model"
                if method_version == "advanced-mixed-effects-statsmodels-v1"
                else "Linear mixed-effects exploratory approximation"
            ),
            outcome_column=outcome_column,
            predictor_columns=fit["predictor_columns"],
            row_count=len(rows),
            complete_case_count=fit["complete_case_count"],
            excluded_row_count=len(rows) - fit["complete_case_count"],
            degrees_of_freedom=fit["degrees_of_freedom"],
            r_squared=fit["r_squared"],
            adjusted_r_squared=fit["adjusted_r_squared"],
            coefficients=fit["coefficients"],
            methods_draft=methods_draft,
            results_draft=results_draft,
            warnings=warnings,
            diagnostic_handoff=diagnostic_handoff,
            confirmation=confirmation,
            method_version=method_version,
            raw_csv_saved=False,
            audit_summary=audit_summary,
            next_step="把 fixed effects、cluster 结构、ICC 信号和随机效应设定交给 Alex Writer 前，请先完成人工统计复核。",
        )

    def _fit_linear_regression(
        self,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
    ) -> dict[str, object]:
        group_levels = sorted(
            {
                row.get(group_column, "").strip()
                for row in rows
                if group_column and row.get(group_column, "").strip().lower() not in MISSING_TOKENS
            }
        )
        group_reference = group_levels[0] if group_levels else None
        encoded_group_levels = group_levels[1:] if group_reference else []
        term_names = [
            "Intercept",
            *numeric_predictors,
            *[f"{group_column}={level}" for level in encoded_group_levels],
        ]
        predictor_columns = [
            *numeric_predictors,
            *([group_column] if group_column else []),
        ]
        design_matrix: list[list[float]] = []
        outcome_values: list[float] = []
        for row in rows:
            outcome_value = self._parse_float(row.get(outcome_column, ""))
            if outcome_value is None:
                continue
            predictor_values: list[float] = [1.0]
            skip_row = False
            for predictor in numeric_predictors:
                predictor_value = self._parse_float(row.get(predictor, ""))
                if predictor_value is None:
                    skip_row = True
                    break
                predictor_values.append(predictor_value)
            if skip_row:
                continue
            if group_column and group_reference:
                group_value = row.get(group_column, "").strip()
                if group_value.lower() in MISSING_TOKENS:
                    continue
                predictor_values.extend(1.0 if group_value == level else 0.0 for level in encoded_group_levels)
            design_matrix.append(predictor_values)
            outcome_values.append(outcome_value)

        complete_case_count = len(outcome_values)
        parameter_count = len(term_names)
        if complete_case_count <= parameter_count:
            raise ValueError("完整病例数量不足以拟合线性回归模型。")

        xtx = self._matrix_xtx(design_matrix)
        xty = self._matrix_xty(design_matrix, outcome_values)
        inverse_xtx = self._invert_matrix(xtx)
        coefficients_raw = self._matrix_vector_multiply(inverse_xtx, xty)
        fitted_values = [
            sum(value * coefficients_raw[index] for index, value in enumerate(row))
            for row in design_matrix
        ]
        residuals = [
            outcome_values[index] - fitted_values[index]
            for index in range(complete_case_count)
        ]
        y_mean = fmean(outcome_values)
        ss_residual = sum(residual ** 2 for residual in residuals)
        ss_total = sum((value - y_mean) ** 2 for value in outcome_values)
        degrees_of_freedom = complete_case_count - parameter_count
        residual_variance = ss_residual / degrees_of_freedom if degrees_of_freedom > 0 else 0.0
        r_squared = 1 - ss_residual / ss_total if ss_total > 0 else 0.0
        adjusted_r_squared = (
            1 - (1 - r_squared) * (complete_case_count - 1) / degrees_of_freedom
            if degrees_of_freedom > 0 and complete_case_count > 1
            else None
        )
        t_critical = self._student_t_critical_975(degrees_of_freedom)
        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            estimate = coefficients_raw[index]
            standard_error = sqrt(max(residual_variance * inverse_xtx[index][index], 0.0))
            statistic = estimate / standard_error if standard_error > 0 else None
            p_value = (
                self._student_t_two_sided_p_value(statistic, degrees_of_freedom)
                if statistic is not None and degrees_of_freedom > 0
                else None
            )
            ci_low = estimate - t_critical * standard_error if t_critical is not None else None
            ci_high = estimate + t_critical * standard_error if t_critical is not None else None
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(estimate, 4),
                    standard_error=round(standard_error, 4),
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=(
                        "Exploratory intercept estimate."
                        if term == "Intercept"
                        else f"Holding other included predictors constant, {term} is associated with an estimated change of {round(estimate, 4)} in {outcome_column}."
                    ),
                )
            )

        warnings: list[str] = []
        if group_column and group_reference:
            warnings.append(f"{group_column} reference level: {group_reference}.")
        if len(numeric_predictors) > 3:
            warnings.append("Multiple numeric predictors were included; collinearity should be reviewed.")
        return {
            "complete_case_count": complete_case_count,
            "degrees_of_freedom": degrees_of_freedom,
            "predictor_columns": predictor_columns,
            "r_squared": round(r_squared, 4),
            "adjusted_r_squared": round(adjusted_r_squared, 4) if adjusted_r_squared is not None else None,
            "coefficients": coefficients,
            "warnings": warnings,
        }

    def _fit_mixed_effects(
        self,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str,
    ) -> dict[str, object]:
        if StatsmodelsMixedLM is not None and statsmodels_np is not None:
            try:
                return self._fit_statsmodels_mixed_effects(
                    rows=rows,
                    outcome_column=outcome_column,
                    numeric_predictors=numeric_predictors,
                    group_column=group_column,
                )
            except Exception as exc:
                fallback_fit = self._fit_mixed_effects_approximation(
                    rows=rows,
                    outcome_column=outcome_column,
                    numeric_predictors=numeric_predictors,
                    group_column=group_column,
                )
                detail = str(exc).strip() or exc.__class__.__name__
                if len(detail) > 180:
                    detail = f"{detail[:177]}..."
                fallback_fit["warnings"].append(
                    f"statsmodels MixedLM failed ({exc.__class__.__name__}: {detail}); used clustered linear approximation fallback."
                )
                return fallback_fit
        return self._fit_mixed_effects_approximation(
            rows=rows,
            outcome_column=outcome_column,
            numeric_predictors=numeric_predictors,
            group_column=group_column,
        )

    def _fit_statsmodels_mixed_effects(
        self,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str,
    ) -> dict[str, object]:
        if StatsmodelsMixedLM is None or statsmodels_np is None:
            raise RuntimeError("statsmodels MixedLM is not available.")

        def finite_float(value: object) -> float | None:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return None
            return numeric if isfinite(numeric) else None

        term_names = ["Intercept", *numeric_predictors]
        design_matrix: list[list[float]] = []
        outcome_values: list[float] = []
        group_values: list[str] = []
        for row in rows:
            outcome_value = self._parse_float(row.get(outcome_column, ""))
            group_value = row.get(group_column, "").strip()
            if outcome_value is None or group_value.lower() in MISSING_TOKENS:
                continue
            predictor_values: list[float] = [1.0]
            skip_row = False
            for predictor in numeric_predictors:
                predictor_value = self._parse_float(row.get(predictor, ""))
                if predictor_value is None:
                    skip_row = True
                    break
                predictor_values.append(predictor_value)
            if skip_row:
                continue
            design_matrix.append(predictor_values)
            outcome_values.append(outcome_value)
            group_values.append(group_value)

        complete_case_count = len(outcome_values)
        parameter_count = len(term_names)
        cluster_counts = Counter(group_values)
        cluster_count = len(cluster_counts)
        if cluster_count < 2:
            raise ValueError("mixed-effects model needs at least two clusters.")
        if max(cluster_counts.values()) < 2:
            raise ValueError("mixed-effects model needs at least one cluster with repeated observations.")
        if complete_case_count <= parameter_count:
            raise ValueError("Complete-case count is too small for mixed-effects fitting.")

        endog = statsmodels_np.asarray(outcome_values, dtype=float)
        exog = statsmodels_np.asarray(design_matrix, dtype=float)
        groups = statsmodels_np.asarray(group_values)
        captured_warning_texts: list[str] = []
        with py_warnings.catch_warnings(record=True) as captured_warnings:
            py_warnings.simplefilter("always")
            result = StatsmodelsMixedLM(endog, exog, groups=groups).fit(
                reml=False,
                method="powell",
                disp=False,
            )
            captured_warning_texts = [str(warning.message) for warning in captured_warnings]
        if getattr(result, "converged", True) is False:
            raise RuntimeError("statsmodels MixedLM did not converge.")

        fixed_effects = [finite_float(value) for value in result.fe_params]
        standard_errors = [finite_float(value) for value in getattr(result, "bse_fe", [])]
        p_values = [finite_float(value) for value in getattr(result, "pvalues", [])]
        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            estimate = fixed_effects[index] if index < len(fixed_effects) else None
            if estimate is None:
                continue
            standard_error = standard_errors[index] if index < len(standard_errors) else None
            statistic = estimate / standard_error if standard_error and standard_error > 0 else None
            p_value = p_values[index] if index < len(p_values) else None
            if p_value is None and statistic is not None:
                p_value = self._normal_two_sided_p_value(statistic)
            ci_low = estimate - 1.96 * standard_error if standard_error is not None else None
            ci_high = estimate + 1.96 * standard_error if standard_error is not None else None
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(estimate, 4),
                    standard_error=round(standard_error, 4) if standard_error is not None else None,
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=(
                        "Statsmodels MixedLM fixed intercept estimate."
                        if term == "Intercept"
                        else f"Statsmodels MixedLM fixed-effect estimate for {term}, holding other included predictors constant."
                    ),
                )
            )
        if not coefficients:
            raise RuntimeError("statsmodels MixedLM returned no finite fixed-effect coefficients.")

        random_intercept_variance = None
        try:
            random_intercept_variance = finite_float(result.cov_re[0, 0])
        except Exception:
            try:
                random_intercept_variance = finite_float(result.cov_re.iloc[0, 0])
            except Exception:
                random_intercept_variance = None
        residual_variance = finite_float(getattr(result, "scale", None))
        if random_intercept_variance is None or random_intercept_variance < 0:
            random_intercept_variance = 0.0
        if residual_variance is None or residual_variance < 0:
            residual_variance = 0.0
        approximate_icc = (
            random_intercept_variance / (random_intercept_variance + residual_variance)
            if random_intercept_variance + residual_variance > 0
            else 0.0
        )
        coefficients.extend(
            [
                AdvancedModelCoefficient(
                    term="Random intercept variance",
                    estimate=round(random_intercept_variance, 4),
                    standard_error=None,
                    statistic=None,
                    p_value=None,
                    confidence_interval_low=None,
                    confidence_interval_high=None,
                    interpretation="Statsmodels MixedLM random-intercept variance component.",
                ),
                AdvancedModelCoefficient(
                    term="Residual variance",
                    estimate=round(residual_variance, 4),
                    standard_error=None,
                    statistic=None,
                    p_value=None,
                    confidence_interval_low=None,
                    confidence_interval_high=None,
                    interpretation="Statsmodels MixedLM residual variance estimate.",
                ),
                AdvancedModelCoefficient(
                    term="Approximate residual ICC",
                    estimate=round(approximate_icc, 4),
                    standard_error=None,
                    statistic=None,
                    p_value=None,
                    confidence_interval_low=None,
                    confidence_interval_high=None,
                    interpretation="Approximate intraclass-correlation from random-intercept and residual variance.",
                ),
            ]
        )

        cluster_sizes = sorted(cluster_counts.values())
        warnings = ["Mixed-effects model fitted with statsmodels MixedLM random intercept."]
        warnings.extend(
            f"statsmodels warning: {warning_text}"
            for warning_text in captured_warning_texts
            if warning_text
        )
        warnings.append(f"{group_column} was treated as the random-intercept grouping variable.")
        warnings.append("No random slope structure was fitted in this automated route.")
        return {
            "complete_case_count": complete_case_count,
            "degrees_of_freedom": complete_case_count - parameter_count,
            "predictor_columns": [*numeric_predictors, group_column],
            "r_squared": None,
            "adjusted_r_squared": None,
            "coefficients": coefficients,
            "warnings": warnings,
            "cluster_count": cluster_count,
            "singleton_cluster_count": sum(1 for count in cluster_sizes if count == 1),
            "median_cluster_size": round(median(cluster_sizes), 4),
            "approximate_icc": round(approximate_icc, 4),
            "method_version": "advanced-mixed-effects-statsmodels-v1",
        }

    def _fit_mixed_effects_approximation(
        self,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str,
    ) -> dict[str, object]:
        term_names = ["Intercept", *numeric_predictors]
        design_matrix: list[list[float]] = []
        outcome_values: list[float] = []
        group_values: list[str] = []
        for row in rows:
            outcome_value = self._parse_float(row.get(outcome_column, ""))
            group_value = row.get(group_column, "").strip()
            if outcome_value is None or group_value.lower() in MISSING_TOKENS:
                continue
            predictor_values: list[float] = [1.0]
            skip_row = False
            for predictor in numeric_predictors:
                predictor_value = self._parse_float(row.get(predictor, ""))
                if predictor_value is None:
                    skip_row = True
                    break
                predictor_values.append(predictor_value)
            if skip_row:
                continue
            design_matrix.append(predictor_values)
            outcome_values.append(outcome_value)
            group_values.append(group_value)

        complete_case_count = len(outcome_values)
        parameter_count = len(term_names)
        cluster_counts = Counter(group_values)
        cluster_count = len(cluster_counts)
        if cluster_count < 2:
            raise ValueError("mixed-effects model 至少需要两个 cluster。")
        if max(cluster_counts.values()) < 2:
            raise ValueError("mixed-effects model 需要至少一个 cluster 含有重复观测。")
        if complete_case_count <= parameter_count:
            raise ValueError("完整病例数量不足以拟合 mixed-effects 近似模型。")

        xtx = self._matrix_xtx(design_matrix)
        xty = self._matrix_xty(design_matrix, outcome_values)
        inverse_xtx = self._invert_matrix(xtx)
        coefficients_raw = self._matrix_vector_multiply(inverse_xtx, xty)
        fitted_values = [
            sum(value * coefficients_raw[index] for index, value in enumerate(row))
            for row in design_matrix
        ]
        residuals = [
            outcome_values[index] - fitted_values[index]
            for index in range(complete_case_count)
        ]
        y_mean = fmean(outcome_values)
        ss_residual = sum(residual ** 2 for residual in residuals)
        ss_total = sum((value - y_mean) ** 2 for value in outcome_values)
        degrees_of_freedom = complete_case_count - parameter_count
        residual_variance = ss_residual / degrees_of_freedom if degrees_of_freedom > 0 else 0.0
        r_squared = 1 - ss_residual / ss_total if ss_total > 0 else 0.0
        adjusted_r_squared = (
            1 - (1 - r_squared) * (complete_case_count - 1) / degrees_of_freedom
            if degrees_of_freedom > 0 and complete_case_count > 1
            else None
        )
        t_critical = self._student_t_critical_975(degrees_of_freedom)
        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            estimate = coefficients_raw[index]
            standard_error = sqrt(max(residual_variance * inverse_xtx[index][index], 0.0))
            statistic = estimate / standard_error if standard_error > 0 else None
            p_value = (
                self._student_t_two_sided_p_value(statistic, degrees_of_freedom)
                if statistic is not None and degrees_of_freedom > 0
                else None
            )
            ci_low = estimate - t_critical * standard_error if t_critical is not None else None
            ci_high = estimate + t_critical * standard_error if t_critical is not None else None
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(estimate, 4),
                    standard_error=round(standard_error, 4),
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=(
                        "Exploratory fixed intercept estimate."
                        if term == "Intercept"
                        else f"Exploratory fixed-effect estimate for {term}, before validated random-effects inference."
                    ),
                )
            )

        residuals_by_group: dict[str, list[float]] = defaultdict(list)
        for index, group_value in enumerate(group_values):
            residuals_by_group[group_value].append(residuals[index])
        cluster_mean_residuals = [
            fmean(group_residuals)
            for group_residuals in residuals_by_group.values()
            if group_residuals
        ]
        between_variance = stdev(cluster_mean_residuals) ** 2 if len(cluster_mean_residuals) > 1 else 0.0
        within_denominator = complete_case_count - cluster_count
        within_variance = (
            sum(
                (residual - fmean(group_residuals)) ** 2
                for group_residuals in residuals_by_group.values()
                for residual in group_residuals
            )
            / within_denominator
            if within_denominator > 0
            else 0.0
        )
        approximate_icc = (
            between_variance / (between_variance + within_variance)
            if between_variance + within_variance > 0
            else 0.0
        )
        coefficients.extend(
            [
                AdvancedModelCoefficient(
                    term="Approximate residual ICC",
                    estimate=round(approximate_icc, 4),
                    standard_error=None,
                    statistic=None,
                    p_value=None,
                    confidence_interval_low=None,
                    confidence_interval_high=None,
                    interpretation="Approximate residual intraclass-correlation signal; validate with a true mixed-effects model.",
                ),
                AdvancedModelCoefficient(
                    term="Between-cluster residual variance",
                    estimate=round(between_variance, 4),
                    standard_error=None,
                    statistic=None,
                    p_value=None,
                    confidence_interval_low=None,
                    confidence_interval_high=None,
                    interpretation="Approximate between-cluster residual variance from the clustered linear approximation.",
                ),
            ]
        )

        cluster_sizes = sorted(cluster_counts.values())
        warnings: list[str] = []
        if len(numeric_predictors) > 3:
            warnings.append("Multiple fixed-effect predictors were included; collinearity should be reviewed.")
        warnings.append(f"{group_column} was treated as the candidate random-intercept grouping variable.")
        warnings.append("No random slope structure was fitted in this prototype.")
        return {
            "complete_case_count": complete_case_count,
            "degrees_of_freedom": degrees_of_freedom,
            "predictor_columns": [*numeric_predictors, group_column],
            "r_squared": round(r_squared, 4),
            "adjusted_r_squared": round(adjusted_r_squared, 4) if adjusted_r_squared is not None else None,
            "coefficients": coefficients,
            "warnings": warnings,
            "cluster_count": cluster_count,
            "singleton_cluster_count": sum(1 for count in cluster_sizes if count == 1),
            "median_cluster_size": round(median(cluster_sizes), 4),
            "approximate_icc": round(approximate_icc, 4),
        }

    def _fit_logistic_regression(
        self,
        rows: list[dict[str, str]],
        outcome_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
    ) -> dict[str, object]:
        outcome_values = [
            row.get(outcome_column, "").strip()
            for row in rows
            if row.get(outcome_column, "").strip().lower() not in MISSING_TOKENS
        ]
        unique_outcomes = sorted(set(outcome_values))
        if outcome_column == "qa_result" and "Pass" in unique_outcomes:
            event_label = "Pass"
            non_event_label = "non-Pass"
        elif len(unique_outcomes) == 2:
            non_event_label, event_label = unique_outcomes
        else:
            raise ValueError("logistic regression 结局必须是二分类；qa_result 将按 Pass vs non-Pass 处理。")

        numeric_values: dict[str, list[float]] = {predictor: [] for predictor in numeric_predictors}
        for row in rows:
            if row.get(outcome_column, "").strip().lower() in MISSING_TOKENS:
                continue
            for predictor in numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is not None:
                    numeric_values[predictor].append(value)
        numeric_scales: dict[str, tuple[float, float]] = {}
        for predictor, values in numeric_values.items():
            if len(values) < 2:
                continue
            center = fmean(values)
            spread = stdev(values) if len(values) > 1 else 0.0
            numeric_scales[predictor] = (center, spread if spread > 0 else 1.0)

        group_levels = sorted(
            {
                row.get(group_column, "").strip()
                for row in rows
                if group_column and row.get(group_column, "").strip().lower() not in MISSING_TOKENS
            }
        )
        group_reference = group_levels[0] if group_levels else None
        encoded_group_levels = group_levels[1:] if group_reference else []
        scaled_numeric_predictors = [predictor for predictor in numeric_predictors if predictor in numeric_scales]
        term_names = [
            "Intercept",
            *[f"{predictor} (per SD)" for predictor in scaled_numeric_predictors],
            *[f"{group_column}={level}" for level in encoded_group_levels],
        ]
        predictor_columns = [
            *scaled_numeric_predictors,
            *([group_column] if group_column else []),
        ]
        design_matrix: list[list[float]] = []
        binary_outcomes: list[float] = []
        for row in rows:
            raw_outcome = row.get(outcome_column, "").strip()
            if raw_outcome.lower() in MISSING_TOKENS:
                continue
            if outcome_column == "qa_result":
                outcome_value = 1.0 if raw_outcome == event_label else 0.0
            elif raw_outcome == event_label:
                outcome_value = 1.0
            elif raw_outcome == non_event_label:
                outcome_value = 0.0
            else:
                continue
            predictor_values: list[float] = [1.0]
            skip_row = False
            for predictor in scaled_numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is None:
                    skip_row = True
                    break
                center, spread = numeric_scales[predictor]
                predictor_values.append((value - center) / spread)
            if skip_row:
                continue
            if group_column and group_reference:
                group_value = row.get(group_column, "").strip()
                if group_value.lower() in MISSING_TOKENS:
                    continue
                predictor_values.extend(1.0 if group_value == level else 0.0 for level in encoded_group_levels)
            design_matrix.append(predictor_values)
            binary_outcomes.append(outcome_value)

        complete_case_count = len(binary_outcomes)
        event_count = int(sum(binary_outcomes))
        parameter_count = len(term_names)
        if complete_case_count <= parameter_count:
            raise ValueError("完整病例数量不足以拟合 logistic regression。")
        if event_count == 0 or event_count == complete_case_count:
            raise ValueError("logistic regression 结局没有同时包含事件和非事件。")

        coefficients_raw = [0.0 for _ in term_names]
        inverse_information: list[list[float]] | None = None
        converged = False
        ridge = 1e-6
        for _iteration in range(50):
            probabilities = [
                self._logistic_probability(sum(value * coefficients_raw[index] for index, value in enumerate(row)))
                for row in design_matrix
            ]
            weights = [max(probability * (1 - probability), 1e-6) for probability in probabilities]
            z_values = [
                sum(value * coefficients_raw[index] for index, value in enumerate(row))
                + (binary_outcomes[row_index] - probabilities[row_index]) / weights[row_index]
                for row_index, row in enumerate(design_matrix)
            ]
            information = [
                [
                    sum(weights[row_index] * row[first] * row[second] for row_index, row in enumerate(design_matrix))
                    + (ridge if first == second else 0.0)
                    for second in range(parameter_count)
                ]
                for first in range(parameter_count)
            ]
            target = [
                sum(weights[row_index] * design_matrix[row_index][column_index] * z_values[row_index] for row_index in range(complete_case_count))
                for column_index in range(parameter_count)
            ]
            inverse_information = self._invert_matrix(information)
            next_coefficients = self._matrix_vector_multiply(inverse_information, target)
            delta = max(abs(next_coefficients[index] - coefficients_raw[index]) for index in range(parameter_count))
            coefficients_raw = next_coefficients
            if delta < 1e-6:
                converged = True
                break

        if inverse_information is None:
            raise ValueError("logistic regression 未能生成可用的信息矩阵。")

        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            log_odds = coefficients_raw[index]
            standard_error = sqrt(max(inverse_information[index][index], 0.0))
            statistic = log_odds / standard_error if standard_error > 0 else None
            p_value = self._normal_two_sided_p_value(statistic) if statistic is not None else None
            ci_low = self._safe_exp(log_odds - 1.96 * standard_error) if standard_error > 0 else None
            ci_high = self._safe_exp(log_odds + 1.96 * standard_error) if standard_error > 0 else None
            odds_ratio = self._safe_exp(log_odds)
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(odds_ratio, 4),
                    standard_error=round(standard_error, 4),
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=(
                        "Exploratory intercept odds."
                        if term == "Intercept"
                        else f"Adjusted odds ratio for {event_label} versus {non_event_label}, holding other included predictors constant."
                    ),
                )
            )

        warnings: list[str] = []
        if outcome_column == "qa_result":
            warnings.append("qa_result was recoded as Pass versus non-Pass for this prototype logistic model.")
        if group_column and group_reference:
            warnings.append(f"{group_column} reference level: {group_reference}.")
        if not converged:
            warnings.append("IRLS did not fully converge within the iteration limit; estimates require review.")
        warnings.append("Numeric predictors were standardized; odds ratios are per one standard deviation increase.")
        if any(abs(coefficient) > 20 for coefficient in coefficients_raw):
            warnings.append("One or more log-odds estimates were very large; possible separation or sparse cells require review.")
        return {
            "complete_case_count": complete_case_count,
            "event_count": event_count,
            "degrees_of_freedom": complete_case_count - parameter_count,
            "predictor_columns": predictor_columns,
            "event_label": event_label,
            "non_event_label": non_event_label,
            "coefficients": coefficients,
            "warnings": warnings,
        }

    def _fit_cox_ph(
        self,
        rows: list[dict[str, str]],
        time_column: str,
        event_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
    ) -> dict[str, object]:
        if StatsmodelsPHReg is not None:
            try:
                return self._fit_statsmodels_cox_ph(
                    rows=rows,
                    time_column=time_column,
                    event_column=event_column,
                    numeric_predictors=numeric_predictors,
                    group_column=group_column,
                )
            except Exception as exc:
                fallback_fit = self._fit_cox_ph_approximation(
                    rows=rows,
                    time_column=time_column,
                    event_column=event_column,
                    numeric_predictors=numeric_predictors,
                    group_column=group_column,
                )
                detail = str(exc).strip() or exc.__class__.__name__
                if len(detail) > 180:
                    detail = f"{detail[:177]}..."
                fallback_fit["warnings"].append(
                    f"statsmodels PHReg failed ({exc.__class__.__name__}: {detail}); used internal Cox approximation fallback."
                )
                return fallback_fit
        return self._fit_cox_ph_approximation(
            rows=rows,
            time_column=time_column,
            event_column=event_column,
            numeric_predictors=numeric_predictors,
            group_column=group_column,
        )

    def _fit_cox_ph_approximation(
        self,
        rows: list[dict[str, str]],
        time_column: str,
        event_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
    ) -> dict[str, object]:
        valid_rows = []
        for row in rows:
            follow_up_time = self._parse_float(row.get(time_column, ""))
            event_value = self._parse_survival_event(row.get(event_column, ""))
            if follow_up_time is None or follow_up_time <= 0 or event_value is None:
                continue
            valid_rows.append((row, follow_up_time, event_value))

        numeric_values: dict[str, list[float]] = {predictor: [] for predictor in numeric_predictors}
        for row, _follow_up_time, _event_value in valid_rows:
            for predictor in numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is not None:
                    numeric_values[predictor].append(value)
        numeric_scales: dict[str, tuple[float, float]] = {}
        for predictor, values in numeric_values.items():
            if len(values) < 2:
                continue
            center = fmean(values)
            spread = stdev(values) if len(values) > 1 else 0.0
            numeric_scales[predictor] = (center, spread if spread > 0 else 1.0)

        group_levels = sorted(
            {
                row.get(group_column, "").strip()
                for row, _follow_up_time, _event_value in valid_rows
                if group_column and row.get(group_column, "").strip().lower() not in MISSING_TOKENS
            }
        )
        group_reference = group_levels[0] if group_levels else None
        encoded_group_levels = group_levels[1:] if group_reference else []
        scaled_numeric_predictors = [predictor for predictor in numeric_predictors if predictor in numeric_scales]
        term_names = [
            *[f"{predictor} (per SD)" for predictor in scaled_numeric_predictors],
            *[f"{group_column}={level}" for level in encoded_group_levels],
        ]
        predictor_columns = [
            *scaled_numeric_predictors,
            *([group_column] if group_column and group_reference else []),
        ]
        if not term_names:
            raise ValueError("Cox survival analysis 至少需要一个可编码的预测变量。")

        survival_rows: list[tuple[float, float, list[float]]] = []
        for row, follow_up_time, event_value in valid_rows:
            predictor_values: list[float] = []
            skip_row = False
            for predictor in scaled_numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is None:
                    skip_row = True
                    break
                center, spread = numeric_scales[predictor]
                predictor_values.append((value - center) / spread)
            if skip_row:
                continue
            if group_column and group_reference:
                group_value = row.get(group_column, "").strip()
                if group_value.lower() in MISSING_TOKENS:
                    continue
                predictor_values.extend(1.0 if group_value == level else 0.0 for level in encoded_group_levels)
            survival_rows.append((follow_up_time, event_value, predictor_values))

        complete_case_count = len(survival_rows)
        event_count = int(sum(event_value for _time, event_value, _predictors in survival_rows))
        parameter_count = len(term_names)
        if complete_case_count <= parameter_count:
            raise ValueError("完整病例数量不足以拟合 Cox survival analysis。")
        if event_count == 0:
            raise ValueError("Cox survival analysis 事件字段没有可识别事件。")
        if event_count <= parameter_count:
            raise ValueError("Cox survival analysis 事件数不足以支持当前预测变量数量。")

        coefficients_raw = [0.0 for _term in term_names]
        inverse_information: list[list[float]] | None = None
        converged = False
        ridge = 1e-6
        event_rows = [row for row in survival_rows if row[1] == 1.0]
        for _iteration in range(50):
            score = [0.0 for _term in term_names]
            information = [
                [0.0 for _term in term_names]
                for _term in term_names
            ]
            for event_time, _event_value, event_predictors in event_rows:
                risk_set = [
                    (time_value, predictors)
                    for time_value, _row_event, predictors in survival_rows
                    if time_value >= event_time
                ]
                if not risk_set:
                    continue
                weights = [
                    self._safe_exp(sum(predictor * coefficients_raw[index] for index, predictor in enumerate(predictors)))
                    for _time_value, predictors in risk_set
                ]
                denominator = sum(weights)
                if denominator <= 0:
                    continue
                weighted_mean = [
                    sum(weights[row_index] * predictors[index] for row_index, (_time_value, predictors) in enumerate(risk_set))
                    / denominator
                    for index in range(parameter_count)
                ]
                weighted_second = [
                    [
                        sum(
                            weights[row_index] * predictors[first] * predictors[second]
                            for row_index, (_time_value, predictors) in enumerate(risk_set)
                        )
                        / denominator
                        for second in range(parameter_count)
                    ]
                    for first in range(parameter_count)
                ]
                for index in range(parameter_count):
                    score[index] += event_predictors[index] - weighted_mean[index]
                    for second in range(parameter_count):
                        information[index][second] += (
                            weighted_second[index][second] - weighted_mean[index] * weighted_mean[second]
                        )
            for index in range(parameter_count):
                information[index][index] += ridge
            try:
                inverse_information = self._invert_matrix(information)
            except ValueError as exc:
                raise ValueError("Cox survival model 信息矩阵不可逆，请减少预测变量或合并稀疏分组。") from exc
            step = self._matrix_vector_multiply(inverse_information, score)
            max_step = max(abs(value) for value in step) if step else 0.0
            if max_step > 1:
                step = [value / max_step for value in step]
                max_step = 1.0
            coefficients_raw = [
                coefficients_raw[index] + step[index]
                for index in range(parameter_count)
            ]
            if max_step < 1e-6:
                converged = True
                break

        if inverse_information is None:
            raise ValueError("Cox survival model 未能生成可用的信息矩阵。")

        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            log_hazard = coefficients_raw[index]
            standard_error = sqrt(max(inverse_information[index][index], 0.0))
            statistic = log_hazard / standard_error if standard_error > 0 else None
            p_value = self._normal_two_sided_p_value(statistic) if statistic is not None else None
            ci_low = self._safe_exp(log_hazard - 1.96 * standard_error) if standard_error > 0 else None
            ci_high = self._safe_exp(log_hazard + 1.96 * standard_error) if standard_error > 0 else None
            hazard_ratio = self._safe_exp(log_hazard)
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(hazard_ratio, 4),
                    standard_error=round(standard_error, 4),
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=(
                        f"Exploratory hazard ratio for {term}, holding other included predictors constant."
                    ),
                )
            )

        warnings: list[str] = []
        if group_column and group_reference:
            warnings.append(f"{group_column} reference level: {group_reference}.")
        if not converged:
            warnings.append("Cox partial-likelihood iteration did not fully converge within the iteration limit.")
        if len({time_value for time_value, event_value, _predictors in survival_rows if event_value == 1.0}) < event_count:
            warnings.append("Tied event times were detected; this prototype uses an approximate handling of ties.")
        if event_count == complete_case_count:
            warnings.append("No censored records were detected; confirm that event coding and censoring are correct.")
        warnings.append("Numeric predictors were standardized; hazard ratios are per one standard deviation increase.")
        return {
            "complete_case_count": complete_case_count,
            "event_count": event_count,
            "degrees_of_freedom": event_count - parameter_count,
            "predictor_columns": predictor_columns,
            "coefficients": coefficients,
            "warnings": warnings,
            "method_version": "advanced-cox-v1",
        }

    def _fit_statsmodels_cox_ph(
        self,
        rows: list[dict[str, str]],
        time_column: str,
        event_column: str,
        numeric_predictors: list[str],
        group_column: str | None,
    ) -> dict[str, object]:
        if StatsmodelsPHReg is None or statsmodels_np is None:
            raise RuntimeError("statsmodels PHReg is not available.")

        def finite_float(value: object) -> float | None:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return None
            return numeric if isfinite(numeric) else None

        valid_rows = []
        for row in rows:
            follow_up_time = self._parse_float(row.get(time_column, ""))
            event_value = self._parse_survival_event(row.get(event_column, ""))
            if follow_up_time is None or follow_up_time <= 0 or event_value is None:
                continue
            valid_rows.append((row, follow_up_time, event_value))

        numeric_values: dict[str, list[float]] = {predictor: [] for predictor in numeric_predictors}
        for row, _follow_up_time, _event_value in valid_rows:
            for predictor in numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is not None:
                    numeric_values[predictor].append(value)
        numeric_scales: dict[str, tuple[float, float]] = {}
        for predictor, values in numeric_values.items():
            if len(values) < 2:
                continue
            center = fmean(values)
            spread = stdev(values) if len(values) > 1 else 0.0
            numeric_scales[predictor] = (center, spread if spread > 0 else 1.0)

        group_levels = sorted(
            {
                row.get(group_column, "").strip()
                for row, _follow_up_time, _event_value in valid_rows
                if group_column and row.get(group_column, "").strip().lower() not in MISSING_TOKENS
            }
        )
        group_reference = group_levels[0] if group_levels else None
        encoded_group_levels = group_levels[1:] if group_reference else []
        scaled_numeric_predictors = [predictor for predictor in numeric_predictors if predictor in numeric_scales]
        term_names = [
            *[f"{predictor} (per SD)" for predictor in scaled_numeric_predictors],
            *[f"{group_column}={level}" for level in encoded_group_levels],
        ]
        predictor_columns = [
            *scaled_numeric_predictors,
            *([group_column] if group_column and group_reference else []),
        ]
        if not term_names:
            raise ValueError("Cox survival analysis needs at least one encodable predictor.")

        survival_rows: list[tuple[float, float, list[float]]] = []
        for row, follow_up_time, event_value in valid_rows:
            predictor_values: list[float] = []
            skip_row = False
            for predictor in scaled_numeric_predictors:
                value = self._parse_float(row.get(predictor, ""))
                if value is None:
                    skip_row = True
                    break
                center, spread = numeric_scales[predictor]
                predictor_values.append((value - center) / spread)
            if skip_row:
                continue
            if group_column and group_reference:
                group_value = row.get(group_column, "").strip()
                if group_value.lower() in MISSING_TOKENS:
                    continue
                predictor_values.extend(1.0 if group_value == level else 0.0 for level in encoded_group_levels)
            survival_rows.append((follow_up_time, event_value, predictor_values))

        complete_case_count = len(survival_rows)
        event_count = int(sum(event_value for _time, event_value, _predictors in survival_rows))
        parameter_count = len(term_names)
        if complete_case_count <= parameter_count:
            raise ValueError("Complete-case count is too small for Cox survival analysis.")
        if event_count == 0:
            raise ValueError("Cox survival analysis did not detect any events.")
        if event_count <= parameter_count:
            raise ValueError("Event count is too small for the selected Cox predictors.")

        follow_up_times = statsmodels_np.asarray(
            [time_value for time_value, _event_value, _predictors in survival_rows],
            dtype=float,
        )
        event_status = statsmodels_np.asarray(
            [event_value for _time_value, event_value, _predictors in survival_rows],
            dtype=float,
        )
        design_matrix = statsmodels_np.asarray(
            [predictors for _time_value, _event_value, predictors in survival_rows],
            dtype=float,
        )
        result = StatsmodelsPHReg(
            follow_up_times,
            design_matrix,
            status=event_status,
            ties="breslow",
        ).fit(disp=False)

        params = [finite_float(value) for value in result.params]
        standard_errors = [finite_float(value) for value in result.bse]
        p_values = [finite_float(value) for value in result.pvalues]
        try:
            confidence_intervals = result.conf_int()
        except Exception:
            confidence_intervals = None

        coefficients: list[AdvancedModelCoefficient] = []
        for index, term in enumerate(term_names):
            log_hazard = params[index] if index < len(params) else None
            if log_hazard is None:
                continue
            standard_error = standard_errors[index] if index < len(standard_errors) else None
            statistic = log_hazard / standard_error if standard_error and standard_error > 0 else None
            p_value = p_values[index] if index < len(p_values) else None
            if p_value is None and statistic is not None:
                p_value = self._normal_two_sided_p_value(statistic)
            ci_low = None
            ci_high = None
            if confidence_intervals is not None:
                try:
                    interval = confidence_intervals[index]
                except Exception:
                    interval = None
                if interval is not None and len(interval) >= 2:
                    ci_low_log = finite_float(interval[0])
                    ci_high_log = finite_float(interval[1])
                    ci_low = self._safe_exp(ci_low_log) if ci_low_log is not None else None
                    ci_high = self._safe_exp(ci_high_log) if ci_high_log is not None else None
            coefficients.append(
                AdvancedModelCoefficient(
                    term=term,
                    estimate=round(self._safe_exp(log_hazard), 4),
                    standard_error=round(standard_error, 4) if standard_error is not None else None,
                    statistic=round(statistic, 4) if statistic is not None else None,
                    p_value=round(p_value, 6) if p_value is not None else None,
                    confidence_interval_low=round(ci_low, 4) if ci_low is not None else None,
                    confidence_interval_high=round(ci_high, 4) if ci_high is not None else None,
                    interpretation=f"Statsmodels PHReg hazard ratio for {term}, holding other included predictors constant.",
                )
            )
        if not coefficients:
            raise RuntimeError("statsmodels PHReg returned no finite coefficients.")

        warnings: list[str] = ["Cox model fitted with statsmodels PHReg using Breslow tie handling."]
        if group_column and group_reference:
            warnings.append(f"{group_column} reference level: {group_reference}.")
        if len({time_value for time_value, event_value, _predictors in survival_rows if event_value == 1.0}) < event_count:
            warnings.append("Tied event times were detected; Breslow tie handling was used.")
        if event_count == complete_case_count:
            warnings.append("No censored records were detected; confirm that event coding and censoring are correct.")
        warnings.append("Numeric predictors were standardized; hazard ratios are per one standard deviation increase.")
        return {
            "complete_case_count": complete_case_count,
            "event_count": event_count,
            "degrees_of_freedom": event_count - parameter_count,
            "predictor_columns": predictor_columns,
            "coefficients": coefficients,
            "warnings": warnings,
            "method_version": "advanced-cox-statsmodels-v1",
        }

    def _logistic_probability(self, value: float) -> float:
        if value >= 0:
            denominator = 1 + exp(-value)
            return min(max(1 / denominator, 1e-6), 1 - 1e-6)
        exp_value = exp(value)
        return min(max(exp_value / (1 + exp_value), 1e-6), 1 - 1e-6)

    def _safe_exp(self, value: float) -> float:
        return exp(min(max(value, -30), 30))

    def _has_repeated_measure_signal(
        self,
        headers: list[str],
        columns: list[DataColumnQuality],
        rows: list[dict[str, str]],
    ) -> bool:
        repeated_tokens = [
            "fractionindex",
            "fractionnumber",
            "fractionno",
            "timepoint",
            "visit",
            "session",
            "measurementindex",
            "repeatindex",
            "longitudinal",
        ]
        has_repeated_field = any(
            any(token in self._normalize(header) for token in repeated_tokens)
            for header in headers
        )
        return has_repeated_field and bool(self._select_mixed_effects_group_column(headers, columns, rows, None))

    def _select_mixed_effects_group_column(
        self,
        headers: list[str],
        columns: list[DataColumnQuality],
        rows: list[dict[str, str]],
        requested_group_column: str | None,
    ) -> str | None:
        column_by_name = {column.name: column for column in columns}
        header_order = {header: index for index, header in enumerate(headers)}
        candidates: list[tuple[int, int, str]] = []
        for header in headers:
            column = column_by_name.get(header)
            if not column or column.inferred_type == "empty":
                continue
            values = [
                row.get(header, "").strip()
                for row in rows
                if row.get(header, "").strip().lower() not in MISSING_TOKENS
            ]
            if not values:
                continue
            counts = Counter(values)
            unique_count = len(counts)
            max_cluster_size = max(counts.values())
            if unique_count < 2 or max_cluster_size < 2:
                continue
            if unique_count > max(2, int(len(values) * 0.75)):
                continue
            if column.inferred_type == "numeric" and header != requested_group_column:
                continue
            normalized = self._normalize(header)
            score = 0
            if requested_group_column and header == requested_group_column:
                score += 100
            if any(token in normalized for token in ["patient", "subject", "case", "cluster", "participant"]):
                score += 12
            if any(token in normalized for token in ["id", "code", "unit"]):
                score += 5
            if any(token in normalized for token in ["site", "technique", "gender", "race"]):
                score += 1
            score += min(max_cluster_size, 6)
            score -= header_order.get(header, 0)
            candidates.append((score, -unique_count, header))
        if not candidates:
            return None
        return max(candidates)[2]

    def _select_survival_fields(
        self,
        headers: list[str],
        numeric_columns: list[str],
        columns: list[DataColumnQuality],
    ) -> tuple[str | None, str | None]:
        column_by_name = {column.name: column for column in columns}
        header_order = {header: index for index, header in enumerate(headers)}
        time_candidates = [
            (self._survival_time_score(column), -header_order.get(column, 0), column)
            for column in numeric_columns
            if self._survival_time_score(column) > 0
        ]
        event_candidates = [
            (
                self._survival_event_score(column.name, column),
                -header_order.get(column.name, 0),
                column.name,
            )
            for column in columns
            if self._survival_event_score(column.name, column) > 0
        ]
        time_column = max(time_candidates)[2] if time_candidates else None
        event_column = max(event_candidates)[2] if event_candidates else None
        if event_column == time_column:
            event_column = None
        if time_column and event_column and column_by_name.get(event_column):
            return time_column, event_column
        return time_column, event_column

    def _survival_time_score(self, column_name: str) -> int:
        normalized = self._normalize(column_name)
        score = 0
        if any(token in normalized for token in ["followup", "followuptime", "futime"]):
            score += 8
        if any(token in normalized for token in ["survival", "overallsurvival", "progressionfreesurvival"]):
            score += 7
        if any(token in normalized for token in ["timetoevent", "timeevent", "eventtime"]):
            score += 6
        if any(token in normalized for token in ["osmonths", "pfsmonths", "osdays", "pfsdays"]):
            score += 5
        if "duration" in normalized:
            score += 4
        if any(token in normalized for token in ["months", "month", "days", "day"]):
            score += 2
        if "time" in normalized:
            score += 1
        blocked_generic_time = any(
            token in normalized
            for token in ["delivery", "treatment", "planning", "processing", "beam", "simulation"]
        )
        if blocked_generic_time and score <= 3:
            return 0
        return score

    def _survival_event_score(self, column_name: str, column: DataColumnQuality) -> int:
        normalized = self._normalize(column_name)
        score = 0
        if normalized in {"event", "status", "eventstatus", "survivalstatus", "deathstatus"}:
            score += 8
        if "event" in normalized:
            score += 6
        if "status" in normalized:
            score += 5
        if any(token in normalized for token in ["death", "dead", "deceased", "mortality"]):
            score += 6
        if any(token in normalized for token in ["recurrence", "progression", "failure", "relapse"]):
            score += 4
        if "qaresult" in normalized or normalized == "result":
            return 0
        if score <= 0:
            return 0
        if column.inferred_type == "numeric" and column.unique_count > 2:
            return 0
        if column.inferred_type != "numeric" and column.unique_count > 5:
            return 0
        sample_labels = {value.strip().lower() for value in column.sample_values}
        if sample_labels.intersection(
            {
                "event",
                "death",
                "dead",
                "deceased",
                "progression",
                "recurrence",
                "failure",
                "censored",
                "alive",
                "yes",
                "no",
                "1",
                "0",
            }
        ):
            score += 2
        return score

    def _parse_survival_event(self, value: str | None) -> float | None:
        cleaned = str(value or "").strip()
        if self._is_missing(cleaned):
            return None
        normalized = cleaned.lower()
        if normalized in {"1", "1.0"}:
            return 1.0
        if normalized in {"0", "0.0"}:
            return 0.0
        if normalized in {
            "event",
            "yes",
            "y",
            "true",
            "death",
            "dead",
            "deceased",
            "progression",
            "progressed",
            "recurrence",
            "relapse",
            "failure",
        }:
            return 1.0
        if normalized in {
            "censor",
            "censored",
            "alive",
            "no",
            "n",
            "false",
            "none",
            "non-event",
            "nonevent",
            "no event",
        }:
            return 0.0
        return None

    def _build_advanced_model_candidates(
        self,
        selected_outcomes: list[str],
        binary_outcome: str | None,
        numeric_columns: list[str],
        categorical_columns: list[str],
        group_column: str | None,
        has_time_signal: bool,
        repeated_signal: bool,
        survival_time_column: str | None = None,
        survival_event_column: str | None = None,
    ) -> list[AdvancedModelCandidate]:
        primary_outcome = selected_outcomes[0] if selected_outcomes else None
        excluded_fields = {
            field
            for field in [primary_outcome, binary_outcome, group_column, survival_time_column, survival_event_column]
            if field
        }
        covariates = [
            column
            for column in [*numeric_columns[:4], *categorical_columns[:4]]
            if column not in excluded_fields
        ][:5]
        linear_candidate = self._linear_regression_candidate(primary_outcome, covariates, group_column)
        logistic_candidate = self._logistic_regression_candidate(binary_outcome, covariates, group_column)
        candidates = [
            *( [logistic_candidate] if binary_outcome else [] ),
            linear_candidate,
            *( [] if binary_outcome else [logistic_candidate] ),
            self._cox_model_candidate(survival_time_column, survival_event_column, covariates, has_time_signal),
            self._mixed_effects_candidate(primary_outcome, covariates, group_column, repeated_signal),
        ]
        return candidates

    def _linear_regression_candidate(
        self,
        outcome: str | None,
        covariates: list[str],
        group_column: str | None,
    ) -> AdvancedModelCandidate:
        missing = []
        if not outcome:
            missing.append("continuous outcome")
        if not covariates and not group_column:
            missing.append("at least one predictor or grouping variable")
        available = [value for value in [outcome, group_column, *covariates] if value]
        readiness = "ready" if not missing else "needs_fields"
        return AdvancedModelCandidate(
            model_id="linear_regression",
            model_name="Multivariable linear regression",
            readiness=readiness,
            outcome_column=outcome,
            required_fields=["continuous outcome", "predictors/covariates"],
            available_fields=available,
            missing_fields=missing,
            assumptions=[
                "Continuous outcome with approximately linear relationships.",
                "Residual diagnostics and influential observations must be reviewed.",
                "Collinearity among covariates should be checked before final reporting.",
            ],
            cautions=[
                "This plan does not fit the model or generate coefficients.",
                "Do not report beta estimates, confidence intervals, or P values until model fitting is completed.",
            ],
            methods_template=(
                f"A multivariable linear regression model will be considered for {outcome or '[outcome]'} "
                f"using covariates: {', '.join(covariates) if covariates else '[covariates]'}. "
                "Model diagnostics will include residual assessment, influential-point review, and collinearity checks."
            ),
            results_template=(
                "Regression coefficients, 95% confidence intervals, and P values should be reported only after "
                "the model is fitted and diagnostics are reviewed."
            ),
        )

    def _logistic_regression_candidate(
        self,
        outcome: str | None,
        covariates: list[str],
        group_column: str | None,
    ) -> AdvancedModelCandidate:
        missing = ["binary outcome confirmation"]
        if not outcome:
            missing.append("outcome column")
        if not covariates and not group_column:
            missing.append("at least one predictor or grouping variable")
        available = [value for value in [outcome, group_column, *covariates] if value]
        return AdvancedModelCandidate(
            model_id="logistic_regression",
            model_name="Binary logistic regression",
            readiness="ready" if outcome and (covariates or group_column) else "needs_fields",
            outcome_column=outcome,
            required_fields=["binary outcome", "predictors/covariates"],
            available_fields=available,
            missing_fields=missing,
            assumptions=[
                "Outcome must be explicitly coded as binary.",
                "Events per variable should be sufficient for the planned covariate count.",
                "Separation and sparse categories should be checked.",
            ],
            cautions=[
                "Current CSV type inference cannot prove that the outcome is binary.",
                "Odds ratios should not be reported until model fitting and coding review are complete.",
            ],
            methods_template=(
                f"If {outcome or '[outcome]'} is confirmed as binary, a logistic regression model will be "
                f"considered using covariates: {', '.join(covariates) if covariates else '[covariates]'}. "
                "Adjusted odds ratios with confidence intervals will be reported after coding and sparsity checks."
            ),
            results_template=(
                "Adjusted odds ratios and 95% confidence intervals should be reported after outcome coding, "
                "event counts, and model convergence are verified."
            ),
        )

    def _select_binary_outcome(
        self,
        requested_columns: list[str],
        binary_columns: list[str],
        categorical_columns: list[str],
    ) -> str | None:
        for column in requested_columns:
            if column in binary_columns or column == "qa_result":
                return column
        if "qa_result" in categorical_columns:
            return "qa_result"
        for preferred in ["qa_result", "outcome", "event", "response", "status"]:
            if preferred in binary_columns:
                return preferred
        return binary_columns[0] if binary_columns else None

    def _cox_model_candidate(
        self,
        time_column: str | None,
        event_column: str | None,
        covariates: list[str],
        has_time_signal: bool,
    ) -> AdvancedModelCandidate:
        missing = []
        if not time_column:
            missing.append("follow-up time")
        if not event_column:
            missing.append("event indicator")
        if not covariates:
            missing.append("covariates")
        outcome = f"{time_column} + {event_column}" if time_column and event_column else time_column or event_column
        readiness = "ready" if not missing else "review" if has_time_signal and (time_column or event_column) else "needs_fields"
        return AdvancedModelCandidate(
            model_id="cox_ph",
            model_name="Cox proportional hazards model",
            readiness=readiness,
            outcome_column=outcome,
            required_fields=["follow-up time", "event indicator", "covariates"],
            available_fields=[value for value in [time_column, event_column, *covariates] if value],
            missing_fields=missing,
            assumptions=[
                "Follow-up time and event indicator must be explicitly available.",
                "Proportional hazards assumptions must be checked.",
                "Censoring mechanism should be described in the Methods.",
            ],
            cautions=[
                "The current model plan infers candidate survival fields from column names and still requires manual confirmation.",
                "Hazard ratios from the prototype fit require review in validated survival software before final reporting.",
            ],
            methods_template=(
                f"A Cox proportional hazards model will be considered for {outcome or '[time + event]'} "
                f"using covariates: {', '.join(covariates) if covariates else '[covariates]'}. "
                "Proportional hazards assumptions and censoring definitions must be reviewed before reporting."
            ),
            results_template=(
                "Hazard ratios with 95% confidence intervals should be reported only after time-to-event fields, "
                "event coding, censoring, and proportional hazards assumptions are verified."
            ),
        )

    def _mixed_effects_candidate(
        self,
        outcome: str | None,
        covariates: list[str],
        group_column: str | None,
        repeated_signal: bool,
    ) -> AdvancedModelCandidate:
        missing = []
        if not outcome:
            missing.append("continuous outcome")
        if not group_column:
            missing.append("cluster / subject / patient identifier")
        if not repeated_signal:
            missing.append("repeated-measures design confirmation")
        readiness = (
            "ready"
            if outcome and group_column and repeated_signal
            else "review"
            if outcome and group_column
            else "needs_fields"
        )
        return AdvancedModelCandidate(
            model_id="mixed_effects",
            model_name="Linear mixed-effects model",
            readiness=readiness,
            outcome_column=outcome,
            required_fields=["continuous outcome", "cluster identifier", "fixed-effect covariates"],
            available_fields=[value for value in [outcome, group_column, *covariates] if value],
            missing_fields=missing,
            assumptions=[
                "Repeated observations or clustered data structure must be confirmed.",
                "Random-effects structure should be pre-specified.",
                "Convergence and residual diagnostics must be reviewed.",
            ],
            cautions=[
                "The grouping column may represent a category rather than a subject-level random effect.",
                "Mixed-effects results require validated model fitting and convergence review.",
            ],
            methods_template=(
                f"If repeated or clustered measurements are confirmed, a linear mixed-effects model will be "
                f"considered for {outcome or '[outcome]'}, with {group_column or '[cluster id]'} as the "
                "candidate random-effect grouping variable and pre-specified fixed effects."
            ),
            results_template=(
                "Fixed-effect estimates, random-effect variance components, and model diagnostics should be "
                "reported only after convergence and model specification are reviewed."
            ),
        )

    def build_formal_test_report(
        self,
        project: Project,
        protocol: ProjectProtocol,
        file_name: str,
        content: bytes,
        confirmation: FormalTestConfirmation,
        group_column: str | None = None,
        outcome_columns: list[str] | None = None,
        paired_test: bool = False,
        paired_data_layout: str = "wide",
        paired_analysis: str = "paired_t",
        paired_subject_column: str | None = None,
        paired_condition_column: str | None = None,
        paired_conditions: list[str] | None = None,
        paired_condition_a: str = "",
        paired_condition_b: str = "",
        multiplicity_correction: str = "holm",
    ) -> FormalTestReport:
        missing_confirmations = self._missing_formal_test_confirmations(confirmation)
        if missing_confirmations:
            raise ValueError(f"正式检验前还需要确认：{'、'.join(missing_confirmations)}。")

        privacy_report = self.build_privacy_report_for_csv(content)
        if privacy_report.risk_level == RiskLevel.red:
            raise ValueError("CSV 含疑似直接身份标识。请先完成脱敏，再执行正式检验。")

        headers, rows = self._parse_csv(content)
        if not rows:
            raise ValueError("CSV 文件没有可分析的数据行。")

        columns = [self._analyze_column(header, rows) for header in headers]
        numeric_columns = [column.name for column in columns if column.inferred_type == "numeric"]
        if not numeric_columns:
            raise ValueError("CSV 文件中没有可用于正式检验的数值结局列。")
        normalized_multiplicity_correction = self._normalize_multiplicity_correction(
            multiplicity_correction,
        )

        if paired_test:
            normalized_layout = paired_data_layout.strip().lower() or "wide"
            normalized_paired_analysis = paired_analysis.strip().lower() or "paired_t"
            selected_outcomes = self._select_outcome_columns(
                numeric_columns=numeric_columns,
                requested_columns=outcome_columns or [],
            )
            if normalized_layout == "long":
                if len(selected_outcomes) != 1:
                    raise ValueError("长表配对 t 检验需要且只能选择一个数值结局列。")
                valid_subject_column = self._resolve_group_column(paired_subject_column, headers)
                valid_condition_column = self._resolve_group_column(paired_condition_column, headers)
                first_condition = paired_condition_a.strip()
                second_condition = paired_condition_b.strip()
                if not valid_subject_column:
                    raise ValueError("长表配对 t 检验需要选择对象 ID 列。")
                if not valid_condition_column:
                    raise ValueError("长表配对 t 检验需要选择条件/时间点列。")

                if normalized_paired_analysis in {"friedman", "rm_anova"}:
                    condition_values = self._normalize_condition_values(
                        paired_conditions or [first_condition, second_condition],
                    )
                    if len(condition_values) < 3:
                        raise ValueError("Friedman 重复测量检验至少需要填写 3 个条件/时间点取值。")

                    if normalized_paired_analysis == "friedman":
                        result = self._build_friedman_test_result(
                            outcome_column=selected_outcomes[0],
                            subject_column=valid_subject_column,
                            condition_column=valid_condition_column,
                            condition_values=condition_values,
                            rows=rows,
                            multiplicity_correction=normalized_multiplicity_correction,
                        )
                    else:
                        result = self._build_repeated_measures_anova_design_result(
                            outcome_column=selected_outcomes[0],
                            subject_column=valid_subject_column,
                            condition_column=valid_condition_column,
                            condition_values=condition_values,
                            rows=rows,
                        )
                    completed_count = 1 if result.status == "completed" else 0
                    blocked_count = 1 if result.status == "blocked" else 0
                    review_count = 0 if result.status in {"completed", "blocked"} else 1
                    audit_summary = (
                        f"已在人工确认后执行长表重复测量正式检验：{completed_count} 项完成，"
                        f"{review_count} 项需外部统计环境复核，{blocked_count} 项阻止；未保存原始 CSV。"
                    )
                    next_step = (
                        "将 Friedman 检验和事后比较结果与对象 ID、条件列和研究设计逐项核对，再交给 Alex Writer 写入 Methods/Results。"
                        if protocol.statistical_plan.strip()
                        else "建议先把本次 Friedman 重复测量检验方法补入研究方案的统计路线，再进入论文结果写作。"
                    )
                    return FormalTestReport(
                        project_id=project.id,
                        file_name=file_name,
                        row_count=len(rows),
                        group_column=valid_condition_column,
                        outcome_columns=selected_outcomes,
                        confirmation=confirmation,
                        results=[result],
                        raw_csv_saved=False,
                        audit_summary=audit_summary,
                        next_step=next_step,
                    )

                if normalized_paired_analysis != "paired_t":
                    raise ValueError("长表配对检验类型只能是 paired_t 或 friedman。")
                if not first_condition or not second_condition:
                    raise ValueError("长表配对 t 检验需要填写两个条件/时间点取值。")
                if first_condition == second_condition:
                    raise ValueError("两个条件/时间点取值不能相同。")

                result = self._build_long_paired_t_test_result(
                    outcome_column=selected_outcomes[0],
                    subject_column=valid_subject_column,
                    condition_column=valid_condition_column,
                    first_condition=first_condition,
                    second_condition=second_condition,
                    rows=rows,
                )
                completed_count = 1 if result.status == "completed" else 0
                blocked_count = 1 if result.status == "blocked" else 0
                review_count = 0 if result.status in {"completed", "blocked"} else 1
                audit_summary = (
                    f"已在人工确认后执行长表配对正式检验：{completed_count} 项完成，"
                    f"{review_count} 项需外部统计环境复核，{blocked_count} 项阻止；未保存原始 CSV。"
                )
                next_step = (
                    "将长表配对 t 检验结果与对象 ID、条件列和研究设计逐项核对，再交给 Alex Writer 写入 Methods/Results。"
                    if protocol.statistical_plan.strip()
                    else "建议先把本次长表配对检验方法补入研究方案的统计路线，再进入论文结果写作。"
                )
                return FormalTestReport(
                    project_id=project.id,
                    file_name=file_name,
                    row_count=len(rows),
                    group_column=valid_condition_column,
                    outcome_columns=selected_outcomes,
                    confirmation=confirmation,
                    results=[result],
                    raw_csv_saved=False,
                    audit_summary=audit_summary,
                    next_step=next_step,
                )

            if normalized_layout != "wide":
                raise ValueError("配对 t 检验的数据格式只能是 wide 或 long。")
            if len(selected_outcomes) != 2:
                raise ValueError("配对 t 检验需要且只能选择两个数值结局列。")

            result = self._build_paired_t_test_result(
                first_outcome_column=selected_outcomes[0],
                second_outcome_column=selected_outcomes[1],
                rows=rows,
            )
            completed_count = 1 if result.status == "completed" else 0
            blocked_count = 1 if result.status == "blocked" else 0
            review_count = 0 if result.status in {"completed", "blocked"} else 1
            audit_summary = (
                f"已在人工确认后执行配对正式检验：{completed_count} 项完成，"
                f"{review_count} 项需外部统计环境复核，{blocked_count} 项阻止；未保存原始 CSV。"
            )
            next_step = (
                "将配对 t 检验结果与研究设计逐项核对，再交给 Alex Writer 写入 Methods/Results。"
                if protocol.statistical_plan.strip()
                else "建议先把本次配对检验方法补入研究方案的统计路线，再进入论文结果写作。"
            )
            return FormalTestReport(
                project_id=project.id,
                file_name=file_name,
                row_count=len(rows),
                group_column=None,
                outcome_columns=selected_outcomes,
                confirmation=confirmation,
                results=[result],
                raw_csv_saved=False,
                audit_summary=audit_summary,
                next_step=next_step,
            )

        valid_group_column = self._resolve_group_column(group_column, headers)
        if not valid_group_column:
            raise ValueError("正式检验需要先选择分组列。")

        selected_outcomes = self._select_outcome_columns(
            numeric_columns=numeric_columns,
            requested_columns=outcome_columns or [],
        )
        results = [
            self._build_formal_test_result(
                outcome_column=outcome,
                group_column=valid_group_column,
                rows=rows,
                multiplicity_correction=normalized_multiplicity_correction,
            )
            for outcome in selected_outcomes
        ]
        completed_count = sum(1 for result in results if result.status == "completed")
        blocked_count = sum(1 for result in results if result.status == "blocked")
        review_count = len(results) - completed_count - blocked_count

        audit_summary = (
            f"已在人工确认后执行正式检验：{completed_count} 项完成，"
            f"{review_count} 项需外部统计环境复核，{blocked_count} 项阻止；未保存原始 CSV。"
        )
        if protocol.statistical_plan.strip():
            next_step = "将检验结果与研究方案中的统计路线逐项核对，再交给 Alex Writer 写入 Methods/Results。"
        else:
            next_step = "建议先把本次检验方法补入研究方案的统计路线，再进入论文结果写作。"

        return FormalTestReport(
            project_id=project.id,
            file_name=file_name,
            row_count=len(rows),
            group_column=valid_group_column,
            outcome_columns=selected_outcomes,
            confirmation=confirmation,
            results=results,
            raw_csv_saved=False,
            audit_summary=audit_summary,
            next_step=next_step,
        )

    def _items_from_protocol(self, protocol: ProjectProtocol) -> list[DataRequirementItem]:
        items: list[DataRequirementItem] = []
        for index, label in enumerate(self._split_requirement_text(protocol.data_requirements), start=1):
            items.append(
                DataRequirementItem(
                    id=f"protocol-data-{index}",
                    label=label,
                    category="protocol",
                    source="Project Protocol 数据需求",
                    rationale="来自当前项目研究方案的数据需求字段。",
                )
            )

        for index, label in enumerate(
            self._split_requirement_text(protocol.institutional_field_mapping),
            start=1,
        ):
            items.append(
                DataRequirementItem(
                    id=f"protocol-institutional-field-{index}",
                    label=label,
                    category="institutional_mapping",
                    source="Project Protocol 机构字段适配",
                    rationale="来自当前项目的真实机构字段、伦理授权、导出路径或 TPS/DICOM/QA 适配清单。",
                )
            )

        if protocol.primary_endpoint.strip():
            items.append(
                DataRequirementItem(
                    id="protocol-primary-endpoint",
                    label=protocol.primary_endpoint.strip(),
                    category="endpoint",
                    required=False,
                    source="Project Protocol 主要终点",
                    rationale="主要终点需要能在数据表中定位到对应指标或派生字段。",
                )
            )

        for index, label in enumerate(
            self._split_requirement_text(protocol.secondary_endpoints),
            start=1,
        ):
            items.append(
                DataRequirementItem(
                    id=f"protocol-secondary-endpoint-{index}",
                    label=label,
                    category="endpoint",
                    required=False,
                    source="Project Protocol 次要终点",
                    rationale="次要终点可作为补充分析字段或派生指标。",
                )
            )

        return items

    def _split_requirement_text(self, value: str) -> list[str]:
        parts: list[str] = []
        for line in re.split(r"[；;\n]+", value):
            line = line.strip()
            if not line:
                continue
            if re.match(r"^[-•*]\s*", line):
                parts.append(line)
                continue
            parts.extend(re.split(r"[、，,]", line))
        labels: list[str] = []
        for part in parts:
            label = re.sub(r"^[-•*\d.、\s]+", "", part.strip())
            label = re.sub(r"^(至少需要|需要|包括|以及|和)", "", label)
            label = label.strip(" ：:。. ")
            if label in {"最小数据字段", "测试落地清单", "写入追踪", "Mentor 写入追踪"}:
                continue
            if 2 <= len(label) <= 120 and label not in {"等", "指标", "数据"}:
                labels.append(label)
        return labels

    def _deduplicate_items(self, items: list[DataRequirementItem]) -> list[DataRequirementItem]:
        seen: set[str] = set()
        unique_items: list[DataRequirementItem] = []
        for item in items:
            key = self._normalize(item.label)
            if key and key not in seen:
                seen.add(key)
                unique_items.append(item)
        return unique_items

    def _decode_csv(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("CSV 文件编码无法识别，请使用 UTF-8 或 GBK。")

    def _parse_csv(self, content: bytes) -> tuple[list[str], list[dict[str, str]]]:
        text = self._decode_csv(content)
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV 文件缺少表头。")

        raw_headers = reader.fieldnames
        headers = [self._clean_header(header, index) for index, header in enumerate(raw_headers)]
        rows = [
            {headers[index]: row.get(raw_header, "") for index, raw_header in enumerate(raw_headers)}
            for row in reader
        ]
        return headers, rows

    def _clean_header(self, header: str | None, index: int) -> str:
        value = (header or "").strip()
        return value or f"未命名列 {index + 1}"

    def _analyze_column(self, column_name: str, rows: list[dict[str, str]]) -> DataColumnQuality:
        values = [str(row.get(column_name, "") or "").strip() for row in rows]
        present_values = [value for value in values if not self._is_missing(value)]
        missing_count = len(values) - len(present_values)
        unique_values = list(dict.fromkeys(present_values))
        numeric_values = self._parse_numeric_values(present_values)
        inferred_type = self._infer_type(present_values, numeric_values)

        numeric_summary = None
        if inferred_type == "numeric" and numeric_values:
            numeric_summary = NumericSummary(
                min=round(min(numeric_values), 4),
                max=round(max(numeric_values), 4),
                mean=round(fmean(numeric_values), 4),
            )

        return DataColumnQuality(
            name=column_name,
            inferred_type=inferred_type,
            missing_count=missing_count,
            missing_percent=round(missing_count / len(values) * 100, 1) if values else 0,
            unique_count=len(set(present_values)),
            sample_values=unique_values[:3],
            numeric_summary=numeric_summary,
        )

    def _parse_numeric_values(self, values: list[str]) -> list[float]:
        numeric_values: list[float] = []
        for value in values:
            try:
                numeric_values.append(float(value.replace(",", "")))
            except ValueError:
                continue
        return numeric_values

    def _parse_float(self, value: str | None) -> float | None:
        cleaned = str(value or "").strip()
        if self._is_missing(cleaned):
            return None
        try:
            return float(cleaned.replace(",", ""))
        except ValueError:
            return None

    def _matrix_xtx(self, matrix: list[list[float]]) -> list[list[float]]:
        column_count = len(matrix[0])
        return [
            [
                sum(row[first] * row[second] for row in matrix)
                for second in range(column_count)
            ]
            for first in range(column_count)
        ]

    def _matrix_xty(self, matrix: list[list[float]], values: list[float]) -> list[float]:
        column_count = len(matrix[0])
        return [
            sum(row[column_index] * values[row_index] for row_index, row in enumerate(matrix))
            for column_index in range(column_count)
        ]

    def _matrix_vector_multiply(
        self,
        matrix: list[list[float]],
        vector: list[float],
    ) -> list[float]:
        return [
            sum(row[index] * vector[index] for index in range(len(vector)))
            for row in matrix
        ]

    def _invert_matrix(self, matrix: list[list[float]]) -> list[list[float]]:
        size = len(matrix)
        augmented = [
            [
                *[float(value) for value in matrix[row_index]],
                *[1.0 if row_index == column_index else 0.0 for column_index in range(size)],
            ]
            for row_index in range(size)
        ]
        for pivot_index in range(size):
            pivot_row = max(
                range(pivot_index, size),
                key=lambda row_index: abs(augmented[row_index][pivot_index]),
            )
            if abs(augmented[pivot_row][pivot_index]) < 1e-12:
                raise ValueError("线性回归设计矩阵不可逆，请减少高度相关或重复编码的预测变量。")
            if pivot_row != pivot_index:
                augmented[pivot_index], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_index]
            pivot_value = augmented[pivot_index][pivot_index]
            augmented[pivot_index] = [
                value / pivot_value
                for value in augmented[pivot_index]
            ]
            for row_index in range(size):
                if row_index == pivot_index:
                    continue
                factor = augmented[row_index][pivot_index]
                if factor == 0:
                    continue
                augmented[row_index] = [
                    value - factor * augmented[pivot_index][column_index]
                    for column_index, value in enumerate(augmented[row_index])
                ]
        return [row[size:] for row in augmented]

    def _student_t_critical_975(self, degrees_of_freedom: int) -> float | None:
        if degrees_of_freedom <= 0:
            return None
        if scipy_stats is not None:
            try:
                return float(scipy_stats.t.ppf(0.975, degrees_of_freedom))
            except (FloatingPointError, ValueError):
                pass
        if degrees_of_freedom == 1:
            return 12.706
        if degrees_of_freedom == 2:
            return 4.303
        if degrees_of_freedom <= 5:
            return 2.776
        if degrees_of_freedom <= 10:
            return 2.262
        if degrees_of_freedom <= 20:
            return 2.086
        if degrees_of_freedom <= 30:
            return 2.042
        return 1.96

    def _select_outcome_columns(
        self,
        numeric_columns: list[str],
        requested_columns: list[str],
    ) -> list[str]:
        requested = [column for column in requested_columns if column]
        invalid_columns = [column for column in requested if column not in numeric_columns]
        if invalid_columns:
            raise ValueError(f"以下结局列不是可分析数值列：{', '.join(invalid_columns)}")

        if requested:
            return requested[:6]

        return [
            column
            for column in numeric_columns
            if "id" not in self._normalize(column)
        ][:6] or numeric_columns[:6]

    def _describe_numeric_column(
        self,
        column_name: str,
        rows: list[dict[str, str]],
    ) -> DescriptiveStatistic:
        values = [str(row.get(column_name, "") or "").strip() for row in rows]
        numeric_values = self._parse_numeric_values(
            [value for value in values if not self._is_missing(value)]
        )
        if not numeric_values:
            raise ValueError(f"{column_name} 没有可用于统计的数值。")

        return DescriptiveStatistic(
            column=column_name,
            n=len(numeric_values),
            missing_count=len(rows) - len(numeric_values),
            mean=round(fmean(numeric_values), 4),
            std_dev=round(stdev(numeric_values), 4) if len(numeric_values) > 1 else 0,
            median=round(median(numeric_values), 4),
            min=round(min(numeric_values), 4),
            max=round(max(numeric_values), 4),
        )

    def _build_categorical_summaries(
        self,
        columns: list[DataColumnQuality],
        rows: list[dict[str, str]],
        preferred_group_column: str | None,
    ) -> list[CategoricalSummary]:
        candidates = [
            column.name
            for column in columns
            if column.inferred_type in {"text", "date"}
            and 1 < column.unique_count <= 12
            and column.missing_percent < 100
        ]
        if preferred_group_column and preferred_group_column in candidates:
            candidates = [preferred_group_column, *[name for name in candidates if name != preferred_group_column]]

        return [self._summarize_categorical_column(column, rows) for column in candidates[:4]]

    def _summarize_categorical_column(
        self,
        column_name: str,
        rows: list[dict[str, str]],
    ) -> CategoricalSummary:
        values = [
            str(row.get(column_name, "") or "").strip()
            for row in rows
            if not self._is_missing(str(row.get(column_name, "") or "").strip())
        ]
        counts = Counter(values)
        total = sum(counts.values()) or 1
        levels = [
            CategoricalLevel(
                value=value,
                count=count,
                percent=round(count / total * 100, 1),
            )
            for value, count in counts.most_common(8)
        ]
        return CategoricalSummary(
            column=column_name,
            levels=levels,
            omitted_level_count=max(len(counts) - len(levels), 0),
        )

    def _resolve_group_column(self, group_column: str | None, headers: list[str]) -> str | None:
        if not group_column:
            return None
        if group_column not in headers:
            raise ValueError(f"分组列不存在：{group_column}")
        return group_column

    def _normalize_condition_values(self, values: list[str]) -> list[str]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()
        for value in values:
            normalized_value = value.strip()
            if not normalized_value or normalized_value in seen_values:
                continue
            normalized_values.append(normalized_value)
            seen_values.add(normalized_value)
        return normalized_values

    def _normalize_multiplicity_correction(self, value: str) -> str:
        normalized_value = value.strip().lower().replace("_", "-") or "holm"
        if normalized_value in {"holm", "holm-bonferroni", "bonferroni-holm"}:
            return "holm"
        if normalized_value in {"fdr", "bh", "benjamini-hochberg", "bh-fdr"}:
            return "fdr"
        raise ValueError("多重比较校正方法只能是 Holm-Bonferroni 或 Benjamini-Hochberg FDR。")

    def _build_group_comparison(
        self,
        column_name: str,
        group_column: str,
        rows: list[dict[str, str]],
    ) -> GroupComparisonDraft:
        grouped_values: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            group_value = str(row.get(group_column, "") or "").strip()
            value = str(row.get(column_name, "") or "").strip()
            if self._is_missing(group_value) or self._is_missing(value):
                continue
            numeric_value = self._parse_numeric_values([value])
            if numeric_value:
                grouped_values[group_value].append(numeric_value[0])

        groups = [
            self._describe_group_value(group_value, values)
            for group_value, values in sorted(
                grouped_values.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )[:8]
            if values
        ]

        return GroupComparisonDraft(
            column=column_name,
            group_column=group_column,
            groups=groups,
            interpretation=self._build_group_interpretation(column_name, group_column, groups),
        )

    def _describe_group_value(self, group_value: str, values: list[float]) -> GroupStatistic:
        return GroupStatistic(
            group_value=group_value,
            n=len(values),
            mean=round(fmean(values), 4),
            std_dev=round(stdev(values), 4) if len(values) > 1 else 0,
            median=round(median(values), 4),
            min=round(min(values), 4),
            max=round(max(values), 4),
        )

    def _build_group_interpretation(
        self,
        column_name: str,
        group_column: str,
        groups: list[GroupStatistic],
    ) -> str:
        if len(groups) < 2:
            return (
                f"{column_name} had too few usable groups under {group_column}; no comparative "
                "interpretation is generated at this stage."
            )

        lowest = min(groups, key=lambda group: group.mean)
        highest = max(groups, key=lambda group: group.mean)
        mean_gap = round(highest.mean - lowest.mean, 4)
        return (
            f"For {column_name} grouped by {group_column}, the highest mean was observed in "
            f"{highest.group_value} ({highest.mean}) and the lowest mean in {lowest.group_value} "
            f"({lowest.mean}), with an approximate mean difference of {mean_gap}. This is a "
            "descriptive comparison only; formal significance testing has not yet been applied."
        )

    def _build_distribution_check(
        self,
        summary: DescriptiveStatistic,
        rows: list[dict[str, str]],
    ) -> DistributionCheck:
        skewness_hint = None
        if summary.std_dev > 0:
            skewness_hint = round(3 * (summary.mean - summary.median) / summary.std_dev, 3)

        if summary.n < 10:
            signal = "样本量过小"
            recommendation = "不要依赖正态性判断；优先报告中位数和范围，并考虑非参数检验。"
        elif summary.std_dev == 0:
            signal = "常数列"
            recommendation = "该变量没有可比较变异，不适合作为统计检验结局。"
        elif skewness_hint is not None and abs(skewness_hint) >= 1:
            signal = "明显偏态"
            recommendation = "优先报告中位数和四分位数；正式比较时考虑非参数检验或变量变换。"
        elif skewness_hint is not None and abs(skewness_hint) >= 0.5:
            signal = "轻度偏态"
            recommendation = "正式检验前建议查看直方图/QQ 图，并报告均值与中位数。"
        else:
            signal = "近似对称"
            recommendation = "可作为参数检验候选，但仍需结合 QQ 图、方差齐性和研究设计确认。"

        return DistributionCheck(
            column=summary.column,
            n=summary.n,
            missing_count=summary.missing_count,
            skewness_hint=skewness_hint,
            normality_signal=signal,
            recommendation=recommendation,
        )

    def _build_test_recommendations(
        self,
        selected_outcomes: list[str],
        group_column: str | None,
        group_comparisons: list[GroupComparisonDraft],
        distribution_checks: list[DistributionCheck],
    ) -> list[StatisticalTestRecommendation]:
        checks_by_column = {check.column: check for check in distribution_checks}
        comparison_by_column = {comparison.column: comparison for comparison in group_comparisons}
        has_multiple_outcomes = len(selected_outcomes) > 1

        recommendations: list[StatisticalTestRecommendation] = []
        for outcome in selected_outcomes:
            check = checks_by_column.get(outcome)
            comparison = comparison_by_column.get(outcome)
            group_count = len(comparison.groups) if comparison else 0
            candidate_tests = self._candidate_tests_for_outcome(
                group_count=group_count,
                distribution_check=check,
                group_column=group_column,
            )
            caveats = [
                "当前系统仅给出检验建议，不计算 P 值。",
                "正式检验前需确认独立样本、配对样本或重复测量设计。",
            ]
            if has_multiple_outcomes:
                caveats.append("存在多个结局列，正式报告时需要考虑多重比较校正。")
            if check and check.missing_count:
                caveats.append("该结局列存在缺失值，需说明缺失处理策略。")

            recommendations.append(
                StatisticalTestRecommendation(
                    outcome_column=outcome,
                    group_column=group_column,
                    candidate_tests=candidate_tests,
                    p_value_boundary=(
                        "只有在预先定义主要/次要终点、确认分布与方差条件、明确样本独立性或配对关系后，"
                        "才应计算和报告 P 值。探索性结果应避免把 P 值写成确定性结论。"
                    ),
                    effect_size_note=(
                        "建议同时报告效应量和 95% 置信区间；剂量学研究可补充绝对差值、相对差值或临床阈值达标率。"
                    ),
                    caveats=caveats,
                )
            )

        return recommendations

    def _candidate_tests_for_outcome(
        self,
        group_count: int,
        distribution_check: DistributionCheck | None,
        group_column: str | None,
    ) -> list[str]:
        if not group_column or group_count < 2:
            return ["描述性统计", "如为前后/配对设计，补充配对差值后再选择配对检验"]

        is_skewed = distribution_check is not None and distribution_check.normality_signal in {
            "明显偏态",
            "样本量过小",
        }
        if group_count == 2:
            if is_skewed:
                return ["Mann-Whitney U 检验", "如为配对设计则使用 Wilcoxon 符号秩检验"]
            return ["独立样本 t 检验", "Welch t 检验", "如为配对设计则使用配对 t 检验"]

        if is_skewed:
            return ["Kruskal-Wallis 检验", "事后两两比较需进行多重比较校正"]
        return ["单因素 ANOVA", "Welch ANOVA", "事后比较需进行多重比较校正"]

    def _missing_formal_test_confirmations(
        self,
        confirmation: FormalTestConfirmation,
    ) -> list[str]:
        missing_items: list[str] = []
        if not confirmation.confirmed_by.strip():
            missing_items.append("确认人姓名")
        if not confirmation.design_confirmed:
            missing_items.append("研究设计与样本独立性")
        if not confirmation.endpoints_confirmed:
            missing_items.append("主要/次要终点")
        if not confirmation.deidentified_confirmed:
            missing_items.append("CSV 脱敏状态")
        if not confirmation.missing_data_reviewed:
            missing_items.append("缺失值处理策略")
        if not confirmation.assumptions_reviewed:
            missing_items.append("分布、方差和异常值假设")
        if not confirmation.multiplicity_reviewed:
            missing_items.append("多重比较处理")
        return missing_items

    def _build_formal_test_result(
        self,
        outcome_column: str,
        group_column: str,
        rows: list[dict[str, str]],
        multiplicity_correction: str,
    ) -> FormalTestResult:
        grouped_values = self._collect_grouped_numeric_values(
            outcome_column=outcome_column,
            group_column=group_column,
            rows=rows,
        )
        group_labels = list(grouped_values.keys())
        warnings: list[str] = []

        if len(grouped_values) < 2:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="正式检验未执行",
                status="blocked",
                group_count=len(grouped_values),
                group_labels=group_labels,
                interpretation=f"{outcome_column} 在 {group_column} 下可用分组不足，无法执行正式检验。",
                warnings=["至少需要两个存在有效数值的分组。"],
            )

        if len(grouped_values) > 2:
            if self._should_use_kruskal_wallis(grouped_values):
                return self._build_kruskal_wallis_result(
                    outcome_column=outcome_column,
                    group_column=group_column,
                    grouped_values=grouped_values,
                    multiplicity_correction=multiplicity_correction,
                )
            if self._should_use_welch_anova(grouped_values):
                return self._build_welch_anova_result(
                    outcome_column=outcome_column,
                    group_column=group_column,
                    grouped_values=grouped_values,
                    multiplicity_correction=multiplicity_correction,
                )
            return self._build_one_way_anova_result(
                outcome_column=outcome_column,
                group_column=group_column,
                grouped_values=grouped_values,
                multiplicity_correction=multiplicity_correction,
            )

        first_label, second_label = group_labels
        first_values = grouped_values[first_label]
        second_values = grouped_values[second_label]
        if len(first_values) < 2 or len(second_values) < 2:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Welch t 检验未执行",
                status="blocked",
                group_count=2,
                group_labels=group_labels,
                interpretation=(
                    f"{outcome_column} 的两个分组有效样本量不足，无法估计组内方差。"
                ),
                warnings=["每个分组至少需要 2 个有效数值。"],
            )

        first_mean = fmean(first_values)
        second_mean = fmean(second_values)
        first_variance = self._sample_variance(first_values)
        second_variance = self._sample_variance(second_values)
        standard_error_squared = first_variance / len(first_values) + second_variance / len(second_values)
        if standard_error_squared <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Welch t 检验未执行",
                status="blocked",
                group_count=2,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的组内方差为 0，无法计算 t 统计量。",
                warnings=["常数列或完全无组内变异不适合做均值差异检验。"],
            )

        statistic = (first_mean - second_mean) / sqrt(standard_error_squared)
        degrees_of_freedom = self._welch_degrees_of_freedom(
            first_variance=first_variance,
            first_n=len(first_values),
            second_variance=second_variance,
            second_n=len(second_values),
        )
        p_value = self._student_t_two_sided_p_value(statistic, degrees_of_freedom)
        effect_size = self._cohens_d(first_values, second_values)

        if min(len(first_values), len(second_values)) < 10:
            warnings.append("至少一个分组样本量小于 10，P 值需要谨慎解释。")
        if abs(effect_size) >= 0.8:
            effect_note = "效应量较大"
        elif abs(effect_size) >= 0.5:
            effect_note = "效应量中等"
        elif abs(effect_size) >= 0.2:
            effect_note = "效应量较小"
        else:
            effect_note = "效应量很小"

        interpretation = (
            f"{outcome_column} 按 {group_column} 分为 {first_label} 与 {second_label} 后，"
            f"Welch t={round(statistic, 4)}，df={round(degrees_of_freedom, 2)}，"
            f"双侧 P={self._format_p_value(p_value)}，Cohen's d={round(effect_size, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=group_column,
            test_name="Welch t 检验",
            status="completed",
            statistic=round(statistic, 6),
            degrees_of_freedom=round(degrees_of_freedom, 6),
            p_value=round(p_value, 8),
            effect_size=round(effect_size, 6),
            group_count=2,
            group_labels=group_labels,
            interpretation=interpretation,
            warnings=warnings,
        )

    def _build_paired_t_test_result(
        self,
        first_outcome_column: str,
        second_outcome_column: str,
        rows: list[dict[str, str]],
    ) -> FormalTestResult:
        paired_differences: list[float] = []
        skipped_pair_count = 0
        for row in rows:
            first_raw_value = str(row.get(first_outcome_column, "") or "").strip()
            second_raw_value = str(row.get(second_outcome_column, "") or "").strip()
            if self._is_missing(first_raw_value) or self._is_missing(second_raw_value):
                skipped_pair_count += 1
                continue

            first_values = self._parse_numeric_values([first_raw_value])
            second_values = self._parse_numeric_values([second_raw_value])
            if not first_values or not second_values:
                skipped_pair_count += 1
                continue
            paired_differences.append(second_values[0] - first_values[0])

        return self._build_paired_t_result_from_differences(
            paired_differences=paired_differences,
            outcome_label=f"{second_outcome_column} - {first_outcome_column}",
            group_labels=[first_outcome_column, second_outcome_column],
            first_label=first_outcome_column,
            second_label=second_outcome_column,
            skipped_pair_count=skipped_pair_count,
            design_note="配对 t 检验要求每一行代表同一对象的两次/两条件测量。",
            skipped_note_prefix="已排除",
        )

    def _build_long_paired_t_test_result(
        self,
        outcome_column: str,
        subject_column: str,
        condition_column: str,
        first_condition: str,
        second_condition: str,
        rows: list[dict[str, str]],
    ) -> FormalTestResult:
        subject_values: dict[str, dict[str, float]] = defaultdict(dict)
        duplicate_subjects: set[str] = set()
        invalid_subjects: set[str] = set()
        ignored_row_count = 0
        target_conditions = {first_condition, second_condition}

        for row in rows:
            subject_value = str(row.get(subject_column, "") or "").strip()
            condition_value = str(row.get(condition_column, "") or "").strip()
            raw_outcome_value = str(row.get(outcome_column, "") or "").strip()
            if self._is_missing(subject_value) or self._is_missing(condition_value):
                ignored_row_count += 1
                continue
            if condition_value not in target_conditions:
                ignored_row_count += 1
                continue
            if self._is_missing(raw_outcome_value):
                invalid_subjects.add(subject_value)
                continue

            numeric_values = self._parse_numeric_values([raw_outcome_value])
            if not numeric_values:
                invalid_subjects.add(subject_value)
                continue
            if condition_value in subject_values[subject_value]:
                duplicate_subjects.add(subject_value)
                continue
            subject_values[subject_value][condition_value] = numeric_values[0]

        paired_differences: list[float] = []
        incomplete_subject_count = 0
        excluded_subjects = duplicate_subjects | invalid_subjects
        for subject_value, condition_values in subject_values.items():
            if subject_value in excluded_subjects:
                continue
            if first_condition not in condition_values or second_condition not in condition_values:
                incomplete_subject_count += 1
                continue
            paired_differences.append(condition_values[second_condition] - condition_values[first_condition])

        extra_warnings: list[str] = []
        if duplicate_subjects:
            extra_warnings.append(
                f"已排除 {len(duplicate_subjects)} 个对象：同一对象在同一条件下存在重复行。"
            )
        if invalid_subjects:
            extra_warnings.append(
                f"已排除 {len(invalid_subjects)} 个对象：目标条件下存在缺失或非数值结局。"
            )
        if incomplete_subject_count:
            extra_warnings.append(f"已排除 {incomplete_subject_count} 个对象：缺少其中一个目标条件。")
        if ignored_row_count:
            extra_warnings.append(f"已忽略 {ignored_row_count} 行非目标条件或缺少对象/条件标识的记录。")

        return self._build_paired_t_result_from_differences(
            paired_differences=paired_differences,
            outcome_label=f"{outcome_column}: {second_condition} - {first_condition}",
            group_labels=[first_condition, second_condition],
            first_label=first_condition,
            second_label=second_condition,
            skipped_pair_count=0,
            design_note=(
                f"长表配对 t 检验按 {subject_column} 配对，并比较 "
                f"{condition_column}={first_condition} 与 {second_condition}。"
            ),
            skipped_note_prefix="已排除",
            extra_warnings=extra_warnings,
        )

    def _build_friedman_test_result(
        self,
        outcome_column: str,
        subject_column: str,
        condition_column: str,
        condition_values: list[str],
        rows: list[dict[str, str]],
        multiplicity_correction: str,
    ) -> FormalTestResult:
        subject_values: dict[str, dict[str, float]] = defaultdict(dict)
        duplicate_subjects: set[str] = set()
        invalid_subjects: set[str] = set()
        ignored_row_count = 0
        target_conditions = set(condition_values)

        for row in rows:
            subject_value = str(row.get(subject_column, "") or "").strip()
            condition_value = str(row.get(condition_column, "") or "").strip()
            raw_outcome_value = str(row.get(outcome_column, "") or "").strip()
            if self._is_missing(subject_value) or self._is_missing(condition_value):
                ignored_row_count += 1
                continue
            if condition_value not in target_conditions:
                ignored_row_count += 1
                continue
            if self._is_missing(raw_outcome_value):
                invalid_subjects.add(subject_value)
                continue

            numeric_values = self._parse_numeric_values([raw_outcome_value])
            if not numeric_values:
                invalid_subjects.add(subject_value)
                continue
            if condition_value in subject_values[subject_value]:
                duplicate_subjects.add(subject_value)
                continue
            subject_values[subject_value][condition_value] = numeric_values[0]

        complete_subject_values: list[dict[str, float]] = []
        incomplete_subject_count = 0
        excluded_subjects = duplicate_subjects | invalid_subjects
        for subject_value, values_by_condition in subject_values.items():
            if subject_value in excluded_subjects:
                continue
            if any(condition not in values_by_condition for condition in condition_values):
                incomplete_subject_count += 1
                continue
            complete_subject_values.append(
                {condition: values_by_condition[condition] for condition in condition_values}
            )

        subject_count = len(complete_subject_values)
        condition_count = len(condition_values)
        warnings = [
            f"Friedman 检验按 {subject_column} 配对，并比较 {condition_column} 中 {condition_count} 个条件。",
            "P 值基于卡方近似；正式报告前需复核重复测量设计、缺失机制和异常值。",
        ]
        if duplicate_subjects:
            warnings.append(f"已排除 {len(duplicate_subjects)} 个对象：同一对象在同一条件下存在重复行。")
        if invalid_subjects:
            warnings.append(f"已排除 {len(invalid_subjects)} 个对象：目标条件下存在缺失或非数值结局。")
        if incomplete_subject_count:
            warnings.append(f"已排除 {incomplete_subject_count} 个对象：未覆盖全部目标条件。")
        if ignored_row_count:
            warnings.append(f"已忽略 {ignored_row_count} 行非目标条件或缺少对象/条件标识的记录。")

        if subject_count < 2:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=condition_column,
                test_name="Friedman 检验未执行",
                status="blocked",
                group_count=condition_count,
                group_labels=condition_values,
                interpretation="完整重复测量对象不足，无法执行 Friedman 检验。",
                warnings=["Friedman 检验至少需要 2 个完整对象。", *warnings],
            )

        rank_sums = {condition: 0.0 for condition in condition_values}
        tie_sum = 0
        for values_by_condition in complete_subject_values:
            ordered_values = [values_by_condition[condition] for condition in condition_values]
            ranks = self._rank_plain_values(ordered_values)
            value_counts = Counter(ordered_values)
            tie_sum += sum(count**3 - count for count in value_counts.values() if count > 1)
            for condition, rank in zip(condition_values, ranks):
                rank_sums[condition] += rank

        statistic = (
            12
            / (subject_count * condition_count * (condition_count + 1))
            * sum(rank_sum**2 for rank_sum in rank_sums.values())
            - 3 * subject_count * (condition_count + 1)
        )
        tie_correction = 1 - tie_sum / (subject_count * condition_count * (condition_count**2 - 1))
        if tie_correction <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=condition_column,
                test_name="Friedman 检验未执行",
                status="blocked",
                group_count=condition_count,
                group_labels=condition_values,
                interpretation="所有完整对象的条件内秩无有效差异，无法执行 Friedman 检验。",
                warnings=["所有重复测量值可能完全相同。", *warnings],
            )
        statistic = max(statistic / tie_correction, 0)
        degrees_of_freedom = condition_count - 1
        p_value = self._chi_square_survival(statistic, degrees_of_freedom)
        if scipy_stats is not None and hasattr(scipy_stats, "friedmanchisquare"):
            try:
                friedman_result = scipy_stats.friedmanchisquare(
                    *[
                        [values_by_condition[condition] for values_by_condition in complete_subject_values]
                        for condition in condition_values
                    ]
                )
                statistic = max(float(friedman_result.statistic), 0)
                p_value = self._clamp_probability(float(friedman_result.pvalue))
                warnings[1] = (
                    "P 值由 scipy.stats.friedmanchisquare 计算；正式报告前仍需复核重复测量设计、"
                    "缺失机制和异常值。"
                )
            except (FloatingPointError, ValueError):
                pass
        kendalls_w = min(statistic / (subject_count * (condition_count - 1)), 1)

        if kendalls_w >= 0.5:
            effect_note = "一致性效应较大"
        elif kendalls_w >= 0.3:
            effect_note = "一致性效应中等"
        elif kendalls_w >= 0.1:
            effect_note = "一致性效应较小"
        else:
            effect_note = "一致性效应很小"
        if subject_count < 10:
            warnings.append("完整对象数小于 10，Friedman 卡方近似 P 值需要谨慎解释。")

        interpretation = (
            f"{outcome_column} 在 {condition_count} 个重复测量条件下，"
            f"Friedman Q({degrees_of_freedom})={round(statistic, 4)}，"
            f"P={self._format_p_value(p_value)}，Kendall's W={round(kendalls_w, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=condition_column,
            test_name="Friedman 检验",
            status="completed",
            statistic=round(statistic, 6),
            degrees_of_freedom=float(degrees_of_freedom),
            p_value=round(p_value, 8),
            effect_size=round(kendalls_w, 6),
            group_count=condition_count,
            group_labels=condition_values,
            interpretation=interpretation,
            warnings=warnings,
            pairwise_results=self._build_pairwise_signed_rank_results(
                complete_subject_values=complete_subject_values,
                condition_values=condition_values,
                multiplicity_correction=multiplicity_correction,
            ),
        )

    def _build_repeated_measures_anova_design_result(
        self,
        outcome_column: str,
        subject_column: str,
        condition_column: str,
        condition_values: list[str],
        rows: list[dict[str, str]],
    ) -> FormalTestResult:
        subject_values: dict[str, dict[str, float]] = defaultdict(dict)
        duplicate_subjects: set[str] = set()
        invalid_subjects: set[str] = set()
        ignored_row_count = 0
        target_conditions = set(condition_values)

        for row in rows:
            subject_value = str(row.get(subject_column, "") or "").strip()
            condition_value = str(row.get(condition_column, "") or "").strip()
            raw_outcome_value = str(row.get(outcome_column, "") or "").strip()
            if self._is_missing(subject_value) or self._is_missing(condition_value):
                ignored_row_count += 1
                continue
            if condition_value not in target_conditions:
                ignored_row_count += 1
                continue
            if self._is_missing(raw_outcome_value):
                invalid_subjects.add(subject_value)
                continue

            numeric_values = self._parse_numeric_values([raw_outcome_value])
            if not numeric_values:
                invalid_subjects.add(subject_value)
                continue
            if condition_value in subject_values[subject_value]:
                duplicate_subjects.add(subject_value)
                continue
            subject_values[subject_value][condition_value] = numeric_values[0]

        complete_subject_count = 0
        incomplete_subject_count = 0
        excluded_subjects = duplicate_subjects | invalid_subjects
        for subject_value, values_by_condition in subject_values.items():
            if subject_value in excluded_subjects:
                continue
            if any(condition not in values_by_condition for condition in condition_values):
                incomplete_subject_count += 1
                continue
            complete_subject_count += 1

        condition_count = len(condition_values)
        warnings = [
            (
                f"Recognized repeated-measures design with subject column {subject_column}, "
                f"condition column {condition_column}, and {condition_count} target conditions."
            ),
            (
                "Formal repeated-measures ANOVA is not computed in this prototype. "
                "Validate the final F statistic, degrees of freedom, P value, and effect size "
                "with statsmodels AnovaRM, R, SPSS, or another validated statistics workflow."
            ),
        ]
        if duplicate_subjects:
            warnings.append(
                f"Excluded {len(duplicate_subjects)} subject(s) with duplicated rows inside the same condition."
            )
        if invalid_subjects:
            warnings.append(
                f"Excluded {len(invalid_subjects)} subject(s) with missing or non-numeric outcomes in target conditions."
            )
        if incomplete_subject_count:
            warnings.append(
                f"Found {incomplete_subject_count} incomplete subject(s); mixed-effects models may fit unbalanced repeated-measures data better."
            )
        if ignored_row_count:
            warnings.append(
                f"Ignored {ignored_row_count} row(s) outside target conditions or missing subject/condition identifiers."
            )

        if complete_subject_count < 2:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=condition_column,
                test_name="Repeated-measures ANOVA design check",
                status="blocked",
                group_count=condition_count,
                group_labels=condition_values,
                interpretation=(
                    "Repeated-measures ANOVA was not run because fewer than 2 complete subjects "
                    "covered all selected conditions."
                ),
                warnings=warnings,
            )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=condition_column,
            test_name="Repeated-measures ANOVA design check",
            status="needs_external_review",
            group_count=condition_count,
            group_labels=condition_values,
            interpretation=(
                "The uploaded CSV matches a long-table repeated-measures ANOVA design. "
                "Formal ANOVA statistics should be reviewed in an external validated environment."
            ),
            warnings=warnings,
        )

    def _build_paired_t_result_from_differences(
        self,
        paired_differences: list[float],
        outcome_label: str,
        group_labels: list[str],
        first_label: str,
        second_label: str,
        skipped_pair_count: int,
        design_note: str,
        skipped_note_prefix: str,
        extra_warnings: list[str] | None = None,
    ) -> FormalTestResult:
        pair_count = len(paired_differences)
        if pair_count < 2:
            return FormalTestResult(
                outcome_column=outcome_label,
                group_column=None,
                test_name="配对 t 检验未执行",
                status="blocked",
                group_count=2,
                group_labels=group_labels,
                interpretation=(
                    f"{first_label} 与 {second_label} 的完整配对数据不足，"
                    "无法估计差值方差。"
                ),
                warnings=["配对 t 检验至少需要 2 对完整数值。", *(extra_warnings or [])],
            )

        mean_difference = fmean(paired_differences)
        difference_std_dev = stdev(paired_differences)
        if difference_std_dev <= 0:
            return FormalTestResult(
                outcome_column=outcome_label,
                group_column=None,
                test_name="配对 t 检验未执行",
                status="blocked",
                group_count=2,
                group_labels=group_labels,
                interpretation=(
                    f"{first_label} 与 {second_label} 的配对差值方差为 0，"
                    "无法计算 t 统计量。"
                ),
                warnings=["所有配对差值相同，不适合做配对 t 检验。", *(extra_warnings or [])],
            )

        statistic = mean_difference / (difference_std_dev / sqrt(pair_count))
        degrees_of_freedom = pair_count - 1
        p_value = self._student_t_two_sided_p_value(statistic, degrees_of_freedom)
        effect_size = mean_difference / difference_std_dev

        warnings = [
            design_note,
            "正式报告前需复核差值近似正态、异常值和配对关系是否成立。",
        ]
        if pair_count < 10:
            warnings.append("完整配对数小于 10，P 值需要谨慎解释。")
        if skipped_pair_count:
            warnings.append(f"{skipped_note_prefix} {skipped_pair_count} 行不完整或非数值配对。")
        warnings.extend(extra_warnings or [])

        if abs(effect_size) >= 0.8:
            effect_note = "效应量较大"
        elif abs(effect_size) >= 0.5:
            effect_note = "效应量中等"
        elif abs(effect_size) >= 0.2:
            effect_note = "效应量较小"
        else:
            effect_note = "效应量很小"

        interpretation = (
            f"{second_label} 相对 {first_label} 的配对差值均值为 "
            f"{round(mean_difference, 4)}，配对 t({degrees_of_freedom})={round(statistic, 4)}，"
            f"双侧 P={self._format_p_value(p_value)}，dz={round(effect_size, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_label,
            group_column=None,
            test_name="配对 t 检验",
            status="completed",
            statistic=round(statistic, 6),
            degrees_of_freedom=float(degrees_of_freedom),
            p_value=round(p_value, 8),
            effect_size=round(effect_size, 6),
            group_count=2,
            group_labels=group_labels,
            interpretation=interpretation,
            warnings=warnings,
        )

    def _should_use_kruskal_wallis(self, grouped_values: dict[str, list[float]]) -> bool:
        all_values = [
            value
            for values in grouped_values.values()
            for value in values
        ]
        group_sizes = [len(values) for values in grouped_values.values()]
        if min(group_sizes) < 10:
            return True

        if len(all_values) < 3:
            return True
        pooled_std_dev = stdev(all_values)
        if pooled_std_dev <= 0:
            return False
        skewness_hint = 3 * (fmean(all_values) - median(all_values)) / pooled_std_dev
        return abs(skewness_hint) >= 1

    def _should_use_welch_anova(self, grouped_values: dict[str, list[float]]) -> bool:
        group_sizes = [len(values) for values in grouped_values.values()]
        group_variances = [self._sample_variance(values) for values in grouped_values.values()]
        if any(variance <= 0 for variance in group_variances):
            return False

        variance_ratio = max(group_variances) / min(group_variances)
        size_ratio = max(group_sizes) / min(group_sizes)
        return variance_ratio >= 4 or size_ratio >= 3 or (variance_ratio >= 2 and size_ratio >= 2)

    def _build_kruskal_wallis_result(
        self,
        outcome_column: str,
        group_column: str,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> FormalTestResult:
        group_labels = list(grouped_values.keys())
        group_count = len(grouped_values)
        ranked_values = self._rank_grouped_values(grouped_values)
        total_n = len(ranked_values)
        df = group_count - 1
        if total_n <= group_count or df <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Kruskal-Wallis 检验未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的有效样本量不足，无法执行 Kruskal-Wallis 检验。",
                warnings=["每个分组都需要足够的有效数值。"],
            )

        rank_sums = {
            label: 0.0
            for label in group_labels
        }
        for label, _value, rank in ranked_values:
            rank_sums[label] += rank

        h_statistic = (
            12
            / (total_n * (total_n + 1))
            * sum((rank_sums[label] ** 2) / len(grouped_values[label]) for label in group_labels)
            - 3 * (total_n + 1)
        )
        tie_correction = self._rank_tie_correction(ranked_values)
        if tie_correction <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Kruskal-Wallis 检验未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的所有有效数值相同，无法比较秩分布差异。",
                warnings=["常数列或完全相同的结局值不适合做秩和检验。"],
            )
        h_statistic = max(h_statistic / tie_correction, 0)
        p_value = self._chi_square_survival(h_statistic, df)
        epsilon_squared = max((h_statistic - group_count + 1) / (total_n - group_count), 0)
        epsilon_squared = min(epsilon_squared, 1)

        if epsilon_squared >= 0.26:
            effect_note = "效应量较大"
        elif epsilon_squared >= 0.08:
            effect_note = "效应量中等"
        elif epsilon_squared >= 0.01:
            effect_note = "效应量较小"
        else:
            effect_note = "效应量很小"

        group_sizes = [len(values) for values in grouped_values.values()]
        warnings = [
            "Kruskal-Wallis 检验只判断多组秩分布是否存在总体差异；已附带 Dunn 风格近似事后比较。",
            "P 值基于卡方近似；正式报告前需结合研究设计和多重比较校正复核。",
        ]
        if min(group_sizes) < 5:
            warnings.append("至少一个分组样本量小于 5，卡方近似 P 值需要谨慎解释。")
        if tie_correction < 0.95:
            warnings.append("数据中存在较多相同数值，已进行 ties correction。")

        interpretation = (
            f"{outcome_column} 按 {group_column} 分为 {group_count} 组后，"
            f"Kruskal-Wallis H({df})={round(h_statistic, 4)}，"
            f"P={self._format_p_value(p_value)}，ε²={round(epsilon_squared, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=group_column,
            test_name="Kruskal-Wallis 检验",
            status="completed",
            statistic=round(h_statistic, 6),
            degrees_of_freedom=float(df),
            p_value=round(p_value, 8),
            effect_size=round(epsilon_squared, 6),
            group_count=group_count,
            group_labels=group_labels,
            interpretation=interpretation,
            warnings=warnings,
            pairwise_results=self._build_dunn_pairwise_results(
                grouped_values,
                multiplicity_correction=multiplicity_correction,
            ),
        )

    def _build_welch_anova_result(
        self,
        outcome_column: str,
        group_column: str,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> FormalTestResult:
        group_labels = list(grouped_values.keys())
        group_count = len(grouped_values)
        group_stats = [
            {
                "label": label,
                "n": len(values),
                "mean": fmean(values),
                "variance": self._sample_variance(values),
            }
            for label, values in grouped_values.items()
        ]
        invalid_groups = [
            str(stat["label"])
            for stat in group_stats
            if stat["n"] < 2 or stat["variance"] <= 0
        ]
        if invalid_groups:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Welch ANOVA 未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=(
                    f"{outcome_column} 在 {group_column} 下存在无法估计组内方差的分组，"
                    "无法执行 Welch ANOVA。"
                ),
                warnings=[
                    f"以下分组样本量不足或方差为 0：{'、'.join(invalid_groups[:5])}。",
                    "请先补充数据、合并稀疏分组，或改用人工复核的统计方案。",
                ],
            )

        weights = [
            stat["n"] / stat["variance"]
            for stat in group_stats
        ]
        total_weight = sum(weights)
        if total_weight <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="Welch ANOVA 未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的 Welch 权重无法计算。",
                warnings=["请确认每个分组都有足够变异和有效样本量。"],
            )

        weighted_mean = sum(
            weight * stat["mean"]
            for weight, stat in zip(weights, group_stats)
        ) / total_weight
        df_between = group_count - 1
        correction_sum = sum(
            ((1 - weight / total_weight) ** 2) / (stat["n"] - 1)
            for weight, stat in zip(weights, group_stats)
        )
        if correction_sum <= 0:
            return self._build_one_way_anova_result(
                outcome_column=outcome_column,
                group_column=group_column,
                grouped_values=grouped_values,
                multiplicity_correction=multiplicity_correction,
            )

        denominator_df = (group_count**2 - 1) / (3 * correction_sum)
        denominator_adjustment = 1 + (
            2
            * (group_count - 2)
            / (group_count**2 - 1)
            * correction_sum
        )
        numerator = sum(
            weight * (stat["mean"] - weighted_mean) ** 2
            for weight, stat in zip(weights, group_stats)
        ) / df_between
        statistic = numerator / denominator_adjustment
        p_value = self._f_distribution_survival(
            statistic=statistic,
            numerator_df=df_between,
            denominator_df=denominator_df,
        )
        eta_squared = self._eta_squared_from_grouped_values(grouped_values)

        if eta_squared >= 0.14:
            effect_note = "描述性效应量较大"
        elif eta_squared >= 0.06:
            effect_note = "描述性效应量中等"
        elif eta_squared >= 0.01:
            effect_note = "描述性效应量较小"
        else:
            effect_note = "描述性效应量很小"

        group_sizes = [int(stat["n"]) for stat in group_stats]
        group_variances = [float(stat["variance"]) for stat in group_stats]
        warnings = [
            "Welch ANOVA 用于方差不齐或样本量不均衡的多组均值比较。",
            "已附带 Games-Howell 风格近似事后比较；正式报告前需用统计软件复核精确分布。",
        ]
        if max(group_sizes) / min(group_sizes) >= 3:
            warnings.append("分组样本量明显不均衡，已采用 Welch ANOVA 近似自由度。")
        if max(group_variances) / min(group_variances) >= 4:
            warnings.append("分组方差差异明显，已采用 Welch ANOVA。")

        interpretation = (
            f"{outcome_column} 按 {group_column} 分为 {group_count} 组后，"
            f"Welch ANOVA F({df_between}, {round(denominator_df, 2)})={round(statistic, 4)}，"
            f"P={self._format_p_value(p_value)}，描述性 η²={round(eta_squared, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=group_column,
            test_name="Welch ANOVA",
            status="completed",
            statistic=round(statistic, 6),
            degrees_of_freedom=float(df_between),
            denominator_degrees_of_freedom=round(denominator_df, 6),
            p_value=round(p_value, 8),
            effect_size=round(eta_squared, 6),
            group_count=group_count,
            group_labels=group_labels,
            interpretation=interpretation,
            warnings=warnings,
            pairwise_results=self._build_games_howell_pairwise_results(
                grouped_values,
                multiplicity_correction=multiplicity_correction,
            ),
        )

    def _build_one_way_anova_result(
        self,
        outcome_column: str,
        group_column: str,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> FormalTestResult:
        group_labels = list(grouped_values.keys())
        undersized_groups = [
            label
            for label, values in grouped_values.items()
            if len(values) < 2
        ]
        if undersized_groups:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="单因素 ANOVA 未执行",
                status="blocked",
                group_count=len(grouped_values),
                group_labels=group_labels,
                interpretation=(
                    f"{outcome_column} 在 {group_column} 下存在有效样本量不足的分组，"
                    "无法稳定估计组内方差。"
                ),
                warnings=[
                    f"以下分组少于 2 个有效数值：{'、'.join(undersized_groups[:5])}。",
                    "请先合并稀疏分组、补充数据或改用人工复核的统计方案。",
                ],
            )

        all_values = [
            value
            for values in grouped_values.values()
            for value in values
        ]
        group_count = len(grouped_values)
        total_n = len(all_values)
        df_between = group_count - 1
        df_within = total_n - group_count
        if df_between <= 0 or df_within <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="单因素 ANOVA 未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的自由度不足，无法执行单因素 ANOVA。",
                warnings=["请确认每个分组都有足够的有效数值。"],
            )

        grand_mean = fmean(all_values)
        group_means = {
            label: fmean(values)
            for label, values in grouped_values.items()
        }
        ss_between = sum(
            len(values) * (group_means[label] - grand_mean) ** 2
            for label, values in grouped_values.items()
        )
        ss_within = sum(
            sum((value - group_means[label]) ** 2 for value in values)
            for label, values in grouped_values.items()
        )
        if ss_within <= 0:
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="单因素 ANOVA 未执行",
                status="blocked",
                group_count=group_count,
                group_labels=group_labels,
                interpretation=f"{outcome_column} 的组内方差为 0，无法计算 F 统计量。",
                warnings=["常数列或完全无组内变异不适合做均值差异检验。"],
            )

        ms_between = ss_between / df_between
        ms_within = ss_within / df_within
        statistic = ms_between / ms_within
        p_value = self._f_distribution_survival(
            statistic=statistic,
            numerator_df=df_between,
            denominator_df=df_within,
        )
        eta_squared = ss_between / (ss_between + ss_within) if (ss_between + ss_within) > 0 else 0

        if eta_squared >= 0.14:
            effect_note = "效应量较大"
        elif eta_squared >= 0.06:
            effect_note = "效应量中等"
        elif eta_squared >= 0.01:
            effect_note = "效应量较小"
        else:
            effect_note = "效应量很小"

        group_sizes = [len(values) for values in grouped_values.values()]
        warnings = [
            "单因素 ANOVA 只检验总体均值差异；已附带 Tukey HSD 风格近似事后比较。",
            "报告前仍需结合方差齐性、异常值和多重比较校正进行统计复核。",
        ]
        if min(group_sizes) < 10:
            warnings.append("至少一个分组样本量小于 10，P 值需要谨慎解释。")
        if max(group_sizes) / min(group_sizes) >= 3:
            warnings.append("分组样本量不均衡，建议复核方差齐性或考虑 Welch ANOVA。")

        interpretation = (
            f"{outcome_column} 按 {group_column} 分为 {group_count} 组后，"
            f"单因素 ANOVA F({df_between}, {df_within})={round(statistic, 4)}，"
            f"P={self._format_p_value(p_value)}，η²={round(eta_squared, 4)}（{effect_note}）。"
        )

        return FormalTestResult(
            outcome_column=outcome_column,
            group_column=group_column,
            test_name="单因素 ANOVA",
            status="completed",
            statistic=round(statistic, 6),
            degrees_of_freedom=float(df_between),
            denominator_degrees_of_freedom=float(df_within),
            p_value=round(p_value, 8),
            effect_size=round(eta_squared, 6),
            group_count=group_count,
            group_labels=group_labels,
            interpretation=interpretation,
            warnings=warnings,
            pairwise_results=self._build_tukey_pairwise_results(
                grouped_values,
                multiplicity_correction=multiplicity_correction,
            ),
        )

    def _collect_grouped_numeric_values(
        self,
        outcome_column: str,
        group_column: str,
        rows: list[dict[str, str]],
    ) -> dict[str, list[float]]:
        grouped_values: dict[str, list[float]] = {}
        for row in rows:
            group_value = str(row.get(group_column, "") or "").strip()
            raw_value = str(row.get(outcome_column, "") or "").strip()
            if self._is_missing(group_value) or self._is_missing(raw_value):
                continue
            numeric_values = self._parse_numeric_values([raw_value])
            if not numeric_values:
                continue
            grouped_values.setdefault(group_value, []).append(numeric_values[0])

        return dict(
            sorted(
                grouped_values.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
        )

    def _rank_grouped_values(
        self,
        grouped_values: dict[str, list[float]],
    ) -> list[tuple[str, float, float]]:
        sorted_values = sorted(
            [
                (label, value)
                for label, values in grouped_values.items()
                for value in values
            ],
            key=lambda item: item[1],
        )
        ranked_values: list[tuple[str, float, float]] = []
        index = 0
        while index < len(sorted_values):
            tie_end = index + 1
            while tie_end < len(sorted_values) and sorted_values[tie_end][1] == sorted_values[index][1]:
                tie_end += 1
            average_rank = (index + 1 + tie_end) / 2
            for tie_index in range(index, tie_end):
                label, value = sorted_values[tie_index]
                ranked_values.append((label, value, average_rank))
            index = tie_end
        return ranked_values

    def _rank_plain_values(self, values: list[float]) -> list[float]:
        sorted_values = sorted(enumerate(values), key=lambda item: item[1])
        ranks = [0.0] * len(values)
        index = 0
        while index < len(sorted_values):
            tie_end = index + 1
            while tie_end < len(sorted_values) and sorted_values[tie_end][1] == sorted_values[index][1]:
                tie_end += 1
            average_rank = (index + 1 + tie_end) / 2
            for tie_index in range(index, tie_end):
                original_index, _value = sorted_values[tie_index]
                ranks[original_index] = average_rank
            index = tie_end
        return ranks

    def _rank_tie_correction(self, ranked_values: list[tuple[str, float, float]]) -> float:
        total_n = len(ranked_values)
        denominator = total_n**3 - total_n
        if denominator <= 0:
            return 0

        value_counts = Counter(value for _label, value, _rank in ranked_values)
        tie_sum = sum(count**3 - count for count in value_counts.values() if count > 1)
        return 1 - tie_sum / denominator

    def _build_tukey_pairwise_results(
        self,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        df_within = sum(len(values) - 1 for values in grouped_values.values())
        ss_within = sum(
            sum((value - fmean(values)) ** 2 for value in values)
            for values in grouped_values.values()
        )
        if df_within <= 0 or ss_within <= 0:
            return self._build_pairwise_welch_results(
                grouped_values,
                test_name="Tukey HSD 近似比较未执行，改用两两 Welch t 检验",
                multiplicity_correction=multiplicity_correction,
            )

        mse = ss_within / df_within
        for first_label, second_label in combinations(grouped_values.keys(), 2):
            first_values = grouped_values[first_label]
            second_values = grouped_values[second_label]
            if len(first_values) < 2 or len(second_values) < 2:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="Tukey HSD 近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 有效样本量不足，未执行 Tukey 风格比较。",
                        warnings=["每个分组至少需要 2 个有效数值。"],
                    )
                )
                continue

            mean_difference = fmean(first_values) - fmean(second_values)
            standard_error = sqrt(mse / 2 * (1 / len(first_values) + 1 / len(second_values)))
            if standard_error <= 0:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="Tukey HSD 近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 的 pooled MSE 无法支持两两比较。",
                        warnings=["常数列或完全无组内变异不适合做 Tukey 风格比较。"],
                    )
                )
                continue

            q_statistic = abs(mean_difference) / standard_error
            studentized_range_p_value = self._studentized_range_survival(
                statistic=q_statistic,
                group_count=len(grouped_values),
                degrees_of_freedom=df_within,
            )
            if studentized_range_p_value is None:
                t_like_statistic = q_statistic / sqrt(2)
                p_value = self._student_t_two_sided_p_value(t_like_statistic, df_within)
                p_value_warning = (
                    "Tukey HSD 的 studentized range 分布不可用，当前 P 值使用 t 分布近似；"
                    "正式报告前需用统计软件复核。"
                )
            else:
                p_value = studentized_range_p_value
                p_value_warning = "Tukey HSD P 值使用 scipy.stats.studentized_range 分布计算。"
            effect_size = self._cohens_d(first_values, second_values)
            results.append(
                PairwiseComparisonResult(
                    group_a=first_label,
                    group_b=second_label,
                    test_name="Tukey HSD 近似比较",
                    status="completed",
                    statistic=round(q_statistic, 6),
                    degrees_of_freedom=float(df_within),
                    p_value=round(p_value, 8),
                    effect_size=round(effect_size, 6),
                    interpretation=(
                        f"{first_label} vs {second_label}：Tukey HSD 风格 q={round(q_statistic, 4)}，"
                        f"原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=[
                        p_value_warning,
                        self._multiplicity_warning(multiplicity_correction),
                    ],
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _build_games_howell_pairwise_results(
        self,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        group_count = len(grouped_values)
        for first_label, second_label in combinations(grouped_values.keys(), 2):
            first_values = grouped_values[first_label]
            second_values = grouped_values[second_label]
            if len(first_values) < 2 or len(second_values) < 2:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="Games-Howell 近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 有效样本量不足，未执行 Games-Howell 比较。",
                        warnings=["每个分组至少需要 2 个有效数值。"],
                    )
                )
                continue

            first_variance = self._sample_variance(first_values)
            second_variance = self._sample_variance(second_values)
            first_term = first_variance / len(first_values)
            second_term = second_variance / len(second_values)
            standard_error_squared = 0.5 * (first_term + second_term)
            if standard_error_squared <= 0:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="Games-Howell 近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 组内方差为 0，未执行 Games-Howell 比较。",
                        warnings=["常数列或完全无组内变异不适合做均值差异比较。"],
                    )
                )
                continue

            mean_difference = fmean(first_values) - fmean(second_values)
            q_statistic = abs(mean_difference) / sqrt(standard_error_squared)
            degrees_of_freedom = self._welch_degrees_of_freedom(
                first_variance=first_variance,
                first_n=len(first_values),
                second_variance=second_variance,
                second_n=len(second_values),
            )
            studentized_range_p_value = self._studentized_range_survival(
                statistic=q_statistic,
                group_count=group_count,
                degrees_of_freedom=degrees_of_freedom,
            )
            if studentized_range_p_value is None:
                t_like_statistic = q_statistic / sqrt(2)
                p_value = self._student_t_two_sided_p_value(t_like_statistic, degrees_of_freedom)
                p_value_warning = (
                    "Games-Howell 的 studentized range 分布不可用，当前 P 值使用 Welch t 分布近似；"
                    "正式报告前需用统计软件复核。"
                )
            else:
                p_value = studentized_range_p_value
                p_value_warning = "Games-Howell P 值使用 scipy.stats.studentized_range 分布计算。"
            effect_size = self._cohens_d(first_values, second_values)

            results.append(
                PairwiseComparisonResult(
                    group_a=first_label,
                    group_b=second_label,
                    test_name="Games-Howell 近似比较",
                    status="completed",
                    statistic=round(q_statistic, 6),
                    degrees_of_freedom=round(degrees_of_freedom, 6),
                    p_value=round(p_value, 8),
                    effect_size=round(effect_size, 6),
                    interpretation=(
                        f"{first_label} vs {second_label}：Games-Howell q={round(q_statistic, 4)}，"
                        f"df={round(degrees_of_freedom, 2)}，原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=[
                        p_value_warning,
                        self._multiplicity_warning(multiplicity_correction),
                    ],
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _build_dunn_pairwise_results(
        self,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str,
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        ranked_values = self._rank_grouped_values(grouped_values)
        total_n = len(ranked_values)
        tie_correction = self._rank_tie_correction(ranked_values)
        if total_n <= 1 or tie_correction <= 0:
            return results

        rank_sums: dict[str, float] = {label: 0.0 for label in grouped_values}
        for label, _value, rank in ranked_values:
            rank_sums[label] += rank

        for first_label, second_label in combinations(grouped_values.keys(), 2):
            first_n = len(grouped_values[first_label])
            second_n = len(grouped_values[second_label])
            if first_n < 1 or second_n < 1:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="Dunn 近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 有效样本量不足，未执行 Dunn 比较。",
                        warnings=["每个分组至少需要 1 个有效数值。"],
                    )
                )
                continue

            mean_rank_difference = rank_sums[first_label] / first_n - rank_sums[second_label] / second_n
            standard_error = sqrt(total_n * (total_n + 1) / 12 * (1 / first_n + 1 / second_n) * tie_correction)
            if standard_error <= 0:
                continue
            statistic = mean_rank_difference / standard_error
            p_value = self._normal_two_sided_p_value(statistic)
            effect_size = abs(statistic) / sqrt(total_n)
            results.append(
                PairwiseComparisonResult(
                    group_a=first_label,
                    group_b=second_label,
                    test_name="Dunn 近似比较",
                    status="completed",
                    statistic=round(statistic, 6),
                    p_value=round(p_value, 8),
                    effect_size=round(effect_size, 6),
                    interpretation=(
                        f"{first_label} vs {second_label}：Dunn 近似 Z={round(statistic, 4)}，"
                        f"原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=[
                        "Dunn 比较使用全局秩和正态近似；正式报告前需用统计软件复核。",
                        self._multiplicity_warning(multiplicity_correction),
                    ],
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _build_pairwise_signed_rank_results(
        self,
        complete_subject_values: list[dict[str, float]],
        condition_values: list[str],
        multiplicity_correction: str,
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        for first_condition, second_condition in combinations(condition_values, 2):
            differences = [
                values_by_condition[second_condition] - values_by_condition[first_condition]
                for values_by_condition in complete_subject_values
            ]
            non_zero_differences = [difference for difference in differences if difference != 0]
            if len(non_zero_differences) < 2:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_condition,
                        group_b=second_condition,
                        test_name="配对秩和近似比较",
                        status="blocked",
                        interpretation=(
                            f"{first_condition} 与 {second_condition} 的非零配对差值不足，"
                            "未执行 Friedman 事后配对秩和比较。"
                        ),
                        warnings=["配对秩和近似比较至少需要 2 个非零配对差值。"],
                    )
                )
                continue

            absolute_differences = [abs(difference) for difference in non_zero_differences]
            ranks = self._rank_plain_values(absolute_differences)
            positive_rank_sum = sum(
                rank
                for difference, rank in zip(non_zero_differences, ranks)
                if difference > 0
            )
            sample_size = len(non_zero_differences)
            expected_rank_sum = sample_size * (sample_size + 1) / 4
            tie_counts = Counter(absolute_differences)
            tie_sum = sum(count**3 - count for count in tie_counts.values() if count > 1)
            variance = sample_size * (sample_size + 1) * (2 * sample_size + 1) / 24 - tie_sum / 48
            if variance <= 0:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_condition,
                        group_b=second_condition,
                        test_name="配对秩和近似比较",
                        status="blocked",
                        interpretation=(
                            f"{first_condition} 与 {second_condition} 的配对差值秩方差为 0，"
                            "未执行事后比较。"
                        ),
                        warnings=["常数差值或完全相同的绝对差值不适合做配对秩和近似比较。"],
                    )
                )
                continue

            statistic = (positive_rank_sum - expected_rank_sum) / sqrt(variance)
            scipy_p_value = self._wilcoxon_two_sided_p_value(non_zero_differences)
            p_value = scipy_p_value if scipy_p_value is not None else self._normal_two_sided_p_value(statistic)
            effect_size = abs(statistic) / sqrt(sample_size)
            warnings = [
                self._multiplicity_warning(multiplicity_correction),
            ]
            if scipy_p_value is not None:
                warnings.insert(
                    0,
                    "Friedman 事后比较 P 值由 scipy.stats.wilcoxon 计算；Z 和效应量为正态近似辅助指标。",
                )
            else:
                warnings.insert(
                    0,
                    "Friedman 事后比较使用 Wilcoxon signed-rank 正态近似；正式报告前需用统计软件复核。",
                )
            zero_difference_count = len(differences) - sample_size
            if zero_difference_count:
                warnings.append(f"已忽略 {zero_difference_count} 个零差值配对。")
            if sample_size < 10:
                warnings.append("非零配对数小于 10，正态近似 P 值需要谨慎解释。")
            if tie_sum > 0:
                warnings.append("绝对差值中存在相同数值，已在方差估计中考虑 ties correction。")

            results.append(
                PairwiseComparisonResult(
                    group_a=first_condition,
                    group_b=second_condition,
                    test_name="配对秩和近似比较",
                    status="completed",
                    statistic=round(statistic, 6),
                    p_value=round(p_value, 8),
                    effect_size=round(effect_size, 6),
                    interpretation=(
                        f"{first_condition} vs {second_condition}：配对秩和近似 Z={round(statistic, 4)}，"
                        f"原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=warnings,
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _build_pairwise_welch_results(
        self,
        grouped_values: dict[str, list[float]],
        test_name: str = "两两 Welch t 检验",
        extra_warning: str | None = None,
        multiplicity_correction: str = "holm",
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        for first_label, second_label in combinations(grouped_values.keys(), 2):
            first_values = grouped_values[first_label]
            second_values = grouped_values[second_label]
            if len(first_values) < 2 or len(second_values) < 2:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name=test_name,
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 有效样本量不足，未执行两两比较。",
                        warnings=["每个分组至少需要 2 个有效数值。"],
                    )
                )
                continue

            first_variance = self._sample_variance(first_values)
            second_variance = self._sample_variance(second_values)
            standard_error_squared = first_variance / len(first_values) + second_variance / len(second_values)
            if standard_error_squared <= 0:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name=test_name,
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 组内方差为 0，未执行两两比较。",
                        warnings=["常数列或完全无组内变异不适合做均值差异检验。"],
                    )
                )
                continue

            statistic = (fmean(first_values) - fmean(second_values)) / sqrt(standard_error_squared)
            degrees_of_freedom = self._welch_degrees_of_freedom(
                first_variance=first_variance,
                first_n=len(first_values),
                second_variance=second_variance,
                second_n=len(second_values),
            )
            p_value = self._student_t_two_sided_p_value(statistic, degrees_of_freedom)
            effect_size = self._cohens_d(first_values, second_values)
            warnings = [self._multiplicity_warning(multiplicity_correction)]
            if extra_warning:
                warnings.insert(0, extra_warning)
            if min(len(first_values), len(second_values)) < 10:
                warnings.append("至少一个分组样本量小于 10，两两比较需要谨慎解释。")

            results.append(
                PairwiseComparisonResult(
                    group_a=first_label,
                    group_b=second_label,
                    test_name=test_name,
                    status="completed",
                    statistic=round(statistic, 6),
                    degrees_of_freedom=round(degrees_of_freedom, 6),
                    p_value=round(p_value, 8),
                    effect_size=round(effect_size, 6),
                    interpretation=(
                        f"{first_label} vs {second_label}：Welch t={round(statistic, 4)}，"
                        f"原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=warnings,
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _build_pairwise_rank_sum_results(
        self,
        grouped_values: dict[str, list[float]],
        multiplicity_correction: str = "holm",
    ) -> list[PairwiseComparisonResult]:
        results: list[PairwiseComparisonResult] = []
        for first_label, second_label in combinations(grouped_values.keys(), 2):
            subset = {
                first_label: grouped_values[first_label],
                second_label: grouped_values[second_label],
            }
            first_values = subset[first_label]
            second_values = subset[second_label]
            first_n = len(first_values)
            second_n = len(second_values)
            if first_n < 1 or second_n < 1:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="两两秩和近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 有效样本量不足，未执行秩和比较。",
                        warnings=["每个分组至少需要 1 个有效数值。"],
                    )
                )
                continue

            ranked_values = self._rank_grouped_values(subset)
            total_n = len(ranked_values)
            rank_sum_first = sum(rank for label, _value, rank in ranked_values if label == first_label)
            u_first = rank_sum_first - first_n * (first_n + 1) / 2
            u_second = first_n * second_n - u_first
            tie_counts = Counter(value for _label, value, _rank in ranked_values)
            tie_sum = sum(count**3 - count for count in tie_counts.values() if count > 1)
            variance = first_n * second_n / 12 * (
                total_n + 1 - tie_sum / (total_n * (total_n - 1))
            )
            if variance <= 0:
                results.append(
                    PairwiseComparisonResult(
                        group_a=first_label,
                        group_b=second_label,
                        test_name="两两秩和近似比较",
                        status="blocked",
                        interpretation=f"{first_label} 与 {second_label} 数值完全相同，未执行秩和比较。",
                        warnings=["常数列或完全相同的结局值不适合做秩和检验。"],
                    )
                )
                continue

            mean_u = first_n * second_n / 2
            statistic = (u_first - mean_u) / sqrt(variance)
            p_value = self._normal_two_sided_p_value(statistic)
            rank_biserial = 1 - (2 * min(u_first, u_second) / (first_n * second_n))
            warnings = [
                f"两两秩和比较使用正态近似；{self._multiplicity_warning(multiplicity_correction)}",
            ]
            if min(first_n, second_n) < 5:
                warnings.append("至少一个分组样本量小于 5，正态近似 P 值需要谨慎解释。")
            if tie_sum > 0:
                warnings.append("数据中存在相同数值，已在方差估计中考虑 ties correction。")

            results.append(
                PairwiseComparisonResult(
                    group_a=first_label,
                    group_b=second_label,
                    test_name="两两秩和近似比较",
                    status="completed",
                    statistic=round(statistic, 6),
                    p_value=round(p_value, 8),
                    effect_size=round(rank_biserial, 6),
                    interpretation=(
                        f"{first_label} vs {second_label}：秩和近似 Z={round(statistic, 4)}，"
                        f"原始 P={self._format_p_value(p_value)}。"
                    ),
                    warnings=warnings,
                )
            )

        self._apply_multiplicity_correction(results, multiplicity_correction)
        self._refresh_pairwise_interpretations(results)
        return results

    def _apply_multiplicity_correction(
        self,
        results: list[PairwiseComparisonResult],
        multiplicity_correction: str,
    ) -> None:
        if multiplicity_correction == "fdr":
            self._apply_benjamini_hochberg_fdr(results)
            return
        self._apply_holm_bonferroni(results)

    def _multiplicity_warning(self, multiplicity_correction: str) -> str:
        if multiplicity_correction == "fdr":
            return "Benjamini-Hochberg FDR 校正用于控制假发现率，适合探索性或多指标场景。"
        return "Holm-Bonferroni 校正用于保守控制多重比较风险。"

    def _apply_holm_bonferroni(self, results: list[PairwiseComparisonResult]) -> None:
        completed_results = [
            (index, result.p_value)
            for index, result in enumerate(results)
            if result.status == "completed" and result.p_value is not None
        ]
        ordered_results = sorted(completed_results, key=lambda item: item[1])
        running_adjusted_p = 0.0
        test_count = len(ordered_results)
        for order_index, (result_index, p_value) in enumerate(ordered_results):
            adjusted_p = min((test_count - order_index) * p_value, 1)
            running_adjusted_p = max(running_adjusted_p, adjusted_p)
            results[result_index].adjusted_p_value = round(running_adjusted_p, 8)
            results[result_index].correction_method = "Holm-Bonferroni"

    def _apply_benjamini_hochberg_fdr(self, results: list[PairwiseComparisonResult]) -> None:
        completed_results = [
            (index, result.p_value)
            for index, result in enumerate(results)
            if result.status == "completed" and result.p_value is not None
        ]
        ordered_results = sorted(completed_results, key=lambda item: item[1])
        test_count = len(ordered_results)
        running_adjusted_p = 1.0
        for reverse_rank, (result_index, p_value) in enumerate(reversed(ordered_results), start=1):
            rank = test_count - reverse_rank + 1
            adjusted_p = min(p_value * test_count / rank, 1)
            running_adjusted_p = min(running_adjusted_p, adjusted_p)
            results[result_index].adjusted_p_value = round(running_adjusted_p, 8)
            results[result_index].correction_method = "Benjamini-Hochberg FDR"

    def _refresh_pairwise_interpretations(self, results: list[PairwiseComparisonResult]) -> None:
        for result in results:
            if result.status != "completed" or result.adjusted_p_value is None:
                continue
            correction_label = (
                "FDR"
                if result.correction_method == "Benjamini-Hochberg FDR"
                else "Holm"
            )
            result.interpretation = (
                f"{result.group_a} vs {result.group_b}：{result.test_name}，"
                f"原始 P={self._format_p_value(result.p_value or 1)}，"
                f"{correction_label} 校正后 P={self._format_p_value(result.adjusted_p_value)}。"
            )

    def _eta_squared_from_grouped_values(self, grouped_values: dict[str, list[float]]) -> float:
        all_values = [
            value
            for values in grouped_values.values()
            for value in values
        ]
        if not all_values:
            return 0

        grand_mean = fmean(all_values)
        group_means = {
            label: fmean(values)
            for label, values in grouped_values.items()
        }
        ss_between = sum(
            len(values) * (group_means[label] - grand_mean) ** 2
            for label, values in grouped_values.items()
        )
        ss_total = sum((value - grand_mean) ** 2 for value in all_values)
        if ss_total <= 0:
            return 0
        return ss_between / ss_total

    def _sample_variance(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0
        mean_value = fmean(values)
        return sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)

    def _welch_degrees_of_freedom(
        self,
        first_variance: float,
        first_n: int,
        second_variance: float,
        second_n: int,
    ) -> float:
        first_term = first_variance / first_n
        second_term = second_variance / second_n
        numerator = (first_term + second_term) ** 2
        denominator = (first_term**2 / (first_n - 1)) + (second_term**2 / (second_n - 1))
        if denominator <= 0:
            return float(first_n + second_n - 2)
        return numerator / denominator

    def _student_t_two_sided_p_value(self, statistic: float, degrees_of_freedom: float) -> float:
        if degrees_of_freedom <= 0:
            return 1
        abs_statistic = abs(statistic)
        if abs_statistic == 0:
            return 1
        if scipy_stats is not None:
            try:
                return self._clamp_probability(float(scipy_stats.t.sf(abs_statistic, degrees_of_freedom) * 2))
            except (FloatingPointError, ValueError):
                pass
        if abs_statistic >= 20:
            return 0

        step_count = max(200, min(4000, int(abs_statistic * 300)))
        if step_count % 2:
            step_count += 1
        step = abs_statistic / step_count

        area = self._student_t_pdf(0, degrees_of_freedom) + self._student_t_pdf(
            abs_statistic,
            degrees_of_freedom,
        )
        for index in range(1, step_count):
            weight = 4 if index % 2 else 2
            area += weight * self._student_t_pdf(index * step, degrees_of_freedom)
        area *= step / 3

        cdf = min(0.5 + area, 1)
        return max(2 * (1 - cdf), 0)

    def _student_t_pdf(self, value: float, degrees_of_freedom: float) -> float:
        log_coefficient = (
            lgamma((degrees_of_freedom + 1) / 2)
            - lgamma(degrees_of_freedom / 2)
            - 0.5 * (log(degrees_of_freedom) + log(pi))
        )
        log_kernel = -((degrees_of_freedom + 1) / 2) * log(1 + value**2 / degrees_of_freedom)
        return exp(log_coefficient + log_kernel)

    def _f_distribution_survival(
        self,
        statistic: float,
        numerator_df: float,
        denominator_df: float,
    ) -> float:
        if statistic <= 0 or numerator_df <= 0 or denominator_df <= 0:
            return 1
        if scipy_stats is not None:
            try:
                return self._clamp_probability(float(scipy_stats.f.sf(statistic, numerator_df, denominator_df)))
            except (FloatingPointError, ValueError):
                pass

        numerator = numerator_df * statistic
        x_value = numerator / (numerator + denominator_df)
        cdf = self._regularized_incomplete_beta(
            x_value,
            numerator_df / 2,
            denominator_df / 2,
        )
        cdf = max(0, min(cdf, 1))
        return max(1 - cdf, 0)

    def _chi_square_survival(self, statistic: float, degrees_of_freedom: int) -> float:
        if statistic <= 0 or degrees_of_freedom <= 0:
            return 1
        if scipy_stats is not None:
            try:
                return self._clamp_probability(float(scipy_stats.chi2.sf(statistic, degrees_of_freedom)))
            except (FloatingPointError, ValueError):
                pass
        survival = self._regularized_gamma_q(
            degrees_of_freedom / 2,
            statistic / 2,
        )
        return max(0, min(survival, 1))

    def _normal_two_sided_p_value(self, statistic: float) -> float:
        abs_statistic = abs(statistic)
        if scipy_stats is not None:
            try:
                return self._clamp_probability(float(scipy_stats.norm.sf(abs_statistic) * 2))
            except (FloatingPointError, ValueError):
                pass
        cdf = 0.5 * (1 + erf(abs_statistic / sqrt(2)))
        return max(2 * (1 - cdf), 0)

    def _studentized_range_survival(
        self,
        statistic: float,
        group_count: int,
        degrees_of_freedom: float,
    ) -> float | None:
        if statistic <= 0:
            return 1
        if group_count <= 1 or degrees_of_freedom <= 0:
            return None
        if scipy_stats is None or not hasattr(scipy_stats, "studentized_range"):
            return None
        try:
            return self._clamp_probability(
                float(scipy_stats.studentized_range.sf(statistic, group_count, degrees_of_freedom))
            )
        except (FloatingPointError, ValueError):
            return None

    def _wilcoxon_two_sided_p_value(self, differences: list[float]) -> float | None:
        if scipy_stats is None or not hasattr(scipy_stats, "wilcoxon"):
            return None
        try:
            result = scipy_stats.wilcoxon(
                differences,
                zero_method="wilcox",
                correction=False,
                alternative="two-sided",
                method="auto",
            )
            return self._clamp_probability(float(result.pvalue))
        except (FloatingPointError, TypeError, ValueError):
            return None

    def _clamp_probability(self, value: float) -> float:
        if value != value:
            return 1
        return max(0, min(value, 1))

    def _regularized_incomplete_beta(self, x_value: float, alpha: float, beta: float) -> float:
        if x_value <= 0:
            return 0
        if x_value >= 1:
            return 1

        log_beta_factor = (
            lgamma(alpha + beta)
            - lgamma(alpha)
            - lgamma(beta)
            + alpha * log(x_value)
            + beta * log(1 - x_value)
        )
        beta_factor = exp(log_beta_factor)
        if x_value < (alpha + 1) / (alpha + beta + 2):
            return beta_factor * self._beta_continued_fraction(alpha, beta, x_value) / alpha
        return 1 - beta_factor * self._beta_continued_fraction(beta, alpha, 1 - x_value) / beta

    def _beta_continued_fraction(self, alpha: float, beta: float, x_value: float) -> float:
        max_iterations = 200
        epsilon = 3e-12
        tiny = 1e-30

        qab = alpha + beta
        qap = alpha + 1
        qam = alpha - 1
        c_value = 1
        d_value = 1 - qab * x_value / qap
        if abs(d_value) < tiny:
            d_value = tiny
        d_value = 1 / d_value
        h_value = d_value

        for iteration in range(1, max_iterations + 1):
            double_iteration = 2 * iteration
            coefficient = (
                iteration
                * (beta - iteration)
                * x_value
                / ((qam + double_iteration) * (alpha + double_iteration))
            )
            d_value = 1 + coefficient * d_value
            if abs(d_value) < tiny:
                d_value = tiny
            c_value = 1 + coefficient / c_value
            if abs(c_value) < tiny:
                c_value = tiny
            d_value = 1 / d_value
            h_value *= d_value * c_value

            coefficient = (
                -(alpha + iteration)
                * (qab + iteration)
                * x_value
                / ((alpha + double_iteration) * (qap + double_iteration))
            )
            d_value = 1 + coefficient * d_value
            if abs(d_value) < tiny:
                d_value = tiny
            c_value = 1 + coefficient / c_value
            if abs(c_value) < tiny:
                c_value = tiny
            d_value = 1 / d_value
            delta = d_value * c_value
            h_value *= delta
            if abs(delta - 1) < epsilon:
                break

        return h_value

    def _regularized_gamma_q(self, alpha: float, x_value: float) -> float:
        if alpha <= 0:
            return 1
        if x_value <= 0:
            return 1
        if x_value < alpha + 1:
            return 1 - self._regularized_gamma_p_series(alpha, x_value)
        return self._regularized_gamma_q_continued_fraction(alpha, x_value)

    def _regularized_gamma_p_series(self, alpha: float, x_value: float) -> float:
        epsilon = 3e-12
        term = 1 / alpha
        total = term
        current_alpha = alpha
        for _iteration in range(200):
            current_alpha += 1
            term *= x_value / current_alpha
            total += term
            if abs(term) < abs(total) * epsilon:
                break
        return total * exp(-x_value + alpha * log(x_value) - lgamma(alpha))

    def _regularized_gamma_q_continued_fraction(self, alpha: float, x_value: float) -> float:
        epsilon = 3e-12
        tiny = 1e-30
        b_value = x_value + 1 - alpha
        c_value = 1 / tiny
        d_value = 1 / b_value if abs(b_value) > tiny else 1 / tiny
        h_value = d_value

        for iteration in range(1, 200):
            coefficient = -iteration * (iteration - alpha)
            b_value += 2
            d_value = coefficient * d_value + b_value
            if abs(d_value) < tiny:
                d_value = tiny
            c_value = b_value + coefficient / c_value
            if abs(c_value) < tiny:
                c_value = tiny
            d_value = 1 / d_value
            delta = d_value * c_value
            h_value *= delta
            if abs(delta - 1) < epsilon:
                break

        return exp(-x_value + alpha * log(x_value) - lgamma(alpha)) * h_value

    def _cohens_d(self, first_values: list[float], second_values: list[float]) -> float:
        first_variance = self._sample_variance(first_values)
        second_variance = self._sample_variance(second_values)
        pooled_denominator = len(first_values) + len(second_values) - 2
        if pooled_denominator <= 0:
            return 0
        pooled_variance = (
            (len(first_values) - 1) * first_variance
            + (len(second_values) - 1) * second_variance
        ) / pooled_denominator
        if pooled_variance <= 0:
            return 0
        return (fmean(first_values) - fmean(second_values)) / sqrt(pooled_variance)

    def _format_p_value(self, p_value: float) -> str:
        if p_value < 0.001:
            return "<0.001"
        return str(round(p_value, 4))

    def _build_reproducible_script(
        self,
        file_name: str,
        selected_outcomes: list[str],
        group_column: str | None,
        chart_specs: list[ChartSpec],
    ) -> ReproducibleAnalysisScript:
        outcome_columns_json = json.dumps(selected_outcomes, ensure_ascii=False)
        group_column_json = json.dumps(group_column, ensure_ascii=False)
        chart_ids_json = json.dumps([chart.id for chart in chart_specs], ensure_ascii=False)
        script_file_name = self._build_script_file_name(file_name)
        script = f'''from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path


# Replace this with the local path to your de-identified CSV.
INPUT_CSV = Path({json.dumps(file_name, ensure_ascii=False)})
OUTCOME_COLUMNS = {outcome_columns_json}
GROUP_COLUMN = {group_column_json}
EXPECTED_CHART_IDS = {chart_ids_json}
MISSING_TOKENS = {{"", "na", "n/a", "nan", "null", "none", "-", "--"}}


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    raise RuntimeError("CSV encoding is not UTF-8/GBK compatible.")


def is_missing(value: str) -> bool:
    return value.strip().lower() in MISSING_TOKENS


def parse_float(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def numeric_values(rows: list[dict[str, str]], column: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw_value = str(row.get(column, "") or "").strip()
        if is_missing(raw_value):
            continue
        parsed = parse_float(raw_value)
        if parsed is not None:
            values.append(parsed)
    return values


def describe(rows: list[dict[str, str]], column: str) -> dict[str, float | int | str]:
    values = numeric_values(rows, column)
    if not values:
        return {{"column": column, "n": 0, "missing_count": len(rows)}}
    return {{
        "column": column,
        "n": len(values),
        "missing_count": len(rows) - len(values),
        "mean": round(statistics.fmean(values), 4),
        "std_dev": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
        "median": round(statistics.median(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }}


def grouped_describe(rows: list[dict[str, str]], column: str, group_column: str) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = {{}}
    for row in rows:
        group_value = str(row.get(group_column, "") or "").strip()
        if is_missing(group_value):
            continue
        grouped.setdefault(group_value, []).append(row)
    return [
        {{"group_value": group_value, **describe(group_rows, column)}}
        for group_value, group_rows in sorted(grouped.items())
    ]


def histogram_bins(values: list[float]) -> list[dict[str, float | int | str]]:
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return [{{"label": str(round(min_value, 2)), "value": len(values)}}]

    bin_count = max(3, min(8, round(math.sqrt(len(values)))))
    bin_width = (max_value - min_value) / bin_count
    counts = [0 for _ in range(bin_count)]
    for value in values:
        index = min(int((value - min_value) / bin_width), bin_count - 1)
        counts[index] += 1
    return [
        {{
            "label": f"{{round(min_value + index * bin_width, 2)}}-{{round(min_value + (index + 1) * bin_width, 2)}}",
            "value": count,
        }}
        for index, count in enumerate(counts)
    ]


def main() -> None:
    rows = read_csv(INPUT_CSV)
    missing_columns = [column for column in OUTCOME_COLUMNS if rows and column not in rows[0]]
    if GROUP_COLUMN and rows and GROUP_COLUMN not in rows[0]:
        missing_columns.append(GROUP_COLUMN)
    if missing_columns:
        raise RuntimeError(f"Missing expected columns: {{', '.join(missing_columns)}}")

    descriptive_statistics = [describe(rows, column) for column in OUTCOME_COLUMNS]
    group_statistics = {{}}
    if GROUP_COLUMN:
        group_statistics = {{
            column: grouped_describe(rows, column, GROUP_COLUMN)
            for column in OUTCOME_COLUMNS
        }}

    chart_data = {{
        f"hist-{{column}}": histogram_bins(numeric_values(rows, column))
        for column in OUTCOME_COLUMNS[:2]
    }}

    result = {{
        "source_file": str(INPUT_CSV),
        "row_count": len(rows),
        "outcome_columns": OUTCOME_COLUMNS,
        "group_column": GROUP_COLUMN,
        "descriptive_statistics": descriptive_statistics,
        "group_statistics": group_statistics,
        "chart_data": chart_data,
        "expected_chart_ids_from_app": EXPECTED_CHART_IDS,
        "notes": [
            "This script reproduces descriptive summaries from a local de-identified CSV.",
            "It does not calculate P values. Confirm design, distribution, variance assumptions, and multiplicity before formal testing.",
            "The SCI-helper prototype does not store the original CSV.",
        ],
    }}

    output_path = INPUT_CSV.with_suffix(".analysis-summary.json")
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {{output_path}}")
    print(json.dumps(descriptive_statistics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
        return ReproducibleAnalysisScript(
            file_name=script_file_name,
            script=script,
            input_file_placeholder=file_name,
            instructions=[
                "将脚本保存到本地后，把 INPUT_CSV 改成脱敏 CSV 的实际路径。",
                "运行 `python script_name.py`，会生成 `.analysis-summary.json` 复核文件。",
                "脚本只复现描述性统计和基础图表数据，不自动计算 P 值。",
            ],
            safety_notes=[
                "请只在本地受控环境运行脚本。",
                "脚本不会上传数据，也不需要联网。",
                "如 CSV 含直接身份标识，请先完成脱敏后再运行。",
            ],
        )

    def _build_script_file_name(self, file_name: str) -> str:
        stem = file_name.rsplit(".", 1)[0]
        normalized = self._normalize(stem) or "analysis"
        return f"{normalized}-reproducible-analysis.py"

    def _build_chart_specs(
        self,
        rows: list[dict[str, str]],
        numeric_summaries: list[DescriptiveStatistic],
        categorical_summaries: list[CategoricalSummary],
        group_comparisons: list[GroupComparisonDraft],
    ) -> list[ChartSpec]:
        charts: list[ChartSpec] = []

        for summary in numeric_summaries[:2]:
            chart = self._build_histogram_chart(summary.column, rows)
            if chart is not None:
                charts.append(chart)

        if categorical_summaries:
            charts.append(self._build_categorical_chart(categorical_summaries[0]))

        for comparison in group_comparisons[:2]:
            chart = self._build_group_mean_chart(comparison)
            if chart is not None:
                charts.append(chart)

        return charts[:4]

    def _build_histogram_chart(
        self,
        column_name: str,
        rows: list[dict[str, str]],
    ) -> ChartSpec | None:
        values = self._parse_numeric_values(
            [
                str(row.get(column_name, "") or "").strip()
                for row in rows
                if not self._is_missing(str(row.get(column_name, "") or "").strip())
            ]
        )
        if not values:
            return None

        min_value = min(values)
        max_value = max(values)
        if min_value == max_value:
            return ChartSpec(
                id=f"hist-{self._normalize(column_name)}",
                title=f"{column_name} distribution",
                chart_type="histogram",
                x_label=column_name,
                y_label="Record count",
                points=[
                    ChartDataPoint(
                        label=str(round(min_value, 2)),
                        value=len(values),
                        note="All non-missing values are identical",
                    )
                ],
                narrative=f"All non-missing records for {column_name} had the same value: {round(min_value, 4)}.",
            )

        bin_count = max(3, min(8, round(sqrt(len(values)))))
        bin_width = (max_value - min_value) / bin_count
        counts = [0 for _ in range(bin_count)]
        for value in values:
            index = min(int((value - min_value) / bin_width), bin_count - 1)
            counts[index] += 1

        points = []
        for index, count in enumerate(counts):
            start = min_value + index * bin_width
            end = start + bin_width
            points.append(
                ChartDataPoint(
                    label=f"{round(start, 2)}-{round(end, 2)}",
                    value=count,
                )
            )

        return ChartSpec(
            id=f"hist-{self._normalize(column_name)}",
            title=f"{column_name} distribution",
            chart_type="histogram",
            x_label=column_name,
            y_label="Record count",
            points=points,
            narrative=f"The observed range for {column_name} was {round(min_value, 4)} to {round(max_value, 4)}.",
        )

    def _build_categorical_chart(self, summary: CategoricalSummary) -> ChartSpec:
        return ChartSpec(
            id=f"cat-{self._normalize(summary.column)}",
            title=f"{summary.column} composition",
            chart_type="bar",
            x_label=summary.column,
            y_label="Record count",
            points=[
                ChartDataPoint(
                    label=level.value,
                    value=level.count,
                    note=f"{level.percent}%",
                )
                for level in summary.levels[:8]
            ],
            narrative=f"The chart displays the first {min(len(summary.levels), 8)} category level(s) for {summary.column}.",
        )

    def _build_group_mean_chart(self, comparison: GroupComparisonDraft) -> ChartSpec | None:
        if not comparison.groups:
            return None

        return ChartSpec(
            id=f"group-{self._normalize(comparison.group_column)}-{self._normalize(comparison.column)}",
            title=f"{comparison.column} grouped mean",
            chart_type="bar",
            x_label=comparison.group_column,
            y_label=comparison.column,
            points=[
                ChartDataPoint(
                    label=group.group_value,
                    value=group.mean,
                    note=f"n={group.n}",
                )
                for group in comparison.groups
            ],
            narrative=comparison.interpretation,
        )

    def _infer_type(self, present_values: list[str], numeric_values: list[float]) -> str:
        if not present_values:
            return "empty"
        if len(numeric_values) / len(present_values) >= 0.8:
            return "numeric"
        if sum(1 for value in present_values if self._looks_like_date(value)) / len(present_values) >= 0.8:
            return "date"
        return "text"

    def _looks_like_date(self, value: str) -> bool:
        return bool(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", value))

    def _build_privacy_report(
        self,
        headers: list[str],
        rows: list[dict[str, str]],
        columns: list[DataColumnQuality],
    ) -> DataPrivacyReport:
        findings: list[DataPrivacyFinding] = []
        findings.extend(self._scan_privacy_headers(headers))
        findings.extend(self._scan_privacy_values(rows=rows, columns=columns))
        findings = self._deduplicate_privacy_findings(findings)

        risk_level = RiskLevel.green
        if any(finding.severity == RiskLevel.red for finding in findings):
            risk_level = RiskLevel.red
        elif any(finding.severity == RiskLevel.orange for finding in findings):
            risk_level = RiskLevel.orange

        if risk_level == RiskLevel.red:
            status = "needs_deidentification"
            summary = "检测到疑似直接身份标识。请先在本地完成脱敏，再继续用于统计或写作。"
        elif risk_level == RiskLevel.orange:
            status = "needs_review"
            summary = "未发现明确直接标识，但存在编码、日期或自由文本等需要复核的隐私风险。"
        else:
            status = "ready_for_analysis"
            summary = "未发现常见直接身份标识；系统未保存原始 CSV。"

        return DataPrivacyReport(
            status=status,
            risk_level=risk_level,
            scanned_row_count=len(rows),
            scanned_column_count=len(headers),
            findings=findings,
            raw_data_saved=False,
            summary=summary,
        )

    def _scan_privacy_headers(self, headers: list[str]) -> list[DataPrivacyFinding]:
        findings: list[DataPrivacyFinding] = []
        for header in headers:
            normalized_header = self._normalize(header)
            lower_header = header.lower()
            for category, severity, patterns, recommendation in PHI_HEADER_RULES:
                if any(
                    self._privacy_pattern_matches_header(
                        pattern=pattern,
                        normalized_header=normalized_header,
                        lower_header=lower_header,
                    )
                    for pattern in patterns
                ):
                    findings.append(
                        DataPrivacyFinding(
                            severity=severity,
                            category=category,
                            column=header,
                            evidence=f"列名匹配 {category} 规则。",
                            recommendation=recommendation,
                        )
                    )
                    break
        return findings

    def _privacy_pattern_matches_header(
        self,
        pattern: str,
        normalized_header: str,
        lower_header: str,
    ) -> bool:
        normalized_pattern = self._normalize(pattern)
        if normalized_pattern in {"name", "姓名"}:
            return normalized_header == normalized_pattern
        if len(normalized_pattern) <= 3:
            return normalized_header == normalized_pattern or lower_header == pattern
        return normalized_pattern in normalized_header or pattern in lower_header

    def _scan_privacy_values(
        self,
        rows: list[dict[str, str]],
        columns: list[DataColumnQuality],
    ) -> list[DataPrivacyFinding]:
        findings: list[DataPrivacyFinding] = []
        scanned_rows = rows[:50]
        for column in columns:
            values = [
                str(row.get(column.name, "") or "").strip()
                for row in scanned_rows
                if not self._is_missing(str(row.get(column.name, "") or "").strip())
            ]
            if not values:
                continue

            email_count = sum(1 for value in values if EMAIL_PATTERN.match(value))
            if email_count:
                findings.append(
                    DataPrivacyFinding(
                        severity=RiskLevel.red,
                        category="direct_identifier",
                        column=column.name,
                        evidence=f"前 {len(scanned_rows)} 行中检测到 {email_count} 个疑似邮箱格式值。",
                        recommendation="移除邮箱等联系方式，或替换为不可逆研究编码。",
                    )
                )

            phone_count = sum(1 for value in values if PHONE_PATTERN.match(value))
            if phone_count:
                findings.append(
                    DataPrivacyFinding(
                        severity=RiskLevel.red,
                        category="direct_identifier",
                        column=column.name,
                        evidence=f"前 {len(scanned_rows)} 行中检测到 {phone_count} 个疑似电话号码格式值。",
                        recommendation="移除电话号码等联系方式，或替换为不可逆研究编码。",
                    )
                )

            id_count = sum(1 for value in values if CHINESE_ID_PATTERN.match(value))
            if id_count:
                findings.append(
                    DataPrivacyFinding(
                        severity=RiskLevel.red,
                        category="direct_identifier",
                        column=column.name,
                        evidence=f"前 {len(scanned_rows)} 行中检测到 {id_count} 个疑似身份证号格式值。",
                        recommendation="移除证件号等直接身份标识，禁止进入论文分析工作区。",
                    )
                )

            if (
                column.inferred_type == "text"
                and column.unique_count >= max(10, int(len(rows) * 0.8))
                and column.missing_percent < 20
            ):
                findings.append(
                    DataPrivacyFinding(
                        severity=RiskLevel.orange,
                        category="high_cardinality_text",
                        column=column.name,
                        evidence="该文本列接近一行一个唯一值，可能是病历号、检查号或自由文本。",
                        recommendation="确认该列不是可回溯身份标识；如非分析必需，建议移除。",
                    )
                )

        return findings

    def _deduplicate_privacy_findings(
        self,
        findings: list[DataPrivacyFinding],
    ) -> list[DataPrivacyFinding]:
        deduplicated: list[DataPrivacyFinding] = []
        seen: set[tuple[str | None, str, RiskLevel]] = set()
        for finding in findings:
            key = (finding.column, finding.category, finding.severity)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(finding)
        return deduplicated

    def _privacy_findings_to_issues(
        self,
        findings: list[DataPrivacyFinding],
    ) -> list[DataQualityIssue]:
        return [
            DataQualityIssue(
                severity=finding.severity,
                column=finding.column,
                message=f"脱敏风险：{finding.evidence}",
                suggested_action=finding.recommendation,
            )
            for finding in findings
            if finding.severity in {RiskLevel.red, RiskLevel.orange}
        ]

    def _build_issues(
        self,
        row_count: int,
        columns: list[DataColumnQuality],
        missing_required_fields: list[str],
    ) -> list[DataQualityIssue]:
        issues: list[DataQualityIssue] = []
        if row_count == 0:
            issues.append(
                DataQualityIssue(
                    severity=RiskLevel.red,
                    message="CSV 文件没有数据行。",
                    suggested_action="保留表头并至少上传一行脱敏病例数据后再做质控。",
                )
            )

        for field in missing_required_fields:
            issues.append(
                DataQualityIssue(
                    severity=RiskLevel.orange,
                    column=None,
                    message=f"缺少研究方案要求字段：{field}",
                    suggested_action="确认字段命名、补充导出列，或在研究方案中调整数据需求。",
                )
            )

        for column in columns:
            if column.missing_percent >= 50:
                issues.append(
                    DataQualityIssue(
                        severity=RiskLevel.red,
                        column=column.name,
                        message=f"{column.name} 缺失率为 {column.missing_percent}%。",
                        suggested_action="回查原始导出流程，确认该列是否可用于主要分析。",
                    )
                )
            elif column.missing_percent >= 20:
                issues.append(
                    DataQualityIssue(
                        severity=RiskLevel.orange,
                        column=column.name,
                        message=f"{column.name} 缺失率为 {column.missing_percent}%。",
                        suggested_action="记录缺失原因，并考虑敏感性分析或排除规则。",
                    )
                )

            if row_count > 1 and column.unique_count <= 1 and column.missing_percent < 100:
                issues.append(
                    DataQualityIssue(
                        severity=RiskLevel.orange,
                        column=column.name,
                        message=f"{column.name} 只有 {column.unique_count} 个非空唯一值。",
                        suggested_action="确认该列是否为固定批次信息，避免误作为统计变量。",
                    )
                )

        return issues

    def _match_requirements(
        self,
        items: list[DataRequirementItem],
        headers: list[str],
    ) -> tuple[list[str], list[str]]:
        normalized_headers = {header: self._normalize(header) for header in headers}
        matched: list[str] = []
        missing: list[str] = []

        for item in items:
            if not item.required:
                continue

            candidates = self._candidate_keys(item.label)
            has_match = any(
                self._candidate_matches_header(candidate, header_key)
                for candidate in candidates
                for header_key in normalized_headers.values()
            )
            if has_match:
                matched.append(item.label)
            else:
                missing.append(item.label)

        return matched, missing

    def _candidate_keys(self, label: str) -> list[str]:
        candidates = [label, *FIELD_SYNONYMS.get(label, [])]
        return [self._normalize(candidate) for candidate in candidates if self._normalize(candidate)]

    def _candidate_matches_header(self, candidate: str, header_key: str) -> bool:
        if len(candidate) <= 2:
            return candidate == header_key
        return candidate == header_key or candidate in header_key or header_key in candidate

    def _normalize(self, value: str) -> str:
        return "".join(character.lower() for character in value if character.isalnum())

    def _is_missing(self, value: str) -> bool:
        return value.strip().lower() in MISSING_TOKENS

    def _build_writer_summary(
        self,
        project: Project,
        row_count: int,
        column_count: int,
        issue_count: int,
        missing_required_fields: list[str],
    ) -> str:
        missing_text = ", ".join(missing_required_fields[:5]) if missing_required_fields else "none"
        return (
            f"The uploaded dataset for {project.name} contains {row_count} rows and "
            f"{column_count} columns. The current quality-control review identified "
            f"{issue_count} issue(s), and the missing key field(s) are: {missing_text}. "
            "Before drafting the Results section, complete field reconciliation, document "
            "the reasons for missingness, and confirm the primary outcome column."
        )

    def _build_methods_draft(
        self,
        protocol: ProjectProtocol,
        selected_outcomes: list[str],
        group_column: str | None,
    ) -> str:
        outcome_text = ", ".join(selected_outcomes)
        group_text = (
            f"Descriptive summaries were stratified by {group_column}. "
            if group_column
            else "No grouping variable was specified. "
        )
        planned_tests = (
            self._english_manuscript_text(
                protocol.statistical_plan.strip(),
                "Descriptive statistics, between-group differences, and effect sizes will be prioritized; predictive analyses require cross-validation, calibration assessment, and external review.",
            )
            or "Formal statistical tests will be selected according to variable distribution and study design."
        )
        return (
            f"Descriptive statistics were generated for the numeric outcome variable(s) "
            f"({outcome_text}), including sample size, mean, standard deviation, median, "
            f"minimum, and maximum. {group_text}"
            f"At this stage, the workflow generates an exploratory statistical draft only "
            f"and does not report P values. Planned formal statistical approach: {planned_tests}"
        )

    def _english_manuscript_text(self, value: str, fallback: str) -> str:
        if not value.strip():
            return fallback
        if re.search(r"[\u3400-\u9fff]", value):
            return fallback
        return value

    def _build_results_draft(
        self,
        project: Project,
        row_count: int,
        numeric_summaries: list[DescriptiveStatistic],
        group_comparisons: list[GroupComparisonDraft],
    ) -> str:
        first_summary = numeric_summaries[0]
        group_sentence = (
            f" Grouped descriptive interpretation: {group_comparisons[0].interpretation}"
            if group_comparisons
            else ""
        )
        return (
            f"The current CSV for {project.name} included {row_count} records. "
            f"For {first_summary.column}, the available sample size was {first_summary.n}, "
            f"with mean {first_summary.mean}, standard deviation {first_summary.std_dev}, "
            f"median {first_summary.median}, and range {first_summary.min} to {first_summary.max}."
            f"{group_sentence}"
        )


data_workspace_service = DataWorkspaceService()
