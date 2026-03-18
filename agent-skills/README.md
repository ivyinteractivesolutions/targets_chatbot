# Chatbot Agent Skills

Use these files as task-specific playbooks for `targets_chatbot`.

## Skill Files

- `rag-skill.md`: knowledge authoring, ingestion, retrieval quality checks.
- `session-memory-skill.md`: session lifecycle and safe memory behavior.
- `api-contract-skill.md`: endpoint/payload consistency and error semantics.
- `task-update-flow.md`: how to keep skill docs updated after each meaningful task.

## Usage Rule

For each chatbot task:

1. Select the closest skill file.
2. Execute with that checklist.
3. Update the file with durable lessons after completion.
4. Add a new skill file if a repeated task type is not covered.
