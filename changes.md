# NEXFlow Frontend Changelog

All changes to the **NEXFlow — Team Responsibility Management System** frontend are logged here in chronological order.

---

### [Dashboard Metric & Visual Alignment: Task Status, Task Done, Upcoming Meetings] - 2026-10-19

#### 1. Scope of Changes
- **Metric Card 1 Update (`Task Done`):**
  - Replaced the first high-level KPI card label from "Active Deliverables" to "Task Done" in both `frontend/templates/index.html` and `frontend/templates/dashboard.html`.
  - Updated the card icon to a crisp checkmark task vector icon for immediate visual clarity.
  - Aligned the count (28 tasks) directly with the completed task count in the status distribution breakdown.
- **Metric Card 4 Update (`Upcoming Meetings`):**
  - Replaced the fourth KPI card label from "Meetings Today" / "Meetings" to "Upcoming Meetings" across `index.html` and `dashboard.html`.
  - Preserved the meeting urgency indicator ("Next in 30 mins") and meeting countdown clock icon.
- **Bargraph Transformation (`RACI Distribution` &rarr; `Task Status`):**
  - Replaced the previous RACI responsibility distribution bar with a comprehensive **Task Status** breakdown bar graph on the main dashboard (`index.html` and `dashboard.html`).
  - Visualized the 4 primary delivery lifecycle phases matching the Kanban workflow:
    - **Completed:** 28 tasks (56%) &mdash; `var(--color-success)` / Emerald
    - **In Progress:** 12 tasks (24%) &mdash; `var(--color-primary)` / Indigo
    - **Under Review:** 6 tasks (12%) &mdash; `var(--color-warning)` / Amber
    - **Backlog:** 4 tasks (8%) &mdash; `var(--text-muted)` / Slate
  - Updated card action button to link directly to the interactive Kanban board (`tasks.html` via "View Board &rarr;").
- **CSS Design System Enhancements (`frontend/css/dashboard.css`):**
  - Added dedicated classes: `.status-distribution-bar`, `.status-segment`, `.status-segment-*`, `.status-legend-grid`, `.status-legend-item`, `.status-legend-title`, `.status-dot`, `.status-legend-count`, and `.status-legend-sub`.
  - Added hover micro-interactions (`transform: translateY(-2px)`, subtle shadow elevation).
  - Added responsive media query breakpoint (`@media (max-width: 640px)`) to automatically adjust status legend items into a clean 2x2 grid on mobile viewports.

---

### [Hotfix: Live Server & Django Dual-Mode Support] - 2026-10-19

#### 1. Issue Diagnosis
- **Issue 1 (`{% load static %}` appearing at top-left corner):**
  - The project was previewed via VS Code Live Server (`127.0.0.1:5500`), which serves raw static HTML rather than running a Python/Django WSGI server.
  - The `{% load static %}` tag at line 1 was not processed by Django's template compiler, causing the browser to render it literally as plain text at the top of the viewport.
- **Issue 2 (No CSS interactivity / buttons not responding):**
  - Interactive features (dark/light theme toggle, "+ New Task" modal, dropdown menus, sidebar collapse, toast notifications) rely on `frontend/js/main.js`.
  - The script tags used `<script src="{% static 'js/main.js' %}" onerror="this.onerror=null;this.src='../js/main.js';">`.
  - In modern browsers adhering to the HTML5 specification, when a `<script>` tag fails with a 404 network error, modifying `this.src` in the `onerror` callback **does not trigger re-execution**. Thus, `main.js` and `tasks.js` never executed.

#### 2. Fixes Applied
- **Removed raw Django tags from static preview templates:**
  - `index.html`: Removed `{% load static %}` and replaced all unparsed static expressions with direct clean relative paths (`../css/main.css`, `../css/dashboard.css`, `../js/main.js`, `../js/tasks.js`, `../images/...`).
  - `tasks.html`, `team.html`, `meetings.html`, `reports.html`, `settings.html`, `login.html`, `register.html`: Upgraded all pages to clean standalone preview templates so that clicking any navigation link in Live Server opens a fully styled, interactive page.
