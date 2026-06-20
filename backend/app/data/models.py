from datetime import datetime

from pydantic import BaseModel, Field

from app.projects.models import RiskLevel


class DataRequirementItem(BaseModel):
    id: str
    label: str
    category: str
    required: bool = True
    source: str
    rationale: str = ""


class DataRequirementSpec(BaseModel):
    project_id: str
    generated_from_protocol: bool
    protocol_data_requirements: str = ""
    items: list[DataRequirementItem] = Field(default_factory=list)
    next_step: str


class NumericSummary(BaseModel):
    min: float
    max: float
    mean: float


class DataColumnQuality(BaseModel):
    name: str
    inferred_type: str
    missing_count: int
    missing_percent: float
    unique_count: int
    sample_values: list[str] = Field(default_factory=list)
    numeric_summary: NumericSummary | None = None


class DataQualityIssue(BaseModel):
    severity: RiskLevel
    column: str | None = None
    message: str
    suggested_action: str


class DataPrivacyFinding(BaseModel):
    severity: RiskLevel
    category: str
    column: str | None = None
    evidence: str
    recommendation: str


class DataPrivacyReport(BaseModel):
    status: str
    risk_level: RiskLevel
    scanned_row_count: int
    scanned_column_count: int
    findings: list[DataPrivacyFinding] = Field(default_factory=list)
    raw_data_saved: bool = False
    policy_version: str = "privacy-v1"
    summary: str


class DataQualityReport(BaseModel):
    project_id: str
    file_name: str
    row_count: int
    column_count: int
    requirement_items: list[DataRequirementItem]
    matched_required_fields: list[str]
    missing_required_fields: list[str]
    columns: list[DataColumnQuality]
    issues: list[DataQualityIssue]
    privacy_report: DataPrivacyReport | None = None
    summary_for_writer: str


class DescriptiveStatistic(BaseModel):
    column: str
    n: int
    missing_count: int
    mean: float
    std_dev: float
    median: float
    min: float
    max: float


class CategoricalLevel(BaseModel):
    value: str
    count: int
    percent: float


class CategoricalSummary(BaseModel):
    column: str
    levels: list[CategoricalLevel]
    omitted_level_count: int = 0


class GroupStatistic(BaseModel):
    group_value: str
    n: int
    mean: float
    std_dev: float
    median: float
    min: float
    max: float


class GroupComparisonDraft(BaseModel):
    column: str
    group_column: str
    groups: list[GroupStatistic]
    interpretation: str


class DistributionCheck(BaseModel):
    column: str
    n: int
    missing_count: int
    skewness_hint: float | None = None
    normality_signal: str
    recommendation: str


class StatisticalTestRecommendation(BaseModel):
    outcome_column: str
    group_column: str | None = None
    candidate_tests: list[str] = Field(default_factory=list)
    p_value_boundary: str
    effect_size_note: str
    caveats: list[str] = Field(default_factory=list)


class FormalTestConfirmation(BaseModel):
    confirmed_by: str = ""
    design_confirmed: bool = False
    endpoints_confirmed: bool = False
    deidentified_confirmed: bool = False
    missing_data_reviewed: bool = False
    assumptions_reviewed: bool = False
    multiplicity_reviewed: bool = False
    notes: str = ""


class PairwiseComparisonResult(BaseModel):
    group_a: str
    group_b: str
    test_name: str
    status: str
    statistic: float | None = None
    degrees_of_freedom: float | None = None
    p_value: float | None = None
    adjusted_p_value: float | None = None
    correction_method: str = "Holm-Bonferroni"
    effect_size: float | None = None
    interpretation: str
    warnings: list[str] = Field(default_factory=list)


class FormalTestResult(BaseModel):
    outcome_column: str
    group_column: str | None = None
    test_name: str
    status: str
    statistic: float | None = None
    degrees_of_freedom: float | None = None
    denominator_degrees_of_freedom: float | None = None
    p_value: float | None = None
    effect_size: float | None = None
    group_count: int
    group_labels: list[str] = Field(default_factory=list)
    interpretation: str
    warnings: list[str] = Field(default_factory=list)
    pairwise_results: list[PairwiseComparisonResult] = Field(default_factory=list)


class FormalTestReport(BaseModel):
    project_id: str
    file_name: str
    row_count: int
    group_column: str | None = None
    outcome_columns: list[str] = Field(default_factory=list)
    confirmation: FormalTestConfirmation
    results: list[FormalTestResult]
    method_version: str = "formal-tests-v11"
    raw_csv_saved: bool = False
    audit_summary: str
    next_step: str


class ChartDataPoint(BaseModel):
    label: str
    value: float
    note: str = ""


class ChartSpec(BaseModel):
    id: str
    title: str
    chart_type: str
    x_label: str
    y_label: str
    points: list[ChartDataPoint]
    narrative: str


class DataAnalysisParameters(BaseModel):
    source_file_name: str
    row_count: int
    group_column: str | None = None
    outcome_columns: list[str] = Field(default_factory=list)
    generated_chart_ids: list[str] = Field(default_factory=list)
    quality_rule_version: str = "quality-v1"
    statistics_method_version: str = "descriptive-v1"
    chart_spec_version: str = "svg-bar-v1"
    raw_csv_saved: bool = False


class ReproducibleAnalysisScript(BaseModel):
    language: str = "python"
    file_name: str
    script: str
    input_file_placeholder: str
    instructions: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


class DataStatisticsReport(BaseModel):
    project_id: str
    file_name: str
    row_count: int
    numeric_summaries: list[DescriptiveStatistic]
    categorical_summaries: list[CategoricalSummary]
    group_column: str | None = None
    group_comparisons: list[GroupComparisonDraft]
    distribution_checks: list[DistributionCheck] = Field(default_factory=list)
    test_recommendations: list[StatisticalTestRecommendation] = Field(default_factory=list)
    chart_specs: list[ChartSpec] = Field(default_factory=list)
    formal_test_report: FormalTestReport | None = None
    analysis_parameters: DataAnalysisParameters | None = None
    reproducible_script: ReproducibleAnalysisScript | None = None
    methods_draft: str
    results_draft: str
    next_step: str


class AdvancedModelCandidate(BaseModel):
    model_id: str
    model_name: str
    readiness: str
    outcome_column: str | None = None
    required_fields: list[str] = Field(default_factory=list)
    available_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    cautions: list[str] = Field(default_factory=list)
    methods_template: str
    results_template: str


class AdvancedModelPlan(BaseModel):
    project_id: str
    file_name: str
    row_count: int
    generated_from_protocol: bool
    recommended_model_id: str | None = None
    candidates: list[AdvancedModelCandidate] = Field(default_factory=list)
    next_step: str


class DataAnalysisRecordCreate(BaseModel):
    file_name: str
    quality_report: DataQualityReport
    statistics_report: DataStatisticsReport | None = None


class DataAnalysisRecord(BaseModel):
    id: int
    project_id: str
    file_name: str
    row_count: int
    column_count: int
    issue_count: int
    chart_count: int
    quality_report: DataQualityReport
    statistics_report: DataStatisticsReport | None = None
    created_at: datetime


class DataAuditLog(BaseModel):
    id: int
    project_id: str
    action: str
    file_name: str | None = None
    row_count: int = 0
    column_count: int = 0
    risk_level: RiskLevel
    summary: str
    raw_data_saved: bool = False
    created_at: datetime
