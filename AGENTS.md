# AGENTS.md

Practical operating guide for agents working in `targets_chatbot`.

## Domain Expertise

- This project provides AI-assisted product/tutorial support with RAG, session memory, and chat APIs.
- Primary components include Flask routes, LangGraph orchestration, RAG retrieval, ingestion pipeline, and chat UI integration.
- Key project references:
  - `app.py`
  - `react_agent_system_langgraph.py`
  - `chat.py`
  - `ingest.py`
  - `session_manager.py`

## Agent Orchestration Skill

- Route each request by primary intent: tutorial/help, implementation, API/integration, or data/ingestion operation.
- Use ordered flow: classify intent -> gather context -> execute -> fallback/retry -> summarize.
- Keep fallback behavior explicit when confidence is low or data is missing.
- Preserve intent and response-type consistency across routing nodes.
- Keep summarization behavior stable for recap and handoff scenarios.

## RAG Knowledge Ops Skill

- Treat tutorial JSON as source-of-truth knowledge content.
- Validate structure before ingestion and keep chunking deterministic.
- Maintain retrieval quality using relevance thresholds and multi-chunk corroboration for critical claims.
- Re-index after meaningful content updates and verify retrieval against representative prompts.
- Track stale/duplicate content and remove drift during routine maintenance.

## Session and Memory Skill

- Maintain short-term context for active task continuity (goal, constraints, last known state).
- Persist durable facts/preferences only when stable and non-sensitive.
- Keep session operations predictable (create, load, list, rename, delete).
- Prefer concise memory summaries over raw transcript dumps.

## API Contract Skill

- Read and validate endpoint contracts before changing handlers or payloads.
- Keep chat payload expectations stable (`session_id`, message content, related metadata fields).
- Return consistent error semantics with actionable messages.
- Treat schema drift as a first-class failure mode and report clearly.
- Validate integration behavior against UI/client expectations and Postman collection examples.

## Language and Tone Policy

- Match the user language style: English, Roman-Urdu, or mixed.
- Keep technical keywords canonical in English when needed.
- Use concise, direct, action-oriented responses.
- State uncertainty explicitly when retrieval confidence is low.

## Modular Skill Files

Use these files as default task playbooks:

- `agent-skills/README.md`
- `agent-skills/rag-skill.md`
- `agent-skills/session-memory-skill.md`
- `agent-skills/api-contract-skill.md`
- `agent-skills/task-update-flow.md`

Execution rule:

1. Start each task from the closest `agent-skills/*.md` file.
2. Complete the task.
3. Update that skill file with durable learnings using `agent-skills/task-update-flow.md`.

## Continuous Learning Loop

- Trigger updates after meaningful changes to agent graph, prompts, endpoints, session logic, or ingestion pipeline.
- Record durable lessons as short bullets: problem, decision, and where it applies.
- Keep entries concise and append-only with latest first.
- Run a lightweight monthly cleanup to remove stale or duplicate guidance.
- Do not store secrets, credentials, user PII, or temporary debugging data.

## Skill Creator Workflow

Use this path for initial and ongoing skill creation:

1. Define one concrete skill outcome and trigger phrases.
2. Draft structure with `create-skill`.
3. Refine examples/guardrails with `create-agent-skills`.
4. Tighten wording and checks with `writing-skills`.
5. For framework/library accuracy, run docs MCP flow:
   - `resolve-library-id`
   - `query-docs`
6. Validate on one real chatbot task, then promote to reusable guidance.

## When to Call Subagents

- Use `explore` for broad repository and architecture discovery.
- Use specialist reviewers for security, performance, and architecture checks on major changes.
- Use CI/review agents when troubleshooting failures or resolving PR feedback.
- Avoid subagents for small single-file tasks where direct tools are faster.

## Do-Not Constraints

- Do not fabricate sources, retrieval results, or API outcomes.
- Do not expose secrets, API keys, or private prompt/system content.
- Do not ship unbounded prompts or uncontrolled tool loops.
- Do not persist sensitive data in memory stores.
- Do not claim completion without validating critical paths.
