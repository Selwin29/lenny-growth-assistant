# UI/UX Design Documentation - Lenny Growth Assistant

## 1. Theme and Aesthetic
The user interface matches a sleek dark-theme aesthetic using high contrast slate shades (`bg-slate-950` to `bg-slate-900`) and warm amber accents (`text-amber-400` / `bg-amber-500`) to highlight primary triggers and AI actions.

## 2. Layout Structure
- **Sidebar**: Sticky panel managing chat sessions (creating, renaming, deleting) and exposing the user's email and logout trigger. Collapses into a responsive hamburger drawer on mobile viewports.
- **Chat Window**: Multi-turn dialog box showing user messages (slate bg) and assistant responses (dark slate bg) formatted with code highlighting and markdown text.
- **Artifact Viewer**: A side-by-side split viewport triggered by clicking the view artifact button. Accommodates Preview (executes HTML/CSS in an iframe or renders markdown) and Code tabs (shows source markup).

## 3. Micro-animations
- Smooth hover state transitions on all interactive buttons.
- Sliding side animations for the sidebar drawer and the side-by-side artifact viewer panel.
- Spinner state animations during LLM query planning and response processing.
