# Session and Memory Skill

Project: `targets_chatbot`

## Scope

Session lifecycle, memory persistence behavior, and safe handling of context data.

## Core Rules

- Keep active-task memory concise and relevant.
- Persist only durable, non-sensitive preferences/facts.
- Keep session operations predictable and reversible.
- Prefer memory summaries over raw verbose logs.

## Checklist

- Confirm session create/load/list behavior works as expected.
- Ensure context continuity for multi-turn user flows.
- Ensure corrected user preferences overwrite stale assumptions.
- Verify sensitive data is not persisted.

## Do Not

- Do not store secrets, tokens, or personal sensitive data in memory.
- Do not keep stale assumptions after explicit user correction.
- Do not bloat memory with one-off debugging traces.
