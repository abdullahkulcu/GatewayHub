export type StatusCategory = 'todo' | 'in_progress' | 'done' | 'cancelled'
export type WriteState = 'synced' | 'pending' | 'failed'

export interface TaskSummary {
  id: string
  provider: string
  provider_task_id: string
  provider_list_id: string | null
  provider_list_name: string | null
  parent_id: string | null
  title: string
  description: string | null
  status: string
  status_category: StatusCategory | null
  assignees: string[] | null
  priority: string | null
  due_date: string | null
  tags: string[] | null
  write_state: WriteState
  provider_updated_at: string | null
  last_synced_at: string | null
  sync_version: number
}

export interface Comment {
  id: string
  author: string
  body: string
  created_at: string
}

export interface TaskDetail extends TaskSummary {
  comments: Comment[]
  subtasks: TaskSummary[]
}

export interface UserDirectoryEntry {
  id: string
  email: string
}

export interface ListOption {
  id: string
  name: string | null
}
