export type RiskLevel = "green" | "orange" | "red";

export type UserRole = "admin" | "researcher" | "reviewer";

export type ProjectAccessLevel = "viewer" | "editor" | "owner";

export type ItemStatus = "not_started" | "in_progress" | "blocked" | "done";

export type ReminderStatus = "pending" | "sent" | "dismissed";

export type ReminderType = "due_48h" | "due_24h" | "overdue" | "blocked";

export type AgentId =
  | "mentor"
  | "project_manager"
  | "study_planner"
  | "data_analyst"
  | "writer"
  | "reviewer";

export interface AgentProfile {
  id: AgentId;
  name: string;
  role_name: string;
  tagline: string;
  responsibilities: string[];
  tools: string[];
  system_prompt: string;
  is_consultant: boolean;
}

export interface MentorTrendPoint {
  year: number;
  publication_count: number;
}

export interface MentorTrendItem {
  topic_id: string;
  title: string;
  heat_label: string;
  summary: string;
  recent_counts: MentorTrendPoint[];
  forecast_note: string;
}

export interface MentorTrendSnapshot {
  generated_at: string;
  trends: MentorTrendItem[];
  recommended_focus: string;
}

export interface MentorRecommendationCard {
  title: string;
  research_question: string;
  why_fit: string;
  data_pathway: string;
  methods_route: string;
  statistical_plan: string;
  innovation_point: string;
  feasibility_note: string;
  risk_flags: string[];
  minimum_data_fields: string[];
  readiness_checklist: string[];
  protocol_trace: string[];
  first_milestones: string[];
  evidence_items: MentorEvidenceItem[];
  target_journals: string[];
}

export interface MentorEvidenceItem {
  source_type: string;
  evidence_status: string;
  retrieved_at?: string | null;
  external_url?: string | null;
  crossref_url?: string | null;
  pmid?: string | null;
  title?: string | null;
  journal?: string | null;
  publication_year?: string | null;
  doi?: string | null;
  citation_text?: string | null;
  vancouver_citation?: string | null;
  authors: string[];
  volume?: string | null;
  issue?: string | null;
  page?: string | null;
  publication_types: string[];
  review_status: string;
  review_note?: string;
  reviewer?: string;
  full_text_checked?: boolean;
  use_in_introduction?: boolean;
  use_in_discussion?: boolean;
  search_query: string;
  evidence_summary: string;
  recommendation_signal: string;
  limitation: string;
}

export interface MentorRecommendationResponse {
  profile_summary: string;
  resource_diagnosis: string[];
  selection_rationale: string[];
  matched_strengths: string[];
  recommendations: MentorRecommendationCard[];
  next_steps: string[];
}

export interface JournalGuidelineFetchResponse {
  source_url: string;
  title?: string | null;
  text: string;
  character_count: number;
  truncated: boolean;
}

export interface MentorEvidenceReview {
  id: number;
  project_id: string;
  evidence_key: string;
  card_title: string;
  evidence_index: number;
  pmid?: string | null;
  doi?: string | null;
  title?: string | null;
  search_query: string;
  review_status: string;
  review_note: string;
  reviewer: string;
  full_text_checked: boolean;
  use_in_introduction: boolean;
  use_in_discussion: boolean;
  updated_at: string;
}

export interface MentorEvidenceReviewUpdate {
  evidence_key: string;
  card_title: string;
  evidence_index: number;
  pmid?: string | null;
  doi?: string | null;
  title?: string | null;
  search_query: string;
  review_status: string;
  review_note: string;
  reviewer: string;
  full_text_checked: boolean;
  use_in_introduction: boolean;
  use_in_discussion: boolean;
}

export interface UserProfile {
  id: string;
  display_name: string;
  email: string;
  role: UserRole;
}

export interface ProjectAccessPolicy {
  project_id: string;
  user_id: string;
  access_level: ProjectAccessLevel;
  can_view: boolean;
  can_edit: boolean;
  can_manage_data: boolean;
  can_manage_access: boolean;
}

export interface Phase {
  id: string;
  title: string;
  status: ItemStatus;
  start_date: string;
  end_date: string;
  deliverables: string[];
}

