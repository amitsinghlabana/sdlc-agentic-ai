# Coding Standards

House engineering conventions. Agents should follow and cite these when making
implementation or design decisions.

## C-1 Language & style
Python services use FastAPI + Pydantic for validation. Type-hint public
functions. Keep modules small and single-purpose.

## C-2 Error handling
Never swallow exceptions silently. Surface clean error responses (no stack
traces to clients). Log with context at the boundary.

## C-3 Testing
Every feature ships with focused unit tests covering the happy path and at
least one failure path. Prefer fast, deterministic, offline tests.

## C-4 Configuration
All configuration is environment-driven with safe defaults. No environment may
require editing source code to run.

## C-5 Dependencies
Add dependencies deliberately and pin sensible minimums. Prefer the standard
library and already-present packages.