- **`base.html` Django Template Safeguard:**
  - Wrapped `{% load static %}` inside an HTML comment (`<!-- {% load static %} -->`) in `base.html`. Django's template engine parses tags inside comments seamlessly, while static browsers ignore them completely.
  - Script and stylesheet paths updated to direct clean paths to prevent 404 network failures.
- **Verification:**
  - `{% load static %}` is completely gone from the top-left corner.
  - Theme toggle (Dark/Light mode) now switches themes instantly via `main.js`.
  - "+ New Task" button opens the interactive modal dialog.
  - User profile and notifications dropdowns open and close smoothly.
  - Kanban board cards and RACI matrix cells are fully interactive.

---

### [Milestone 1: Repository Audit & Planning] - 2026-10-19
- Inspected workspace file tree: confirmed `backend/` (`accounts/`, `meetings/`, `nexflow/`, `task/`, `manage.py`), `database/`, and existing `frontend/` folders.
- Preserved all backend files without modifications.
- Established strict vanilla stack: HTML5, CSS3, Vanilla JavaScript (ES6+), and Django Templates without any external frameworks (no React, Bootstrap, Tailwind, or Node.js).
- Initialized `progress.md` with tracking milestones and `changes.md` with audit logs.

---

### [Milestone 2: Design System Assets & Graphics] - 2026-10-19
Created crisp vector SVG assets in `frontend/images/`:
- `logo.svg`: Full NEXFlow brand logo with flowing hexagonal gradient emblem and typography.
- `logo-icon.svg`: Compact emblem icon for favicon and collapsed sidebar.
- `avatar-1.svg` to `avatar-5.svg`: Stylized avatar portraits for team members:
  - `avatar-1.svg`: Alex Morgan (Team Lead & Architect)
  - `avatar-2.svg`: Sarah Chen (Senior Fullstack Developer)
  - `avatar-3.svg`: Marcus Vance (Product & UI/UX Designer)
  - `avatar-4.svg`: Elena Rostova (QA & Release Engineer)
  - `avatar-5.svg`: David Kim (Backend Database Specialist)
- `empty-state.svg`: Clean vector illustration for zero-state displays.

---

### [Milestone 3: Vanilla CSS Stylesheets] - 2026-10-19
Created modular stylesheets in `frontend/css/`:
- `main.css`: Design tokens, dark/light themes, responsive layout, cards, buttons, modals, dropdowns, toasts.
- `dashboard.css`: Metric cards, RACI distribution bar, workload meters, activity stream.
- `tasks.css`: 4-column Kanban board, draggable cards, list/board switcher.
- `matrix.css`: RACI Responsibility Assignment Matrix grid and directory cards.
- `meetings.css`: Meeting timelines, agenda items, and action items accountability.

---

### [Milestone 4: Vanilla JavaScript Modules] - 2026-10-19
Created clean, modular ES6+ JavaScript files in `frontend/js/`:
- `main.js`: Theme toggler, responsive sidebar, modals, dropdowns, toasts, search shortcut (`Ctrl+K`).
- `tasks.js`: Kanban board drag-and-drop, view switcher, task checkoffs, new task submission.
- `matrix.js`: Interactive RACI cell cycling (`R -> A -> C -> I -> Clear`), live role tallies.
- `meetings.js`: Tabs switcher, action item checkoff tracking, meeting scheduler.

---

### [Milestone 5 & 6: Django Templates Architecture] - 2026-10-19
- `base.html`: Shared master layout for Django templates.
- `dashboard.html`: Django template extending `base.html`.
- `index.html`: Fully featured standalone live preview for Live Server / browser.
- `tasks.html`, `team.html`, `meetings.html`, `reports.html`, `settings.html`, `login.html`, `register.html`: Application pages.