export interface Task {
  id: string;
  title: string;
  due_date: string;
  status: ItemStatus;
  owner_agent_id: string;
  deliverable: string;
}

export interface Project {
  id: string;
  name: string;
  title: string;
  topic: string;
  current_phase: string;
  progress_percent: number;
  risk_level: RiskLevel;
  stage_days_remaining: number;
  next_milestone: string;
  next_due_date: string;
  phases: Phase[];
  tasks: Task[];
}

export interface ProjectProtocol {
  project_id: string;
  research_question: string;
  hypothesis: string;
  study_type: string;
  primary_endpoint: string;
  secondary_endpoints: string;
  inclusion_criteria: string;
  exclusion_criteria: string;
  data_requirements: string;
  institutional_field_mapping: string;
  experiment_workflow: string;
  statistical_plan: string;
  target_journals: string;
  rhea_milestones: string;
}

export type ProjectProtocolUpdate = Omit<ProjectProtocol, "project_id">;

export interface ProjectPlanDraft {
  id: number;
  project_id: string;
  version_label: string;
  phases: Phase[];
  tasks: Task[];
  created_at: string;
  applied_at?: string | null;
}

export interface WriterIntroductionDraft {
  project_id: string;
  background_paragraph: string;
  gap_paragraph: string;
  objective_paragraph: string;
  citation_bindings: Record<string, string[]>;
  updated_at?: string | null;
}

export type WriterIntroductionDraftUpdate = Omit<
  WriterIntroductionDraft,
  "project_id" | "updated_at"
>;

export interface WriterDraftVersionCreate {
  title: string;
  introduction: WriterIntroductionDraftUpdate;
  derived_sections: Record<string, string>;
  metadata: Record<string, string | number | boolean | null>;
}

export interface WriterDraftVersion {
  id: number;
  project_id: string;
  version_label: string;
  title: string;
  introduction: WriterIntroductionDraftUpdate;
  derived_sections: Record<string, string>;
  metadata: Record<string, string | number | boolean | null>;
  created_at: string;
  restored_at?: string | null;
}

export type ReviewerCommentType = "major" | "minor" | "editorial";

export type ReviewerCommentStatus = "draft" | "addressing" | "resolved" | "deferred";

export type ReviewerRevisionSection =
  | "Introduction"
  | "Methods / Results"
  | "Discussion"
  | "Abstract"
  | "Cover Letter / Submission";

export interface ReviewerCommentThread {
  id: number;
  project_id: string;
  reviewer_label: string;
  comment_type: ReviewerCommentType;
  status: ReviewerCommentStatus;
  comment_text: string;
  response_draft: string;
  manuscript_change: string;
  manual_revision_sections: ReviewerRevisionSection[];
  created_at: string;
  updated_at: string;
}

export type ReviewerCommentThreadUpdate = Omit<
  ReviewerCommentThread,
  "id" | "project_id" | "created_at" | "updated_at"
>;

export interface TaskReminder {
  id: number;
  project_id: string;
  task_id: string;
  task_title: string;
  reminder_type: ReminderType;
  severity: RiskLevel;
  status: ReminderStatus;
  trigger_date: string;
  due_date: string;
  message: string;
  suggested_action: string;
  created_at: string;
  updated_at: string;
  dismissed_at?: string | null;
}

export interface ProjectReminderSummary {
  project_id: string;
  generated_at: string;
  risk_level: RiskLevel;
  active_count: number;
  overdue_count: number;
  blocked_count: number;
  next_due_count: number;
  manager_note: string;
  reminders: TaskReminder[];
}

export interface DataRequirementItem {
  id: string;
  label: string;
  category: string;
  required: boolean;
  source: string;
  rationale: string;
}

export interface DataRequirementSpec {
  project_id: string;
  generated_from_protocol: boolean;
  protocol_data_requirements: string;
  items: DataRequirementItem[];
  next_step: string;
}

export interface NumericSummary {
  min: number;
  max: number;
  mean: number;
}

export interface DataColumnQuality {
  name: string;
  inferred_type: string;
  missing_count: number;
  missing_percent: number;
  unique_count: number;
  sample_values: string[];
  numeric_summary?: NumericSummary | null;
}

export interface DataQualityIssue {
  severity: RiskLevel;
  column?: string | null;
  message: string;
  suggested_action: string;
}

