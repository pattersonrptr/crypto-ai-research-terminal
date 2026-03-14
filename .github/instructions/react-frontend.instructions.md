---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx"
---

# React / TypeScript frontend instructions

## Style
- Use **functional components** only — no class components.
- All props must be typed with a dedicated `interface` or `type`, never `any`.
- Prefer **named exports** over default exports for components.
- Use **React Query** for all server state; **Zustand** for client-only state.

## File organisation
- One component per file; file name matches component name (PascalCase).
- Co-locate component styles (TailwindCSS classes) in the component file.
- API call functions live exclusively in `src/services/`.

## Accessibility
- Every interactive element must have a descriptive `aria-label` or visible label.
- Use semantic HTML elements (`<button>`, `<nav>`, `<main>`, etc.) over generic `<div>`.

## Testing — Test-Driven Development (mandatory)

This project follows strict TDD on the frontend. The cycle is identical to the backend rule:

1. **Red** — Write a failing test that describes the expected behaviour. Run it and confirm it fails.
2. **Green** — Write the minimum component/hook/service code to make the test pass. Nothing more.
3. **Refactor** — Clean up without changing behaviour. Re-run tests to confirm still green.

**Rules:**
- Never write a component, hook, or service before a failing test exists for it.
- One behaviour per test. Name tests as `renders <component> when <condition>` or `calls <fn> when <event>`.
- Test files live next to their components: `ComponentName.test.tsx`.
- Hook tests live next to their hooks: `useHookName.test.ts`.
- Service tests live next to their services: `resourceName.service.test.ts`.
- Tools: **Vitest** + **React Testing Library** + **MSW** (Mock Service Worker for API mocking).
- Minimum coverage target: **80%** per module (same policy as backend).
- `vitest run --coverage` must pass before every commit.
