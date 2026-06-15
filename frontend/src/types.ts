export type RiskLevel = "green" | "orange" | "red";

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