export interface DataPrivacyFinding {
  severity: RiskLevel;
  category: string;
  column?: string | null;
  evidence: string;
  recommendation: string;
}

export interface DataPrivacyReport {
  status: string;
  risk_level: RiskLevel;
  scanned_row_count: number;
  scanned_column_count: number;
  findings: DataPrivacyFinding[];
  raw_data_saved: boolean;
  policy_version: string;
  summary: string;
}

export interface DataQualityReport {
  project_id: string;
  file_name: string;
  row_count: number;
  column_count: number;
  requirement_items: DataRequirementItem[];
  matched_required_fields: string[];
  missing_required_fields: string[];
  columns: DataColumnQuality[];
  issues: DataQualityIssue[];
  privacy_report?: DataPrivacyReport | null;
  summary_for_writer: string;
}

export interface DescriptiveStatistic {
  column: string;
  n: number;
  missing_count: number;
  mean: number;
  std_dev: number;
  median: number;
  min: number;
  max: number;
}

export interface CategoricalLevel {
  value: string;
  count: number;
  percent: number;
}

export interface CategoricalSummary {
  column: string;
  levels: CategoricalLevel[];
  omitted_level_count: number;
}

export interface GroupStatistic {
  group_value: string;
  n: number;
  mean: number;
  std_dev: number;
  median: number;
  min: number;
  max: number;
}

export interface GroupComparisonDraft {
  column: string;
  group_column: string;
  groups: GroupStatistic[];
  interpretation: string;
}

export interface DistributionCheck {
  column: string;
  n: number;
  missing_count: number;
  skewness_hint?: number | null;
  normality_signal: string;
  recommendation: string;
}

export interface StatisticalTestRecommendation {
  outcome_column: string;
  group_column?: string | null;
  candidate_tests: string[];
  p_value_boundary: string;
  effect_size_note: string;
  caveats: string[];
}

export interface FormalTestConfirmation {
  confirmed_by: string;
  design_confirmed: boolean;
  endpoints_confirmed: boolean;
  deidentified_confirmed: boolean;
  missing_data_reviewed: boolean;
  assumptions_reviewed: boolean;
  multiplicity_reviewed: boolean;
  notes: string;
}

export interface PairwiseComparisonResult {
  group_a: string;
  group_b: string;
  test_name: string;
  status: string;
  statistic?: number | null;
  degrees_of_freedom?: number | null;
  p_value?: number | null;
  adjusted_p_value?: number | null;
  correction_method: string;
  effect_size?: number | null;
  interpretation: string;
  warnings: string[];
}

export interface FormalTestResult {
  outcome_column: string;
  group_column?: string | null;
  test_name: string;
  status: string;
  statistic?: number | null;
  degrees_of_freedom?: number | null;
  denominator_degrees_of_freedom?: number | null;
  p_value?: number | null;
  effect_size?: number | null;
  group_count: number;
  group_labels: string[];
  interpretation: string;
  warnings: string[];
  pairwise_results?: PairwiseComparisonResult[];
}

export interface FormalTestReport {
  project_id: string;
  file_name: string;
  row_count: number;
  group_column?: string | null;
  outcome_columns: string[];
  confirmation: FormalTestConfirmation;
  results: FormalTestResult[];
  method_version: string;
  raw_csv_saved: boolean;
  audit_summary: string;
  next_step: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  note: string;
}

export interface ChartSpec {
  id: string;
  title: string;
  chart_type: string;
  x_label: string;
  y_label: string;
  points: ChartDataPoint[];
  narrative: string;
}

export interface DataAnalysisParameters {
  source_file_name: string;
  row_count: number;
  group_column?: string | null;
  outcome_columns: string[];
  generated_chart_ids: string[];
  quality_rule_version: string;
  statistics_method_version: string;
  chart_spec_version: string;
  raw_csv_saved: boolean;
}

export interface ReproducibleAnalysisScript {
  language: string;
  file_name: string;
  script: string;
  input_file_placeholder: string;
  instructions: string[];
  safety_notes: string[];
}

