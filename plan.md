# Engineering Standards

## Code Quality Requirements

This project must prioritize:

* Readability
* Maintainability
* Extensibility
* Testability
* Scalability

The codebase must be designed to support future growth without requiring major architectural refactoring.

---

# Clean Code Requirements

## General Rules

* Follow SOLID principles.
* Follow DRY (Don't Repeat Yourself).
* Follow KISS (Keep It Simple).
* Follow Separation of Concerns.
* Follow Dependency Inversion.
* Use explicit naming.
* Avoid hidden side effects.
* Avoid tightly coupled modules.

---

## Naming Convention

### Classes

Use PascalCase.

Examples:

```python
TicketService
GitService
AgentProvider
CodexProvider
ChatGateway
```

### Functions

Use snake_case.

Examples:

```python
create_ticket()
approve_ticket()
execute_agent_job()
get_ticket_by_id()
```

### Variables

Use descriptive names.

Good:

```python
ticket_id
repository_path
execution_result
agent_response
```

Bad:

```python
id
tmp
data
x
res
```

---

# File Size Rules

Any file exceeding:

```text
400 lines
```

must be reviewed and refactored.

Large services should be split into use cases.

Example:

```text
ticket/

├── use_cases/
│   ├── create_ticket.py
│   ├── update_ticket.py
│   ├── approve_ticket.py
│   └── reject_ticket.py
```

Avoid creating massive service files.

---

# Module Design

Each module must be self-contained.

Example:

```text
ticket/

├── api/
├── domain/
├── repository/
├── service/
├── schemas/
└── use_cases/
```

A module should contain everything needed for its own business domain.

---

# Dependency Rules

Allowed:

```text
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

Forbidden:

```text
API
 ↓
Repository
```

Forbidden:

```text
Repository
 ↓
Service
```

Forbidden:

```text
Module A Repository
 ↓
Module B Repository
```

Cross-module communication must happen through services only.

---

# Business Logic Rules

Business logic must exist only inside:

```text
service/
use_cases/
```

Business logic must never be placed inside:

* FastAPI routers
* Controllers
* WebSocket handlers
* Repositories
* Database models

---

# Repository Rules

Repositories must only perform:

* Create
* Read
* Update
* Delete

Repositories must not:

* Execute AI agents
* Execute Git commands
* Send notifications
* Contain business rules

---

# AI Provider Architecture

All AI integrations must use an abstraction layer.

Example:

```python
class AgentProvider(ABC):

    async def ask(
        self,
        prompt: str
    ) -> str:
        pass

    async def execute(
        self,
        task: AgentTask
    ) -> AgentExecutionResult:
        pass
```

Implementations:

```python
CodexProvider
AntigravityProvider
```

Services must depend on:

```python
AgentProvider
```

Never directly depend on a specific provider.

This allows future integration with:

* Claude Code
* Gemini CLI
* Cursor Agent
* OpenAI Agents

without changing business logic.

---

# Queue Design

Queue workers must never directly call Codex or Antigravity.

Correct flow:

```text
Queue
 ↓
Job
 ↓
Ticket Service
 ↓
Agent Provider
```

This prevents vendor lock-in and simplifies testing.

---

# Git Operations

All Git interactions must be centralized.

Create:

```python
GitService
```

All Git commands must go through this service.

Forbidden:

```python
subprocess.run("git ...")
```

spread throughout the codebase.

---

# Event Driven Design

Important actions must generate events.

Examples:

```python
TicketCreatedEvent

TicketApprovedEvent

TicketRejectedEvent

AgentExecutionStartedEvent

AgentExecutionFinishedEvent

GitDiffGeneratedEvent
```

Benefits:

* Easier notifications
* Easier integrations
* Easier monitoring
* Easier analytics

---

# Database Standards

Primary keys:

```text
UUID
```

required for all entities.

Mandatory audit columns:

```python
created_at
updated_at
created_by
updated_by
```

Soft delete support:

```python
deleted_at
```

for future-proofing.

---

# DTO Rules

Never expose ORM entities directly.

Forbidden:

```python
return Ticket
```

Correct:

```python
return TicketResponse
```

Always use DTOs / Pydantic schemas.

---

# Error Handling

Use domain-specific exceptions.

Examples:

```python
TicketNotFoundException

AgentExecutionException

GitOperationException

RepositoryLockedException
```

Avoid generic exceptions.

Forbidden:

```python
raise Exception(...)
```

---

# Logging Standards

Use structured logging.

Example:

```json
{
  "ticket_id": "123",
  "user_id": "456",
  "action": "ticket_created",
  "timestamp": "2026-07-04T10:00:00Z"
}
```

Never use:

```python
print()
```

for production logging.

---

# Testing Standards

Minimum requirements:

* Unit tests for services
* Repository tests
* Queue tests
* Agent integration tests

Target coverage:

```text
70%+
```

for business logic.

---

# Frontend Standards

Use feature-based architecture.

Example:

```text
src/

features/

├── auth/
├── chat/
├── ticket/
├── logs/
└── settings/
```

Avoid global folders that grow uncontrollably.

---

# State Management

Use Zustand.

Separate stores:

```text
auth-store
chat-store
ticket-store
settings-store
```

Never create a single monolithic store.

---

# Socket.IO Design

Use separate namespaces.

Example:

```text
/chat

/tickets

/admin
```

Do not place all events into a single namespace.

---

# Future Expansion Requirements

The architecture must support future implementation of:

* Multiple repositories
* Multiple AI providers
* Knowledge base
* RAG integration
* GitHub integration
* GitLab integration
* Slack integration
* Telegram integration
* Automatic Pull Requests

without requiring significant architectural changes.

---

# Golden Rule

Every new feature should ideally be implemented by modifying no more than two modules.

If implementing a feature requires changes across many unrelated modules, the architecture should be reconsidered.
