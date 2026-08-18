/** Shared API response shapes (mirror backend/schemas where useful). */

export type AIExecution = {
  request_id: string
  requested_provider: string
  provider_used: string
  status: string
  model: string
  fallback_reason: string | null
  estimated_cost_cents: number
  actual_cost_cents: number | null
}

export type AIStatus = {
  configured: boolean
  enabled: boolean
  provider: string
  model: string
  monthly_budget_cents: number
  monthly_reserved_or_spent_cents: number
  monthly_request_limit: number
  requests_this_month: number
  estimated_maximum_workflow_cents: number
  local_demo_available: boolean
}

export type ResumeListItem = {
  id: number
  filename: string
  created_at: string
}

export type Resume = ResumeListItem & { extracted_text: string }

export type ResumeFeedback = {
  id: number
  resume_id: number
  strengths: string[]
  weaknesses: string[]
  improvements: string[]
  overall_score: number
  summary: string
  created_at: string
  execution?: AIExecution | null
}

export type JobPosting = {
  id: number
  title: string
  company: string
  description: string
  created_at: string
}

export type JobMatch = {
  id: number
  resume_id: number
  job_id: number
  score: number
  matched_keywords: string[]
  gaps: string[]
  summary: string
  created_at: string
  execution?: AIExecution | null
}

export type CoverLetter = {
  id: number
  resume_id: number
  job_id: number
  content: string
  created_at: string
  execution?: AIExecution | null
}

export type SkillGap = {
  id: number
  resume_id: number
  job_id: number
  missing_skills: string[]
  suggested_resources: string[]
  priority_order: string[]
  created_at: string
  execution?: AIExecution | null
}

export type Application = {
  id: number
  company_name: string
  role_title: string
  status: string
  notes: string
  job_url: string
  resume_id: number | null
  job_posting_id: number | null
  created_at: string
  updated_at: string
}

export type Dashboard = {
  resume_count: number
  job_count: number
  application_count: number
  recent_feedbacks: Array<{
    id: number
    resume_id: number
    overall_score: number
    summary: string
    created_at: string
  }>
  recent_matches: Array<{
    id: number
    resume_id: number
    job_id: number
    score: number
    summary: string
    created_at: string
  }>
  applications_by_status: Record<string, number>
}
