# Day 6 — Notes
## Week 2, Thursday: React & MUI, Node.js & Vite Setup, JSX & React Component Structure

---

## Executive Summary

Days 1–5 built RoboPulse entirely from the server outward — a data
model, a database, an ORM, a REST API, and RBAC. None of it had a
face. Today the project gains a `frontend\` folder for the first
time, and with it, an entirely new toolchain: Node.js instead of
Python, `npm` instead of `pip`, Vite instead of `fastapi dev`, and JSX
instead of Python syntax altogether. The underlying engineering
instincts carry over directly even though the syntax doesn't —
project-scoped dependency isolation (`node_modules` playing the same
role `.venv` played on Day 1), a dev server with live-reload
(`npm run dev` playing the same role `fastapi dev` played on Day 4),
and composition of small, focused pieces into something larger
(`RobotList` delegating to `RobotCard`, the same instinct behind Day
4's `APIRouter` composition).

Deliberately absent today: any actual connection to the FastAPI
backend. Every component built today receives its data as a **prop**,
sourced from a hardcoded mock array shaped to match real seeded data
and real verified API responses exactly. This wasn't a shortcut to
avoid harder material — it's a genuine architectural boundary, drawn
on purpose, so that Day 7's introduction of Axios and CORS is a matter
of swapping *where* a prop's value comes from, not rewriting any
component that displays it.

A real, valuable incident happened during today's material: installing
MUI from the wrong working directory (the workspace root, instead of
`frontend\`) silently created a second, independent copy of React,
producing a blank page with an "Invalid hook call" error in the
browser console — no error anywhere in the terminal at all. This is
documented in detail below, both because it's a genuinely common
real-world Node/npm mistake, and because the diagnostic path to find
it (browser console → `npm ls` → tracing the reported project root)
is a transferable debugging skill worth teaching explicitly.

---

## Deep Dive: Node.js & Vite Setup

- **`npm` and `package.json`** are the direct JavaScript-ecosystem
  counterparts to `pip` and `requirements.txt` — a manifest of
  dependencies, plus (unlike `requirements.txt`) a place to define
  reusable command shortcuts (`npm run dev`, seen today; more will
  appear in later days) under `package.json`'s `"scripts"` section.
- **`node_modules\`** is where every installed package's actual code
  lives — the direct equivalent of a Python `.venv`'s
  `site-packages\` folder. Like `.venv`, it's never committed to
  version control (a `.gitignore` entry, not shown as a course step
  today but assumed going forward) and can always be regenerated from
  `package.json` via `npm install` alone.
- **How Node resolves `node_modules` (and why the working directory
  matters more than it might seem).** When JavaScript code does
  `import { Card } from '@mui/material'`, Node's module resolution
  algorithm looks for `node_modules\@mui\material` starting in the
  *current* file's directory, and if it's not found there, walks
  **upward** through every parent directory until it finds one (or
  runs out of parent directories to check). This is different from
  Python's `.venv`, which is explicitly *activated* and has no
  equivalent "walk upward" fallback behavior. The practical
  consequence: running an install command from the wrong directory
  doesn't necessarily produce an obvious error — it can silently
  create a *second*, independent `node_modules` one level up, which
  Node will then dutifully find and use via that upward search,
  quietly resolving some packages from one location and others from
  another. Today's real class incident (see the Troubleshooting Guide)
  was exactly this.
- **Vite** is a build tool and dev server. It's what compiles `.jsx`
  (which no browser can execute directly) down to plain JavaScript,
  and what serves the live, auto-reloading page during development.
  Comparable in role to Webpack + Create React App for older React
  projects, but built around dramatically faster dev-server
  reloading. `npm run dev` (today) is the direct sibling of Day 4's
  `fastapi dev app/main.py` — both are development-only servers with
  live-reload, neither is what a real deployment actually runs (a
  later day builds a production bundle, per the problem statement's
  AWS S3 static-hosting target).

---

## Deep Dive: React & MUI

- **MUI is built on Emotion**, a separate CSS-in-JS library — this is
  why `@emotion/react`/`@emotion/styled` had to be installed alongside
  `@mui/material` as **peer dependencies**, the same relationship
  FastAPI has to Starlette/Pydantic underneath it: a framework built
  *on top of* other libraries rather than reinventing their job.
- **`ThemeProvider` and React Context, previewed.** `ThemeProvider`
  makes the custom `theme` object available to every MUI component
  anywhere in the tree, however deeply nested, without it being passed
  down manually as a prop at every level. Under the hood, this is
  React's **Context** API — the exact mechanism Day 7 formally
  introduces for RoboPulse's own authentication state. Today's usage
  is a live, working example students will already have *used* before
  they're taught the underlying concept by name.
- **`CssBaseline`** is MUI's CSS reset — comparable to `normalize.css`
  — applied once, at the top of the component tree, so every browser
  renders MUI's own components from the same consistent starting
  point (no inconsistent default margins, font baselines, etc. across
  Chrome/Firefox/Edge).
- **The `sx` prop** is MUI's shorthand styling API — a plain
  JavaScript object (`sx={{ mr: 2 }}`), not a CSS string, and
  theme-aware by default (numeric spacing values like `mr: 2` resolve
  through the active theme's spacing scale, not raw pixels). This is
  MUI-specific syntax, not a core part of JSX itself — worth
  distinguishing clearly from the JSX fundamentals below.

---

## Deep Dive: JSX

- **JSX is not HTML.** It looks like HTML, but it's syntactic sugar
  that compiles down to plain JavaScript function calls
  (`<AppBar position="static">...</AppBar>` becomes something like
  `React.createElement(AppBar, { position: "static" }, ...)`) — this
  compilation is exactly what Vite is doing on every save, and it's
  *why* a `.jsx` file needs a build step at all rather than running
  directly in a browser the way a `.html` file can.
- **Concrete syntax differences from real HTML**, all stemming from
  JSX being JavaScript first:
  - Every tag must self-close: `<br />`, never bare `<br>`.
  - Attributes are `camelCase` (`onClick`, not `onclick`), matching
    JavaScript's own naming convention rather than HTML's lowercase
    convention.
  - `class` becomes `className` (not used yet today via MUI's `sx`
    prop, but the reason will matter the moment any plain, non-MUI
    HTML element needs styling later in the course) — `class` is a
    reserved word in JavaScript itself, which is why JSX can't reuse
    it directly.
- **Curly braces `{}` drop back into JavaScript.** Anything inside
  `{}` in JSX is evaluated as a JavaScript expression — a variable, a
  template string, a computed boolean — not rendered as literal text.
  This is how `{robot.serialNumber}` and
  `` {`${robot.batteryLevel}% battery`} `` both work: the braces are
  the escape hatch out of "this looks like markup" back into "this is
  a real value."
- **Fragments (`<> ... </>`).** JSX requires exactly one root element
  per component's return value; a Fragment groups multiple elements
  together to satisfy that requirement without adding an actual extra
  wrapper `<div>` to the real, rendered DOM.

---

## Deep Dive: React Component Structure

- **A component is just a function that returns JSX.** `AppHeader`,
  `RobotCard`, `RobotList` are ordinary JavaScript functions —
  capitalized specifically so React (and JSX itself) can distinguish
  a custom component (`<RobotCard />`) from a built-in HTML element
  (`<div />`) purely by looking at the capitalization of the tag name.
- **Props are the *only* sanctioned way data flows into a component**
  (state, introduced later in the course, is the other half of this
  story). `function RobotCard({ robot })` destructures its one prop
  directly in the function signature — `RobotCard` has no idea and no
  need to know where `robot` originally came from, mirroring the same
  separation of concerns Day 4's `schemas/`/`models/` split
  established on the backend: a component describes *how to display*
  data, not *where it comes from*.
- **Composition over monolithic components.** `RobotList` doesn't
  know how to render an individual robot's details at all — it
  delegates entirely to `RobotCard`, once per array entry. This is
  the same instinct as Day 4's `APIRouter`-per-resource pattern:
  small, single-purpose pieces, assembled into something larger,
  rather than one large component (or one large router) trying to do
  everything.
- **The `key` prop, and its direct parallel to a database primary
  key.** React uses `key` to track which rendered element corresponds
  to which array entry across re-renders — without a stable, unique
  key, React can't reliably tell "this is the same robot, just
  updated" from "this is a completely different robot that happens to
  render similarly," and re-renders/reorders can silently corrupt in
  ways that are hard to spot visually until they cause real bugs. This
  is conceptually identical to why Day 2's `robots` table has a
  `PRIMARY KEY` rather than relying on row position — both solve
  "which one is this, specifically," not just "which one looks like
  this right now." Using an array index as `key` is the equivalent
  mistake to identifying a database row by its position in a result
  set instead of its actual primary key: it happens to work until the
  order changes.

---

## Architectural Analysis

Today's most consequential decision — every component receiving its
data exclusively via props, sourced from mock data shaped to exactly
match real backend responses — is a direct, deliberate parallel to Day
4's `schemas/`/`models/` split. In both cases, a boundary was drawn
between "what this piece of code displays/validates" and "where that
data actually comes from," specifically so the *source* of the data
can change later without touching the code that consumes it. Day 4
predicted this would matter once RBAC needed different data
visibility per role; today's version of the same bet is that Day 7 can
replace `mockRobots`/`mockDiscrepancies` with real `axios.get(...)`
calls without a single change inside `RobotCard.jsx`, `RobotList.jsx`,
`DiscrepancyCard.jsx`, or `DiscrepancyList.jsx` — only `App.jsx` (where
the data is sourced and handed down) will need to change.

The choice to make today's mock data mirror real seeded/API data
exactly — not just plausible-looking placeholder values — continues
the running-example discipline established since Day 1. Business
Question #1 has now been answered visually, via conditional chip
coloring, for the fifth time; Business Question #2's discrepancy
report has appeared as a rendered UI card for the first time. Neither
required inventing new business logic — the entire point, again, is
demonstrating that the same underlying answer survives every layer of
tooling this course adds on top of it.

Today's real class incident is worth treating as a first-class
architectural lesson, not just a bug fix: Node's upward-searching
module resolution means a project's working directory isn't just a
convenience concern the way it often is with Python's explicitly
activated `.venv` — an npm command run one directory too high can
silently succeed while creating a structurally broken dependency tree,
with no error until a specific runtime symptom (here, `ThemeProvider`
crashing on `useMemo`) surfaces well after the mistake was made. The
diagnostic path — browser console first (since a duplicate-React
crash is a runtime error, invisible to Vite's own terminal output),
then `npm ls` to confirm exactly which project root a command is
actually operating against — is a genuinely transferable Node.js
debugging skill, not a RoboPulse-specific workaround.

---

## Common Pitfalls & Anti-Patterns

- **Running an `npm install`/`npm create` command from the wrong
  directory.** Today's real incident: running MUI's install command
  from `robo-pulse\` instead of `robo-pulse\frontend\` created a
  second, independent `node_modules` (and a second `package.json`) at
  the workspace root, giving the project two separate copies of React
  resolved from two different locations. No error appeared until the
  browser actually tried to render `ThemeProvider`.
- **Treating JSX as HTML.** Forgetting to self-close a tag, using
  `class` instead of `className`, or using lowercase event attribute
  names (`onclick` instead of `onClick`) all stem from this — JSX
  looks like markup but is JavaScript underneath, and JavaScript's own
  syntax rules apply.
- **Using an array index as `key`.** Works perfectly with a
  single-element or never-reordered array (exactly the situation
  today's mock data sets up) and silently breaks the moment the
  underlying array's order or contents change — the same fragility
  described in the `key`/primary-key parallel above.
- **Forgetting `export default`** on a new component file — produces
  an import error the moment another file tries to bring it in
  (`import RobotCard from './RobotCard.jsx'` failing because nothing
  was exported).
- **Hardcoding values inside a component instead of reading them from
  props.** Easy to do by accident when only one real data example
  exists to build against (as in today's single-discrepancy mock
  data) — the component appears correct until a second, different
  data object is passed in and the hardcoded value doesn't change to
  match.
- **Forgetting `ThemeProvider`/`CssBaseline` wrap `App`** in
  `main.jsx` — MUI components still render, but without the custom
  theme's colors or the consistent baseline styling, producing a
  visually "off" but not broken page — a subtler symptom than a crash,
  worth knowing to check for even when nothing is technically an
  error.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| Blank page, **no errors in the Vite terminal at all** | The real problem is a runtime error, which only ever surfaces in the **browser's own console** (F12 → Console), not the terminal — this is the first thing to check any time the terminal looks clean but the page is blank | Open the browser console and read the actual error there before investigating further |
| Browser console shows `Invalid hook call` and/or `Cannot read properties of null (reading 'useMemo')`, often pointing into `ThemeProvider` | Two separate copies of React exist in the project, almost always because a package install command was run from the wrong directory (e.g. the workspace root instead of `frontend\`), creating a second, independent `node_modules` | Run `npm ls react react-dom` and check the reported project path at the very top of the output — if it's not `...\frontend`, that confirms the wrong-directory install; remove the misplaced `node_modules`/`package.json` from the incorrect location, confirm `Get-Location` ends in `...\frontend` before reinstalling, then reinstall from there |
| `npm ls` reports a project path that doesn't match where you expected | The command was run from (or is reporting on) the wrong directory in the tree, which is itself diagnostic information | Use the reported path directly to locate the misplaced `node_modules`/`package.json`, rather than assuming the install happened where intended |
| Browser shows a red "Failed to resolve import" overlay | A file referenced in an `import` statement doesn't exist at that exact path, was misnamed, or wasn't saved | Run `Get-ChildItem -Recurse src` from `frontend\` and compare against the directory tree in the demo doc; check for typos in import paths |
| Page renders, but with no MUI styling at all (plain, unstyled HTML-looking output) | `ThemeProvider`/`CssBaseline` aren't wrapping `App` in `main.jsx`, or `@emotion/react`/`@emotion/styled` weren't actually installed | Confirm `main.jsx` matches Step 5 exactly; re-run the Step 4 install command from inside `frontend\` |
| `Uncaught ReferenceError: <Something> is not defined` | A component or value is used without being imported | Add the missing `import` line at the top of the file |
| `Objects are not valid as a React child` | JSX tried to render a whole object directly (e.g. `{robot}` instead of `{robot.serialNumber}`) rather than one of its properties | Access the specific field needed, rather than the whole object, inside the `{}` expression |
| `npm : The term 'npm' is not recognized...` | Node.js wasn't actually installed, or VS Code wasn't fully closed and reopened after the installer ran (the same `PATH`-propagation issue from Day 2's PostgreSQL install) | Confirm with `node --version` in a **freshly opened** VS Code window (full close/reopen, not just a new tab) |
| `Error: listen EADDRINUSE: address already in use :::5173` | Another `npm run dev` process (from an earlier terminal tab) is still running and holding Vite's default port | Close the earlier terminal tab/process, or note the alternate port Vite offers automatically when the default is taken |
| Editing a file no longer triggers a live-reload in the browser | The dev server process was stopped (or crashed) without noticing, and the browser is showing a stale, disconnected page | Check the terminal for the dev server's status; restart with `npm run dev` if it's no longer running |

---
*RoboPulse Fleet Command Center — Day 6 of 13*
