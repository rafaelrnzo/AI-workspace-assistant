import { create } from 'zustand'

export type TicketType = 'request' | 'issue' | 'question'
export type TicketComplexity = 'low' | 'medium' | 'hard'

export interface Ticket {
  id: string
  title: string
  description: string | null
  status: string
  repository_url: string | null
  repository_path: string | null
  branch: string | null
  agent_provider: string | null
  ticket_type: TicketType
  complexity: TicketComplexity
  requester_name: string | null
  review_status: string
  approved_by: string | null
  result: string | null
  execution_log: string | null
  diff: string | null
  queued_at: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface TicketMessage {
  id: string
  ticket_id: string
  role: 'user' | 'assistant' | 'system' | 'admin'
  content: string
  created_at: string
}

export interface ProjectOption {
  name: string
  path: string
}

export interface CreateTicketPayload {
  title: string
  description: string
  ticket_type: TicketType
  complexity: TicketComplexity
  requester_name: string
  repository_path?: string
  agent_provider?: string
}

interface TicketStore {
  tickets: Ticket[]
  messages: Record<string, TicketMessage[]>
  projects: ProjectOption[]
  loading: boolean
  selectedTicketId: string | null
  setSelectedTicket: (id: string | null) => void
  fetchProjects: () => Promise<void>
  fetchTickets: () => Promise<void>
  fetchMessages: (id: string) => Promise<void>
  createTicket: (payload: CreateTicketPayload) => Promise<Ticket>
  sendMessage: (id: string, content: string) => Promise<void>
  updateTicket: (id: string, data: Partial<Ticket>) => Promise<void>
  approveTicket: (id: string) => Promise<void>
  rejectTicket: (id: string) => Promise<void>
  retryTicket: (id: string) => Promise<void>
  deleteTicket: (id: string) => Promise<void>
}

const api = (path: string, init?: RequestInit) =>
  fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  }).then((r) => {
    if (!r.ok) throw new Error(`${r.status}`)
    return r.json()
  })

export const useTicketStore = create<TicketStore>((set) => ({
  tickets: [],
  messages: {},
  projects: [],
  loading: false,
  selectedTicketId: null,

  setSelectedTicket: (id) => set({ selectedTicketId: id }),

  fetchProjects: async () => {
    const projects = await api('/projects/')
    set({ projects })
  },

  fetchTickets: async () => {
    set({ loading: true })
    const tickets = await api('/tickets/')
    set({ tickets, loading: false })
  },

  fetchMessages: async (id) => {
    const messages = await api(`/tickets/${id}/messages`)
    set((state) => ({ messages: { ...state.messages, [id]: messages } }))
  },

  createTicket: async (payload) => {
    const ticket = await api('/tickets/', {
      method: 'POST',
      body: JSON.stringify({
        ...payload,
        description: payload.description || null,
        requester_name: payload.requester_name || null,
        auto_process: true,
      }),
    })
    const tickets = await api('/tickets/')
    set({ tickets, selectedTicketId: ticket.id })
    return ticket
  },

  sendMessage: async (id, content) => {
    await api(`/tickets/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, role: 'user' }),
    })
    const [tickets, messages] = await Promise.all([
      api('/tickets/'),
      api(`/tickets/${id}/messages`),
    ])
    set((state) => ({ tickets, messages: { ...state.messages, [id]: messages } }))
  },

  updateTicket: async (id, data) => {
    await api(`/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
    const tickets = await api('/tickets/')
    set({ tickets })
  },

  approveTicket: async (id) => {
    await api(`/tickets/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ actor: 'backend' }),
    })
    const tickets = await api('/tickets/')
    set({ tickets })
  },

  rejectTicket: async (id) => {
    await api(`/tickets/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ actor: 'backend' }),
    })
    const tickets = await api('/tickets/')
    set({ tickets })
  },

  retryTicket: async (id) => {
    await api(`/tickets/${id}/retry`, { method: 'POST' })
    const tickets = await api('/tickets/')
    set({ tickets })
  },

  deleteTicket: async (id) => {
    await api(`/tickets/${id}`, { method: 'DELETE' })
    const tickets = await api('/tickets/')
    set({ tickets })
  },
}))
