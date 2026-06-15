import type {
  AgentProfile,
  ChatRequest,
  ChatResponse,
  DashboardSummary,
  ItemStatus,
  Project,
  ProjectPlanDraft,
  ProjectProtocol,
  ProjectProtocolUpdate,
  ProjectReminderSummary,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDashboard(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/api/dashboard/");
}

export function getProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects/");
}

export function getProjectProtocol(projectId: string): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol`);
}

export function saveProjectProtocol(
  projectId: string,
  requestBody: ProjectProtocolUpdate,
): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol`, {
    method: "PUT",
    body: JSON.stringify(requestBody),
  });
}

export function draftProjectProtocol(projectId: string): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol/draft`, {
    method: "POST",
  });
}

export function extractProjectProtocol(
  projectId: string,
  sourceText: string,
): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol/extract`, {
    method: "POST",
    body: JSON.stringify({ source_text: sourceText }),
  });
}

export function getProjectPlanDrafts(projectId: string): Promise<ProjectPlanDraft[]> {
  return request<ProjectPlanDraft[]>(`/api/projects/${projectId}/plan/drafts`);
}

export function generateProjectPlanDraftFromProtocol(projectId: string): Promise<ProjectPlanDraft> {
  return request<ProjectPlanDraft>(`/api/projects/${projectId}/plan/drafts/from-protocol`, {
    method: "POST",
  });
}

export function applyProjectPlanDraft(projectId: string, draftId: number): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}/plan/drafts/${draftId}/apply`, {
    method: "POST",
  });
}

export function getProjectReminders(projectId: string): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(`/api/projects/${projectId}/reminders`);
}

export function refreshProjectReminders(projectId: string): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(`/api/projects/${projectId}/reminders/refresh`, {
    method: "POST",
  });
}

export function dismissProjectReminder(
  projectId: string,
  reminderId: number,
): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(
    `/api/projects/${projectId}/reminders/${reminderId}/dismiss`,
    {
      method: "PATCH",
    },
  );
}

export function getAgents(): Promise<AgentProfile[]> {
  return request<AgentProfile[]>("/api/agents/");
}

export function sendChat(requestBody: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat/", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function updateTaskStatus(
  projectId: string,
  taskId: string,
  status: ItemStatus,
): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
