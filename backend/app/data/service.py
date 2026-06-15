from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from io import StringIO
from math import exp, lgamma, log, pi, sqrt
from statistics import fmean, median, stdev

from app.data.models import (
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
            generated_from_protocol=bool(protocol.data_requirements.strip()),
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
            next_step="确认分组变量和主要终点后，再进入正式统计检验、图表生成和结果段落写作。",
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
        normalized = re.sub(r"[；;\n]+", "、", value)
        parts = re.split(r"[、，,]", normalized)
        labels: list[str] = []
        for part in parts:
            label = re.sub(r"^(至少需要|需要|包括|以及|和)", "", part.strip())
            label = label.strip(" ：:。. ")
            if 2 <= len(label) <= 80 and label not in {"等", "指标", "数据"}:
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
            return f"{column_name} 在 {group_column} 下可用分组不足，暂不形成比较结论。"

        lowest = min(groups, key=lambda group: group.mean)
        highest = max(groups, key=lambda group: group.mean)
        mean_gap = round(highest.mean - lowest.mean, 4)
        return (
            f"{column_name} 按 {group_column} 分组后，均值最高组为 {highest.group_value}"
            f"（{highest.mean}），最低组为 {lowest.group_value}（{lowest.mean}），"
            f"均值差约 {mean_gap}。该结果只是描述性比较，尚未进行显著性检验。"
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
            return FormalTestResult(
                outcome_column=outcome_column,
                group_column=group_column,
                test_name="多组比较待复核",
                status="needs_external_review",
                group_count=len(grouped_values),
                group_labels=group_labels,
                interpretation=(
                    f"{outcome_column} 在 {group_column} 下有 {len(grouped_values)} 个分组。"
                    "当前原型不会自动执行 ANOVA 或 Kruskal-Wallis，请导出参数后在正式统计环境复核。"
                ),
                warnings=["多组比较需要明确方差齐性、事后比较和多重比较校正。"],
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
                title=f"{column_name} 分布",
                chart_type="histogram",
                x_label=column_name,
                y_label="病例数",
                points=[
                    ChartDataPoint(
                        label=str(round(min_value, 2)),
                        value=len(values),
                        note="所有非空数值相同",
                    )
                ],
                narrative=f"{column_name} 的非空记录均为 {round(min_value, 4)}。",
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
            title=f"{column_name} 分布",
            chart_type="histogram",
            x_label=column_name,
            y_label="病例数",
            points=points,
            narrative=f"{column_name} 的取值范围为 {round(min_value, 4)} 至 {round(max_value, 4)}。",
        )

    def _build_categorical_chart(self, summary: CategoricalSummary) -> ChartSpec:
        return ChartSpec(
            id=f"cat-{self._normalize(summary.column)}",
            title=f"{summary.column} 构成",
            chart_type="bar",
            x_label=summary.column,
            y_label="病例数",
            points=[
                ChartDataPoint(
                    label=level.value,
                    value=level.count,
                    note=f"{level.percent}%",
                )
                for level in summary.levels[:8]
            ],
            narrative=f"{summary.column} 共显示前 {min(len(summary.levels), 8)} 个分类水平。",
        )

    def _build_group_mean_chart(self, comparison: GroupComparisonDraft) -> ChartSpec | None:
        if not comparison.groups:
            return None

        return ChartSpec(
            id=f"group-{self._normalize(comparison.group_column)}-{self._normalize(comparison.column)}",
            title=f"{comparison.column} 分组均值",
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
        missing_text = "、".join(missing_required_fields[:5]) if missing_required_fields else "暂无"
        return (
            f"{project.name} 上传的数据表包含 {row_count} 行、{column_count} 列。"
            f"当前质控发现 {issue_count} 个需要处理的问题，缺少的关键字段为：{missing_text}。"
            "在进入结果段落写作前，建议先完成字段补齐、缺失原因记录和主要终点列确认。"
        )

    def _build_methods_draft(
        self,
        protocol: ProjectProtocol,
        selected_outcomes: list[str],
        group_column: str | None,
    ) -> str:
        outcome_text = "、".join(selected_outcomes)
        group_text = f"按 {group_column} 进行分组描述。" if group_column else "未指定分组变量。"
        planned_tests = protocol.statistical_plan.strip() or "后续根据变量分布和研究设计选择合适的统计检验。"
        return (
            f"对数值变量（{outcome_text}）进行描述性统计，报告样本量、均值、标准差、"
            f"中位数、最小值和最大值。{group_text}"
            f"本阶段仅生成探索性统计草案，不报告 P 值。正式统计计划：{planned_tests}"
        )

    def _build_results_draft(
        self,
        project: Project,
        row_count: int,
        numeric_summaries: list[DescriptiveStatistic],
        group_comparisons: list[GroupComparisonDraft],
    ) -> str:
        first_summary = numeric_summaries[0]
        group_sentence = (
            f" 分组描述提示：{group_comparisons[0].interpretation}"
            if group_comparisons
            else ""
        )
        return (
            f"{project.name} 当前 CSV 纳入 {row_count} 条记录。"
            f"{first_summary.column} 的可用样本量为 {first_summary.n}，"
            f"均值为 {first_summary.mean}，标准差为 {first_summary.std_dev}，"
            f"中位数为 {first_summary.median}，范围为 {first_summary.min} 至 {first_summary.max}。"
            f"{group_sentence}"
        )


data_workspace_service = DataWorkspaceService()
