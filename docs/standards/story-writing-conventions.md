# Story Writing Conventions

How user stories and JIRA issues must be shaped. The Requirements agent should
follow and cite these when authoring `stories.json`.

## W-1 Story format
Each story uses "As a <role>, I want <goal> so that <benefit>". Summaries are
under 255 characters and start with a verb.

## W-2 Acceptance criteria
Every story lists testable acceptance criteria as short bullet points. Each
criterion must be objectively verifiable.

## W-3 Sub-tasks
Each story includes 2–4 concrete implementation sub-tasks (e.g. build UI, add
API endpoint, write tests) so work is trackable.

## W-4 Labels & estimation
Apply lowercase, hyphenated labels (no spaces). Provide a story-point estimate
using a Fibonacci-like scale (1, 2, 3, 5, 8).

## W-5 Definition of done
A story is done only when code, tests, and docs are complete and the security
checklist items relevant to it are satisfied.

