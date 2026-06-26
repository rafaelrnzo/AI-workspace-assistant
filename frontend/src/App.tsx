import { type FormEvent, type ReactNode, useEffect, useMemo, useRef, useState } from 'react'
import {
  Bot,
  CheckCircle2,
  Circle,
  ClipboardList,
  FolderGit2,
  KanbanSquare,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Send,
  Settings,
  Sparkles,
  Table2,
  UserRound,
  XCircle,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import {
  type CreateTicketPayload,
  type Ticket,
  type TicketComplexity,
  type TicketMessage,
  type TicketType,
  useTicketStore,
} from '@/stores/ticket-store'

type SessionRole = 'user' | 'admin'
type Session = {
  role: SessionRole
  name: string
}

const SESSION_KEY = 'ai-assistant-session'
const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD ?? 'admin'

const STATUSES = ['review_required', 'queued', 'in_progress', 'completed', 'failed', 'pending']
const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  review_required: 'Review',
  queued: 'Queued',
  in_progress: 'Running',
  completed: 'Done',
  failed: 'Failed',
}
const PROVIDERS = [
  { value: '', label: 'Auto' },
  { value: 'codex_low', label: 'Codex low' },
  { value: 'codex_pro_3_1', label: 'Codex pro 3.1' },
  { value: 'antigravity_pro_3_1', label: 'Antigravity pro 3.1' },
  { value: 'gemini_flash', label: 'Gemini flash' },
]
const TICKET_TYPE_OPTIONS = [
  { value: 'request', label: 'Request' },
  { value: 'issue', label: 'Issue' },
  { value: 'question', label: 'Question' },
]
const COMPLEXITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

