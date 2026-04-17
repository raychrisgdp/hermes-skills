# Mermaid Presentability Examples

These are copy-paste templates meant for repo docs, specs, and roadmaps.

## 1. Architecture / system context flowchart

```mermaid
flowchart TB
    Client[Client]
    UI[Operator UI]
    SDK[SDK / CLI]

    subgraph Server[GL Runner Server]
        API[API Layer]
        CTRL[Control Plane]
        RECON[Reconciliation Module]
    end

    ORCH[Orchestration Backend]

    subgraph Worker[GL Runner Worker]
        HOST[Worker Host]
        RT[Runtime Adapters]
        CODE[Runnable Code]
    end

    DB[(PostgreSQL)]
    OBJ[(Artifact Storage)]
    EXT[GL Connector / Remote APIs]

    SDK --> API
    UI --> API
    Client --> API
    API --> CTRL
    CTRL --> RECON
    RECON --> ORCH
    ORCH --> HOST
    HOST --> RT
    RT --> CODE
    CTRL --> DB
    RT --> OBJ
    CODE --> EXT

    classDef glOwned fill:#E8F0FE,stroke:#4F46E5,color:#1F2A44,stroke-width:1.5px;
    classDef backend fill:#F3F4F6,stroke:#6B7280,color:#111827;
    classDef storage fill:#ECFDF5,stroke:#059669,color:#064E3B;
    classDef edge fill:#F8FAFC,stroke:#94A3B8,color:#334155;

    class API,CTRL,RECON,HOST,RT,CODE glOwned;
    class ORCH backend;
    class DB,OBJ storage;
    class Client,UI,SDK,EXT edge;
```

## 2. Lifecycle / background execution sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant S as GL Runner Server
    participant O as Prefect Server
    participant W as Worker
    participant D as PostgreSQL

    C->>S: Run runnable
    S->>D: Create canonical run
    S->>O: Submit flow run
    O->>W: Assign work
    W->>D: Append run events
    W-->>S: Report status
    S-->>C: Stream progress
```

## 3. GL-owned ERD

```mermaid
erDiagram
    TENANTS ||--o{ ACCOUNTS : has
    TENANTS ||--o{ RUNNABLES : scopes
    TENANTS ||--o{ RUNS : scopes
    RUNNABLES ||--o{ RUNS : executes
    RUNS ||--o{ RUN_EVENTS : emits
    RUNNABLES ||--o{ RUNNABLE_LINKS : parent
    RUNNABLES ||--o{ RUNNABLE_LINKS : child

    TENANTS {
        uuid id PK
        text key UK
        text status
    }
    ACCOUNTS {
        uuid id PK
        uuid tenant_id FK
        text key
        text status
    }
    RUNNABLES {
        uuid id PK
        uuid tenant_id FK
        text key
        text kind
        text status
    }
    RUNS {
        uuid id PK
        uuid tenant_id FK
        uuid runnable_id FK
        text status
        text backend_kind
    }
    RUN_EVENTS {
        uuid id PK
        uuid run_id FK
        text event_type
        timestamptz event_ts
    }
    RUNNABLE_LINKS {
        uuid id PK
        uuid parent_runnable_id FK
        uuid child_runnable_id FK
        text link_type
    }
```

## 4. Roadmap / phase progression

```mermaid
flowchart LR
    GL0[GL0<br/>Foundation]
    GL1[GL1<br/>Core Service]
    GL2A[GL2a<br/>Experience]
    GL2B[GL2b<br/>Orchestration]
    GL3[GL3<br/>Background]
    GL4[GL4<br/>HITL]
    GL5[GL5<br/>Ecosystem]

    GL0 --> GL1
    GL1 --> GL2A
    GL1 --> GL2B
    GL2A --> GL3
    GL2B --> GL3
    GL3 --> GL4
    GL4 --> GL5

    classDef critical fill:#E8F0FE,stroke:#4F46E5,color:#1F2A44,stroke-width:2px;
    classDef parallel fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:1.5px;
    classDef future fill:#F3F4F6,stroke:#6B7280,color:#111827;

    class GL0,GL1,GL3 critical;
    class GL2A,GL2B parallel;
    class GL4,GL5 future;
```

## 5. Interface / abstraction class diagram

```mermaid
classDiagram
    class ExecutionBackend {
        +submit_run(run)
        +cancel_run(run_id)
    }

    class RunnableAdapter {
        +load_runnable(definition)
        +run(runnable, payload, context)
    }

    class ScheduleAuthority {
        +upsert_schedule(schedule)
        +reconcile(schedule)
    }

    class PrefectExecutionBackend
    class AgentAdapter

    ExecutionBackend <|.. PrefectExecutionBackend
    RunnableAdapter <|.. AgentAdapter
```

## 6. State diagram

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> running: worker starts
    running --> completed: success
    running --> failed: error
    running --> cancelled: cancel request
    failed --> pending: retry
    completed --> [*]
    cancelled --> [*]
```
