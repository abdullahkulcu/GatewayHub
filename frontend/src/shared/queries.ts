import { useQuery } from '@tanstack/react-query'
import { api } from './api'
import type { ListOption, TaskDetail, TaskSummary, UserDirectoryEntry } from './types'

export interface TaskFilters {
  assignee?: string
  status?: string
  tag?: string
  listId?: string
  hasParent?: boolean
  sort?: string
}

function buildTaskQueryString(filters: TaskFilters): string {
  const params = new URLSearchParams()
  if (filters.assignee) params.set('assignee', filters.assignee)
  if (filters.status) params.set('status', filters.status)
  if (filters.tag) params.set('tag', filters.tag)
  if (filters.listId) params.set('list_id', filters.listId)
  if (filters.hasParent !== undefined) params.set('has_parent', String(filters.hasParent))
  if (filters.sort) params.set('sort', filters.sort)
  return params.toString()
}

export function useTasks(filters: TaskFilters) {
  const qs = buildTaskQueryString(filters)
  return useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => api.get<TaskSummary[]>(`/api/tasks${qs ? `?${qs}` : ''}`),
  })
}

export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: ['task', taskId],
    queryFn: () => api.get<TaskDetail>(`/api/tasks/${taskId}`),
    enabled: taskId !== undefined,
  })
}

export function useUsersDirectory() {
  return useQuery({
    queryKey: ['users-directory'],
    queryFn: () => api.get<UserDirectoryEntry[]>('/api/users/directory'),
  })
}

export function useListOptions() {
  return useQuery({
    queryKey: ['task-list-options'],
    queryFn: () => api.get<ListOption[]>('/api/tasks/list-options'),
  })
}