function App() {
  const [session, setSession] = useState<Session | null>(() => readSession())
  const [adminView, setAdminView] = useState<'kanban' | 'table'>('kanban')
  const {
    tickets,
    messages,
    selectedTicketId,
    setSelectedTicket,
    fetchProjects,
    fetchTickets,
    fetchMessages,
    approveTicket,
    rejectTicket,
    retryTicket,
  } = useTicketStore()

  useEffect(() => {
    if (!session) return
    fetchProjects()
    fetchTickets()
    const timer = window.setInterval(fetchTickets, 3000)
    return () => window.clearInterval(timer)
  }, [fetchProjects, fetchTickets, session])

  const visibleTickets = useMemo(() => {
    if (!session) return []
    if (session.role === 'admin') return tickets
    return tickets.filter((ticket) => ticket.requester_name === session.name)
  }, [session, tickets])

  const selectedTicket = selectedTicketId
    ? visibleTickets.find((ticket) => ticket.id === selectedTicketId)
    : undefined

  useEffect(() => {
    if (!selectedTicket?.id) return
    fetchMessages(selectedTicket.id)
    const timer = window.setInterval(() => fetchMessages(selectedTicket.id), 2500)
    return () => window.clearInterval(timer)
  }, [fetchMessages, selectedTicket?.id])

  const groupedTickets = useMemo(
    () =>
      STATUSES.map((status) => ({
        status,
        tickets: visibleTickets.filter((ticket) => ticket.status === status),
      })),
    [visibleTickets],
  )

  const handleLogin = (nextSession: Session) => {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession))
    setSession(nextSession)
  }

  const handleLogout = () => {
    window.localStorage.removeItem(SESSION_KEY)
    setSelectedTicket(null)
    setSession(null)
  }

  if (!session) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return (
    <div className="flex h-screen overflow-hidden text-foreground">
      {session.role === 'user' ? (
        <UserLayout
          session={session}
          ticket={selectedTicket}
          tickets={visibleTickets}
          messages={messages[selectedTicket?.id ?? ''] ?? []}
          onLogout={handleLogout}
        />
      ) : (
        <div className="flex h-full flex-1 flex-col bg-muted/40">
          <header className="flex shrink-0 items-center justify-between border-b bg-card px-4 py-3 shadow-sm md:px-6">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/25">
                <LayoutDashboard className="size-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight">EL Assistant Desk</h1>
                <p className="text-xs text-muted-foreground">{tickets.length} total tickets</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="default">Admin</Badge>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="size-4" />
              </Button>
            </div>
          </header>
          <section className="flex min-h-0 flex-1 gap-4 overflow-hidden p-4 md:p-6">
            <div className="min-w-0 flex-1 overflow-auto">
              <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Ticket Queue</h2>
                  <p className="text-sm text-muted-foreground">
                    Low/medium run by queue, hard waits for approval.
                  </p>
                </div>
                <TabsList>
                  <TabsTrigger active={adminView === 'kanban'} onClick={() => setAdminView('kanban')}>
                    <KanbanSquare />
                    Kanban
                  </TabsTrigger>
                  <TabsTrigger active={adminView === 'table'} onClick={() => setAdminView('table')}>
                    <Table2 />
                    Table
                  </TabsTrigger>
                </TabsList>
              </div>
              {adminView === 'kanban' ? (
                <div className="grid gap-3 overflow-x-auto pb-2 md:grid-cols-3 xl:grid-cols-6">
                  {groupedTickets.map((group) => (
                    <Card key={group.status} className="min-h-[620px] min-w-[210px] bg-muted/60 shadow-none">
                      <CardHeader className="flex-row items-center justify-between space-y-0 p-3">
                        <CardTitle className="text-sm">{STATUS_LABELS[group.status]}</CardTitle>
                        <Badge variant="outline">{group.tickets.length}</Badge>
                      </CardHeader>
                      <CardContent className="grid gap-2 p-3 pt-0">
                        {group.tickets.map((ticket) => (
                          <TicketCard
                            key={ticket.id}
                            ticket={ticket}
                            active={ticket.id === selectedTicket?.id}
                            onSelect={() => setSelectedTicket(ticket.id)}
                          />
                        ))}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <TicketTable
                  tickets={visibleTickets}
                  selectedId={selectedTicket?.id}
                  onSelect={setSelectedTicket}
                />
              )}
            </div>
            <div className="hidden w-[430px] shrink-0 xl:block">
              <TicketInspector
                ticket={selectedTicket}
                messages={messages[selectedTicket?.id ?? ''] ?? []}
                onApprove={() => selectedTicket && approveTicket(selectedTicket.id)}
                onReject={() => selectedTicket && rejectTicket(selectedTicket.id)}
                onRetry={() => selectedTicket && retryTicket(selectedTicket.id)}
              />
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

function UserLayout({
  session,
  ticket,
  tickets,
  messages,
  onLogout,
}: {
  session: Session
  ticket: Ticket | undefined
  tickets: Ticket[]
  messages: TicketMessage[]
  onLogout: () => void
}) {
  const setSelectedTicket = useTicketStore((state) => state.setSelectedTicket)
  return (
    <div className="flex min-h-0 flex-1 overflow-hidden">
      {/* ── Left sidebar: branding + chat history ── */}
      <aside className="flex w-60 shrink-0 flex-col border-r bg-card">
        {/* Brand */}
        <div className="flex items-center gap-2.5 border-b px-4 py-3">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="size-4" />
          </div>
          <span className="text-sm font-bold tracking-tight">EL Assistant</span>
        </div>

        {/* Nav */}
        <nav className="space-y-0.5 border-b px-2 py-2">
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-accent-foreground transition-colors hover:bg-accent/80"
            onClick={() => setSelectedTicket(null)}
          >
            <Plus className="size-4" />
            New Chat
          </button>
        </nav>

        {/* History list */}
        <div className="flex items-center justify-between px-4 pt-3 pb-1">
          <span className="text-xs font-semibold text-muted-foreground">History</span>
          <span className="text-xs text-muted-foreground">{tickets.length}</span>
        </div>
        <div className="flex-1 overflow-auto px-2 pb-2">
          {tickets.length ? (
            tickets.map((item) => (
              <ChatListItem
                key={item.id}
                ticket={item}
                active={item.id === ticket?.id}
              />
            ))
          ) : (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              No chats yet
            </p>
          )}
        </div>

        {/* User footer */}
        <div className="flex items-center gap-2 border-t px-3 py-3">
          <div className="flex size-8 items-center justify-center rounded-full bg-secondary text-sm font-semibold">
            {session.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{session.name}</p>
          </div>
          <Button variant="ghost" size="icon" className="size-7" onClick={onLogout}>
            <LogOut className="size-3.5" />
          </Button>
        </div>
      </aside>

      {/* ── Center: chat area ── */}
      {ticket ? (
        <ChatPanel ticket={ticket} messages={messages} />
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center bg-muted/20">
          <Sparkles className="mb-4 size-12 text-primary/20" />
          <h2 className="text-xl font-semibold">Welcome to EL Assistant</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure your task on the right, then send a chat.
          </p>
        </div>
      )}

      {/* ── Right sidebar: configuration ── */}
      <aside className="flex w-72 shrink-0 flex-col border-l bg-card">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <Settings className="size-4 text-muted-foreground" />
            <span className="text-sm font-semibold">Configuration</span>
          </div>
          <MoreHorizontal className="size-4 text-muted-foreground" />
        </div>
        <div className="flex-1 overflow-auto p-4">
          <UserTicketComposer requesterName={session.name} />
        </div>
      </aside>
    </div>
  )
}

function ChatListItem({ ticket, active }: { ticket: Ticket; active: boolean }) {
  const setSelectedTicket = useTicketStore((state) => state.setSelectedTicket)
  return (
    <button
      className={cn(
        'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors hover:bg-accent',
        active && 'bg-accent',
      )}
      onClick={() => setSelectedTicket(ticket.id)}
    >
      <StatusDot status={ticket.status} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{ticket.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {projectNameFromPath(ticket.repository_path)}
        </p>
      </div>
    </button>
  )
}

function ChatPanel({ ticket, messages }: { ticket: Ticket; messages: TicketMessage[] }) {
  const [message, setMessage] = useState('')
  const sendMessage = useTicketStore((state) => state.sendMessage)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!message.trim()) return
    await sendMessage(ticket.id, message.trim())
    setMessage('')
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col bg-muted/20">
      {/* Chat header */}
      <div className="flex shrink-0 items-center justify-between border-b bg-card px-6 py-3">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold">{ticket.title}</h2>
          <p className="text-xs text-muted-foreground">
            {ticket.ticket_type} · {ticket.complexity} · {ticket.agent_provider || 'auto'} · {projectNameFromPath(ticket.repository_path)}
          </p>
        </div>
        <StatusBadge status={ticket.status} />
      </div>

      {/* Messages — scrollable, fills available space */}
      <div className="flex-1 overflow-auto px-6 py-5">
        <div className="mx-auto flex max-w-2xl flex-col gap-3">
          {messages.map((item) => (
            <MessageBubble key={item.id} message={item} />
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input — pinned to bottom */}
      <div className="shrink-0 border-t bg-card px-6 py-3">
        <form className="mx-auto flex max-w-2xl items-center gap-2" onSubmit={submit}>
          <Input
            className="flex-1"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Type your message..."
          />
          <Button type="submit" size="icon" className="shrink-0">
            <Send className="size-4" />
          </Button>
        </form>
      </div>
    </section>
  )
}

function LoginScreen({ onLogin }: { onLogin: (session: Session) => void }) {
  const [role, setRole] = useState<SessionRole>('user')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const cleanName = name.trim()
    if (!cleanName) {
      setError('Name is required.')
      return
    }
    if (role === 'admin' && password !== ADMIN_PASSWORD) {
      setError('Admin passphrase is incorrect.')
      return
    }
    setError('')
    onLogin({ role, name: cleanName })
  }

  return (
    <main className="grid min-h-screen place-items-center bg-linear-to-br from-primary/5 via-background to-primary/10 p-4">
      <Card className="w-full max-w-md animate-fade-in shadow-lg">
        <CardHeader>
          <div className="mb-3 flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/25">
            <Bot className="size-6" />
          </div>
          <CardTitle className="text-xl">EL Assistant Desk</CardTitle>
          <CardDescription>Login untuk memisahkan workspace user dan admin.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={submit}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger type="button" active={role === 'user'} onClick={() => setRole('user')}>
                <UserRound />
                User
              </TabsTrigger>
              <TabsTrigger type="button" active={role === 'admin'} onClick={() => setRole('admin')}>
                <LayoutDashboard />
                Admin
              </TabsTrigger>
            </TabsList>
            <div className="grid gap-2">
              <Label htmlFor="name">{role === 'admin' ? 'Admin name' : 'FE/QA name'}</Label>
              <Input
                id="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder={role === 'admin' ? 'Rafael' : 'Frontend Team'}
              />
            </div>
            {role === 'admin' && (
              <div className="grid gap-2">
                <Label htmlFor="password">Admin passphrase</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Default: admin"
                />
              </div>
            )}
            {error && <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full">
              Login
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

function UserTicketComposer({ requesterName }: { requesterName: string }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [ticketType, setTicketType] = useState<TicketType>('request')
  const [complexity, setComplexity] = useState<TicketComplexity>('low')
  const [agentProvider, setAgentProvider] = useState('')
  const [selectedProjectPath, setSelectedProjectPath] = useState('')
  const createTicket = useTicketStore((state) => state.createTicket)
  const projects = useTicketStore((state) => state.projects)
  const projectOptions = projects.map((project) => ({
    value: project.path,
    label: project.name,
  }))

  useEffect(() => {
    if (!selectedProjectPath && projects[0]) {
      setSelectedProjectPath(projects[0].path)
    }
  }, [projects, selectedProjectPath])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!title.trim() || !description.trim()) return
    const payload: CreateTicketPayload = {
      title: title.trim(),
      description: description.trim(),
      ticket_type: ticketType,
      complexity,
      requester_name: requesterName,
      repository_path: selectedProjectPath || undefined,
      agent_provider: agentProvider || undefined,  // ponytail: empty = Auto, backend picks via recommend_provider
    }
    await createTicket(payload)
    setTitle('')
    setDescription('')
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      {/* Project list */}
      <div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground">Project Scope</span>
          <span className="text-xs text-muted-foreground">{projectOptions.length}</span>
        </div>
        <div className="space-y-1">
          {projectOptions.length ? (
            projectOptions.map((proj) => (
              <button
                type="button"
                key={proj.value}
                className={cn(
                  'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-accent',
                  selectedProjectPath === proj.value && 'bg-accent font-medium',
                )}
                onClick={() => setSelectedProjectPath(proj.value)}
              >
                <FolderGit2 className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{proj.label}</span>
                {selectedProjectPath === proj.value && (
                  <Circle className="ml-auto size-2 shrink-0 fill-primary text-primary" />
                )}
              </button>
            ))
          ) : (
            <p className="px-3 py-2 text-xs text-muted-foreground">No projects</p>
          )}
        </div>
      </div>

      {/* Settings */}
      <div className="space-y-3 border-t pt-4">
        <span className="text-xs font-semibold text-muted-foreground">Settings</span>
        <Field label="Type">
          <Select
            value={ticketType}
            onChange={(event) => setTicketType(event.target.value as TicketType)}
            options={TICKET_TYPE_OPTIONS}
          />
        </Field>
        <Field label="Complexity">
          <Select
            value={complexity}
            onChange={(event) => setComplexity(event.target.value as TicketComplexity)}
            options={COMPLEXITY_OPTIONS}
          />
        </Field>
        <Field label="Agent Provider">
          <Select
            value={agentProvider}
            onChange={(event) => setAgentProvider(event.target.value)}
            options={PROVIDERS}
          />
        </Field>
      </div>

      {/* New chat */}
      <div className="space-y-3 border-t pt-4">
        <span className="text-xs font-semibold text-muted-foreground">New Chat</span>
        <Field label="Title">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Short summary" required />
        </Field>
        <Field label="Message">
          <Textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={4}
            placeholder="Describe your request..."
            required
          />
        </Field>
        <Button type="submit" className="w-full">
          <Plus className="size-4" />
          New Chat
        </Button>
      </div>
    </form>
  )
}

function MessageBubble({ message }: { message: TicketMessage }) {
  return (
    <article
      className={cn(
        'animate-fade-in max-w-[82%] rounded-2xl px-4 py-2.5 text-sm shadow-sm',
        message.role === 'user' && 'ml-auto bg-primary text-primary-foreground',
        message.role === 'assistant' && 'border border-emerald-200 bg-emerald-50 text-emerald-900',
        message.role === 'system' && 'max-w-full border border-amber-200 bg-amber-50 text-amber-900',
        message.role === 'admin' && 'border border-violet-200 bg-violet-50 text-violet-900',
      )}
    >
      <div className={cn(
        'mb-1 text-[11px] font-semibold uppercase',
        message.role === 'user' ? 'text-primary-foreground/70' : 'text-muted-foreground',
      )}>{message.role}</div>
      <p className="whitespace-pre-wrap leading-6">{message.content}</p>
    </article>
  )
}

function TicketCard({
  ticket,
  active,
  onSelect,
}: {
  ticket: Ticket
  active: boolean
  onSelect: () => void
}) {
  return (
    <button
      className={cn(
        'grid gap-2 rounded-xl border bg-card p-3 text-left text-card-foreground shadow-sm transition-all hover:bg-accent hover:shadow-md',
        active && 'ring-2 ring-ring',
      )}
      onClick={onSelect}
    >
      <strong className="truncate text-sm">{ticket.title}</strong>
      <span className="text-xs text-muted-foreground">{ticket.requester_name || 'FE/QA'}</span>
      <span className="flex items-center gap-1 truncate text-xs text-muted-foreground">
        <FolderGit2 className="size-3" />
        {projectNameFromPath(ticket.repository_path)}
      </span>
      <div className="flex flex-wrap gap-1">
        <Badge variant="outline">{ticket.ticket_type}</Badge>
        <Badge variant="secondary">{ticket.complexity}</Badge>
      </div>
    </button>
  )
}

function TicketTable({
  tickets,
  selectedId,
  onSelect,
}: {
  tickets: Ticket[]
  selectedId: string | undefined
  onSelect: (id: string) => void
}) {
  return (
    <Card className="overflow-hidden">
      <div className="overflow-auto">
        <table className="w-full min-w-[780px] border-collapse text-sm">
          <thead className="bg-muted/70 text-muted-foreground">
            <tr>
              <th className="border-b px-4 py-3 text-left font-medium">Title</th>
              <th className="border-b px-4 py-3 text-left font-medium">Status</th>
              <th className="border-b px-4 py-3 text-left font-medium">Type</th>
              <th className="border-b px-4 py-3 text-left font-medium">Complexity</th>
              <th className="border-b px-4 py-3 text-left font-medium">Project</th>
              <th className="border-b px-4 py-3 text-left font-medium">Agent</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr
                key={ticket.id}
                className={cn('cursor-pointer border-b transition-colors hover:bg-accent', ticket.id === selectedId && 'bg-accent')}
                onClick={() => onSelect(ticket.id)}
              >
                <td className="px-4 py-3 font-medium">{ticket.title}</td>
                <td className="px-4 py-3"><StatusBadge status={ticket.status} /></td>
                <td className="px-4 py-3">{ticket.ticket_type}</td>
                <td className="px-4 py-3">{ticket.complexity}</td>
                <td className="px-4 py-3">{projectNameFromPath(ticket.repository_path)}</td>
                <td className="px-4 py-3">{ticket.agent_provider}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

function TicketInspector({
  ticket,
  messages,
  onApprove,
  onReject,
  onRetry,
}: {
  ticket: Ticket | undefined
  messages: TicketMessage[]
  onApprove: () => void
  onReject: () => void
  onRetry: () => void
}) {
  if (!ticket) return <EmptyState text="No ticket selected." />

  return (
    <Card className="flex h-full flex-col overflow-hidden">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>Admin Log</CardTitle>
            <CardDescription>Conversation, execution output, and git diff.</CardDescription>
          </div>
          <StatusBadge status={ticket.status} />
        </div>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-4 overflow-auto">
        <div className="grid grid-cols-[96px_1fr] gap-x-3 gap-y-2 rounded-xl border bg-muted/30 p-3 text-sm">
          <span className="text-muted-foreground">Requester</span>
          <strong className="min-w-0 break-words">{ticket.requester_name || 'FE/QA'}</strong>
          <span className="text-muted-foreground">Review</span>
          <strong className="min-w-0 break-words">{ticket.review_status}</strong>
          <span className="text-muted-foreground">Project</span>
          <strong className="min-w-0 break-words">{ticket.repository_path || '-'}</strong>
          <span className="text-muted-foreground">Branch</span>
          <strong className="min-w-0 break-words">{ticket.branch || '-'}</strong>
          <span className="text-muted-foreground">Agent</span>
          <strong className="min-w-0 break-words">{ticket.agent_provider}</strong>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <Button size="sm" onClick={onApprove} disabled={ticket.status !== 'review_required'}>
            <CheckCircle2 />
            Approve
          </Button>
          <Button variant="destructive" size="sm" onClick={onReject} disabled={ticket.status !== 'review_required'}>
            <XCircle />
            Reject
          </Button>
          <Button variant="outline" size="sm" onClick={onRetry} disabled={ticket.status === 'in_progress'}>
            <RefreshCw />
            Retry
          </Button>
        </div>
        <LogBlock
          title="Conversation"
          icon={<MessageSquareText className="size-4" />}
          value={messages.map((message) => `${message.role}: ${message.content}`).join('\n\n')}
        />
        <LogBlock
          title="Agent output"
          icon={<ClipboardList className="size-4" />}
          value={ticket.execution_log || ticket.result || ''}
        />
        <LogBlock title="Git diff" icon={<KanbanSquare className="size-4" />} value={ticket.diff || ''} />
      </CardContent>
    </Card>
  )
}

function LogBlock({ title, icon, value }: { title: string; icon: ReactNode; value: string }) {
  return (
    <section className="grid gap-2">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h3>
      <pre className="max-h-56 min-h-24 overflow-auto rounded-xl border bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        {value || '-'}
      </pre>
    </section>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label className="text-xs">{label}</Label>
      {children}
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <Card className="grid min-h-60 place-items-center p-6 text-sm text-muted-foreground">
      {text}
    </Card>
  )
}

const STATUS_COLORS: Record<string, string> = {
  completed: 'text-emerald-500',
  failed: 'text-red-500',
  in_progress: 'text-blue-500 animate-pulse-dot',
  review_required: 'text-amber-500',
  queued: 'text-muted-foreground',
  pending: 'text-muted-foreground/50',
}

function StatusDot({ status }: { status: string }) {
  return <Circle className={cn('size-2.5 fill-current', STATUS_COLORS[status] ?? 'text-muted-foreground')} />
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'completed'
      ? 'success'
      : status === 'failed'
        ? 'destructive'
        : status === 'review_required'
          ? 'warning'
          : status === 'queued'
            ? 'secondary'
            : 'outline'
  return <Badge variant={variant}>{STATUS_LABELS[status] ?? status}</Badge>
}

function projectNameFromPath(repositoryPath: string | null) {
  if (!repositoryPath) return 'Default project'
  const cleanPath = repositoryPath.replace(/\/$/, '')
  return cleanPath.split('/').pop() || repositoryPath
}

function readSession(): Session | null {
  const rawSession = window.localStorage.getItem(SESSION_KEY)
  if (!rawSession) return null
  try {
    const parsedSession = JSON.parse(rawSession) as Session
    if (parsedSession.role && parsedSession.name) return parsedSession
  } catch {
    window.localStorage.removeItem(SESSION_KEY)
  }
  return null
}

export default App
