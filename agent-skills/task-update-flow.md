# Task Update Flow

Project: `targets_chatbot`

## Goal

Continuously update skill files so each new Cursor task has an accurate starting playbook.

## Per-Task Update Protocol

After each meaningful task:

1. Identify the used skill file (`rag-skill.md`, `session-memory-skill.md`, `api-contract-skill.md`).
2. Add or update a `Latest Updates` section with:
   - date
   - task summary
   - durable lesson
3. Add a new skill file if a recurring task type is uncovered.
4. Monthly: cleanup stale/duplicated guidance.

## Entry Template

- `YYYY-MM-DD`: `<task>` -> `<durable rule>` -> applies to `<routes/nodes/components>`.
