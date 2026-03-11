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

## Testing
- Component tests with **Vitest** + **React Testing Library**.
- Test files live next to their components: `ComponentName.test.tsx`.