export interface DataStatisticsReport {
  project_id: string;
  file_name: string;
  row_count: number;
  numeric_summaries: DescriptiveStatistic[];
  categorical_summaries: CategoricalSummary[];
  group_column?: string | null;
  group_comparisons: GroupComparisonDraft[];
  distribution_checks: DistributionCheck[];
  test_recommendations: StatisticalTestRecommendation[];
  chart_specs: ChartSpec[];
  formal_test_report?: FormalTestReport | null;
  analysis_parameters?: DataAnalysisParameters | null;
  reproducible_script?: ReproducibleAnalysisScript | null;
  methods_draft: string;
  results_draft: string;
  next_step: string;
}

export interface AdvancedModelCandidate {
  model_id: string;
  model_name: string;
  readiness: string;
  outcome_column?: string | null;
  required_fields: string[];
  available_fields: string[];
  missing_fields: string[];
  assumptions: string[];
  cautions: string[];
  methods_template: string;
  results_template: string;
}

export interface AdvancedModelPlan {
  project_id: string;
  file_name: string;
  row_count: number;
  generated_from_protocol: boolean;
  recommended_model_id?: string | null;
  candidates: AdvancedModelCandidate[];
  next_step: string;
}

export interface AdvancedModelCoefficient {
  term: string;
  estimate: number;
  standard_error?: number | null;
  statistic?: number | null;
  p_value?: number | null;
  confidence_interval_low?: number | null;
  confidence_interval_high?: number | null;
  interpretation: string;
}

export interface AdvancedModelDiagnosticHandoff {
  model_family: string;
  review_status: string;
  sample_context: string[];
  required_diagnostics: string[];
  handoff_artifacts: string[];
  manuscript_boundary: string;
  reviewer_focus: string;
}

export interface AdvancedModelFitReport {
  project_id: string;
  file_name: string;
  model_id: string;
  model_name: string;
  outcome_column: string;
  predictor_columns: string[];
  row_count: number;
  complete_case_count: number;
  excluded_row_count: number;
  degrees_of_freedom: number;
  r_squared?: number | null;
  adjusted_r_squared?: number | null;
  coefficients: AdvancedModelCoefficient[];
  methods_draft: string;
  results_draft: string;
  warnings: string[];
  diagnostic_handoff?: AdvancedModelDiagnosticHandoff | null;
  confirmation: FormalTestConfirmation;
  method_version: string;
  raw_csv_saved: boolean;
  audit_summary: string;
  next_step: string;
}

export interface DataAnalysisRecordCreate {
  file_name: string;
  quality_report: DataQualityReport;
  statistics_report?: DataStatisticsReport | null;
}

export interface DataAnalysisRecord {
  id: number;
  project_id: string;
  file_name: string;
  row_count: number;
  column_count: number;
  issue_count: number;
  chart_count: number;
  quality_report: DataQualityReport;
  statistics_report?: DataStatisticsReport | null;
  created_at: string;
}

export interface DataAuditLog {
  id: number;
  project_id: string;
  action: string;
  file_name?: string | null;
  row_count: number;
  column_count: number;
  risk_level: RiskLevel;
  summary: string;
  raw_data_saved: boolean;
  created_at: string;
}

export interface MilestoneSummary {
  project_id: string;
  project_name: string;
  milestone: string;
  due_date: string;
  risk_level: RiskLevel;
}

export interface DashboardSummary {
  overall_completion_percent: number;
  active_project_count: number;
  risk_level: RiskLevel;
  next_milestones: MilestoneSummary[];
  encouragement: string;
  manager_name: string;
  manager_role: string;
  manager_message: string;
}

export interface ChatRequest {
  agent_id: AgentId;
  message: string;
  project_id?: string | null;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  agent_id: AgentId;
  agent_name: string;
  project_id: string | null;
  reply: string;
  suggested_next_actions: string[];
  response_source: string;
  fallback_reason?: string | null;
}

export interface ChatHistoryMessage {
  id: number;
  project_id: string | null;
  agent_id: AgentId;
  speaker: "user" | "agent";
  content: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  speaker: "user" | "agent";
  agentId?: AgentId;
  projectId?: string | null;
  agentName?: string;
  content: string;
  suggestedNextActions?: string[];
}

export interface TaskStatusUpdate {
  status: ItemStatus;
}
