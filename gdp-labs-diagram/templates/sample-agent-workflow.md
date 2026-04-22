```mermaid
flowchart TD
    START((START)):::terminal
    START --> Intake[Intake & Validation]:::default
    Intake --> Valid{Valid?}:::default
    Valid -->|No| Error[Return Error to User]:::error
    Valid -->|Yes| Route[Route Agent]:::default
    Route --> TaskType{Task type?}:::default

    TaskType --> Research[Tool Execution]:::default
    TaskType --> Generate[Tool Execution]:::default
    TaskType --> Analyze[Tool Execution]:::default

    Research --> Review1[Review Gate]:::human
    Generate --> Review2[Review Gate]:::human
    Analyze --> Review3[Review Gate]:::human

    Review1 -->|retry| Research
    Review2 -->|retry| Generate
    Review3 -->|retry| Analyze

    Review1 --> Merge[Merge Results]:::emphasis
    Review2 --> Merge
    Review3 --> Merge

    Merge --> Finalize[Finalize & Deliver]:::default
    Finalize --> END((END)):::terminal
    Error --> END

    classDef default fill:#00A0DF,stroke:#00A0DF,color:#FFFFFF,stroke-width:2px
    classDef terminal fill:#1A3F6F,stroke:#1A3F6F,color:#FFFFFF,stroke-width:2px
    classDef human fill:#1A202C,stroke:#1A202C,color:#FFFFFF,stroke-width:2px
    classDef error fill:#CA54B0,stroke:#CA54B0,color:#FFFFFF,stroke-width:2px
    classDef emphasis fill:#306FB7,stroke:#306FB7,color:#FFFFFF,stroke-width:2px
```

**Color overrides used in this diagram:**

| Node | Color | Why |
| :--- | :--- | :--- |
| START, END | Navy Dark `#1A3F6F` | Terminal — entry/exit, oval shape |
| Review Gate (×3) | Charcoal `#1A202C` | Human gate — must never look automated |
| Return Error to User | Pink `#CA54B0` | Error/rejection path |
| Merge Results | Navy `#306FB7` | Key CTA — single most important convergence |
| Everything else | Sky Blue `#00A0DF` | Default — no justification needed |
