# SDLC Policy

The lifecycle every feature follows in this organization. Agents may cite this
to justify process decisions.

## P-1 Pipeline stages
Requirements → Design → Implementation → Test → Review → Documentation. No stage
is skipped; Review can send work back to Implementation.

## P-2 Review gate
A human-in-the-loop review gate precedes any write to a real system of record
(e.g. creating issues on a real JIRA board).

## P-3 Traceability
Every story traces back to a requirement, and every code change traces to a
story. Prefer small, reviewable increments.

## P-4 Accessibility
User-facing features meet basic accessibility: labelled form fields, keyboard
navigation, and screen-reader-announced errors.

## P-5 Grounding
Generated requirements and designs must be grounded in these standards and cite
the sources used, to reduce hallucination and ensure consistency.

