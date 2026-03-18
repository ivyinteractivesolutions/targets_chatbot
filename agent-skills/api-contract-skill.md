# API Contract Skill

Project: `targets_chatbot`

## Scope

Chat endpoint contract consistency, payload validation, and actionable error handling.

## Core Rules

- Validate route and payload contract before changing behavior.
- Keep request/response fields stable for UI integration.
- Return consistent and actionable error semantics.
- Treat contract drift as a release blocker until clarified.

## Checklist

- Verify required fields and payload shape (including session identifiers).
- Verify response fields expected by frontend logic.
- Validate error paths and user-facing messages.
- Confirm Postman collection examples remain consistent.

## Do Not

- Do not silently change response field names/types.
- Do not swallow contract mismatches as generic failures.
- Do not ship endpoint changes without integration verification.
