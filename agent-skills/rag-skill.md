# RAG Skill

Project: `targets_chatbot`

## Scope

Knowledge authoring, ingestion, embedding refresh, and retrieval quality safeguards.

## Core Rules

- Treat tutorial JSON files as source-of-truth content.
- Validate JSON structure before ingestion.
- Keep chunking deterministic and topic-focused.
- Re-index after meaningful knowledge updates.

## Checklist

- Validate content schema and required fields.
- Remove stale/duplicate content before ingesting.
- Run ingestion/update process and confirm completion.
- Test retrieval with representative prompts.
- Flag low-confidence retrieval results explicitly.

## Do Not

- Do not answer confidently when retrieval confidence is low.
- Do not keep contradictory duplicate entries in knowledge data.
- Do not skip ingestion verification after document updates.
